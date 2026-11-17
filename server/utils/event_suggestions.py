"""Materialize event prefills for unreviewed line items."""

import logging

from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

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
            line_items_query = (
                db.query(LineItem)
                .options(joinedload(LineItem.payment_method), joinedload(LineItem.transaction))
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
            if not rules.categorized_hints:
                # Name-only hints can't supply a category, so only a Stripe expense can produce a suggestion.
                line_items_query = line_items_query.join(Transaction, LineItem.transaction_id == Transaction.id).filter(
                    Transaction.source == "stripe_api", LineItem.amount > 0
                )

            for line_item in line_items_query.all():
                prefill = suggest_prefill(rules, [line_item])
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
    """Insert one suggestion; return False if another refresh already suggested this user/line item.

    Two refreshes can run at once and both try to suggest the same line item. The second insert
    violates the unique (user_id, line_item_id) constraint, and in PostgreSQL that error would abort
    the whole refresh transaction. A savepoint rolls back only this insert, so the rest of the batch
    is kept. Any other integrity error is a real bug and is re-raised.
    """
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
