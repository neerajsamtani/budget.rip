"""Materialize event prefills for unreviewed line items."""

import logging
from dataclasses import replace

from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, selectinload

from models.database import SessionLocal
from models.sql_models import EventLineItem, EventSuggestion, LineItem, Transaction, User
from utils.category_suggestions import load_prefill_rules, suggest_prefill
from utils.id_generator import generate_id

logger = logging.getLogger(__name__)


def generate_event_suggestions(user_id: str | None = None) -> int:
    """Create missing single-line-item suggestions. Existing and rejected records are preserved."""
    created_count = 0

    with SessionLocal.begin() as db:
        user_ids = [user_id] if user_id else [row.id for row in db.query(User.id).all()]

        for current_user_id in user_ids:
            rules = load_prefill_rules(db, current_user_id)
            if not rules.categories_by_name:
                continue
            # Refresh suggestions need a category, so a name-only hint must not shadow a later categorized one.
            categorized_rules = replace(rules, hint_dicts=[h for h in rules.hint_dicts if h["prefill_category_id"]])
            line_items_query = (
                db.query(LineItem)
                .options(joinedload(LineItem.payment_method), joinedload(LineItem.transaction), selectinload(LineItem.events))
                .outerjoin(EventLineItem, EventLineItem.line_item_id == LineItem.id)
                .outerjoin(
                    EventSuggestion,
                    and_(
                        EventSuggestion.line_item_id == LineItem.id,
                        EventSuggestion.user_id == current_user_id,
                    ),
                )
                .filter(EventLineItem.id.is_(None), EventSuggestion.id.is_(None))
            )
            if not rules.hint_dicts:
                # Without hints only a Stripe expense can produce a suggestion.
                line_items_query = line_items_query.join(Transaction, LineItem.transaction_id == Transaction.id).filter(
                    Transaction.source == "stripe_api", LineItem.amount > 0
                )

            for line_item in line_items_query.all():
                prefill = suggest_prefill(rules, [line_item])
                if (not prefill or not prefill["category_id"]) and len(categorized_rules.hint_dicts) < len(rules.hint_dicts):
                    prefill = suggest_prefill(categorized_rules, [line_item])
                if not prefill or not prefill["category_id"]:
                    continue

                suggestion = EventSuggestion(
                    id=generate_id("es"),
                    user_id=current_user_id,
                    line_item_id=line_item.id,
                    event_hint_id=prefill["matched_hint_id"],
                    suggested_name=prefill["name"],
                    category_id=prefill["category_id"],
                    source=prefill["source"],
                    source_metadata=prefill["source_metadata"],
                )
                if insert_unless_already_suggested(db, suggestion):
                    created_count += 1

    logger.info("Created %s event suggestions", created_count)
    return created_count


def insert_unless_already_suggested(db, suggestion: EventSuggestion) -> bool:
    """Insert in a savepoint so a concurrent refresh that suggested the same user/item first doesn't abort the batch."""
    try:
        with db.begin_nested():
            db.add(suggestion)
    except IntegrityError:
        already_suggested = (
            db.query(EventSuggestion.id)
            .filter(EventSuggestion.user_id == suggestion.user_id, EventSuggestion.line_item_id == suggestion.line_item_id)
            .first()
        )
        if not already_suggested:
            raise
        return False
    return True
