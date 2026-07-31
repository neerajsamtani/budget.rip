"""Materialize event-hint matches for unreviewed line items."""

import logging

from sqlalchemy import and_
from sqlalchemy.orm import joinedload

from models.database import SessionLocal
from models.sql_models import Category, EventHint, EventLineItem, EventSuggestion, LineItem, User
from utils.cel_evaluator import evaluate_hints
from utils.id_generator import generate_id

logger = logging.getLogger(__name__)


def generate_event_suggestions(user_id: str | None = None) -> int:
    """Create missing single-line-item suggestions. Existing and rejected records are preserved."""
    created_count = 0

    with SessionLocal.begin() as db:
        user_ids = [user_id] if user_id else [row.id for row in db.query(User.id).all()]

        for current_user_id in user_ids:
            hints = (
                db.query(EventHint)
                .options(joinedload(EventHint.prefill_category))
                .join(Category, EventHint.prefill_category_id == Category.id)
                .filter(
                    EventHint.user_id == current_user_id,
                    Category.user_id == current_user_id,
                    EventHint.is_active == True,  # noqa: E712
                    EventHint.prefill_category_id.is_not(None),
                )
                .order_by(EventHint.display_order)
                .all()
            )
            if not hints:
                continue

            line_items = (
                db.query(LineItem)
                .options(joinedload(LineItem.payment_method))
                .outerjoin(EventLineItem, EventLineItem.line_item_id == LineItem.id)
                .outerjoin(
                    EventSuggestion,
                    and_(
                        EventSuggestion.line_item_id == LineItem.id,
                        EventSuggestion.user_id == current_user_id,
                    ),
                )
                .filter(EventLineItem.id.is_(None), EventSuggestion.id.is_(None))
                .all()
            )

            hint_dicts = [
                {
                    "id": hint.id,
                    "name": hint.name,
                    "cel_expression": hint.cel_expression,
                    "prefill_name": hint.prefill_name,
                    "prefill_category": hint.prefill_category.name,
                    "is_active": hint.is_active,
                }
                for hint in hints
            ]
            hints_by_id = {hint.id: hint for hint in hints}

            for line_item in line_items:
                suggestion = evaluate_hints(
                    hint_dicts,
                    [
                        {
                            "description": line_item.description or "",
                            "amount": float(line_item.amount or 0),
                            "payment_method": line_item.payment_method.name if line_item.payment_method else "",
                            "responsible_party": line_item.responsible_party or "",
                        }
                    ],
                )
                if not suggestion:
                    continue

                matched_hint = hints_by_id[suggestion["matched_hint_id"]]
                db.add(
                    EventSuggestion(
                        id=generate_id("es"),
                        user_id=current_user_id,
                        line_item_id=line_item.id,
                        event_hint_id=matched_hint.id,
                        suggested_name=matched_hint.prefill_name,
                        category_id=matched_hint.prefill_category_id,
                    )
                )
                created_count += 1

    logger.info("Created %s event suggestions", created_count)
    return created_count
