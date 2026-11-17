"""Read-only event prefill shared by the modal's evaluate endpoint."""

from sqlalchemy.orm import joinedload

from models.sql_models import Category, EventHint, EventSuggestion, LineItem
from utils.cel_evaluator import evaluate_hints
from utils.stripe_category_mapping import map_stripe_category


def resolve_event_prefill(db, user_id: str, line_item_ids: list[str]) -> dict | None:
    requested_ids = set(line_item_ids)
    if not requested_ids:
        return None
    items = (
        db.query(LineItem)
        .options(joinedload(LineItem.transaction), joinedload(LineItem.payment_method))
        .filter(LineItem.id.in_(requested_ids))
        .all()
    )
    if {item.id for item in items} != requested_ids:
        return None
    hints = (
        db.query(EventHint)
        .options(joinedload(EventHint.prefill_category))
        .filter(EventHint.user_id == user_id, EventHint.is_active.is_(True))
        .order_by(EventHint.display_order)
        .all()
    )
    hint_dicts = [
        {
            "id": hint.id,
            "name": hint.name,
            "cel_expression": hint.cel_expression,
            "prefill_name": hint.prefill_name,
            "prefill_category": hint.prefill_category.name
            if hint.prefill_category and hint.prefill_category.user_id == user_id
            else None,
        }
        for hint in hints
    ]
    hint_suggestion = evaluate_hints(
        hint_dicts,
        [
            {
                "description": item.description or "",
                "amount": float(item.amount),
                "responsible_party": item.responsible_party or "",
                "payment_method": item.payment_method.name if item.payment_method else "",
            }
            for item in items
        ],
    )
    if hint_suggestion:
        matched_hint = next(hint for hint in hints if hint.id == hint_suggestion["matched_hint_id"])
        hint_suggestion.update(
            category_id=matched_hint.prefill_category_id if hint_suggestion["category"] else None,
            source="event_hint",
            source_metadata={},
        )
    if len(requested_ids) > 1 or (hint_suggestion and hint_suggestion["category"]):
        return hint_suggestion

    item = items[0]
    if item.amount <= 0 or item.transaction.source != "stripe_api" or item.events:
        return hint_suggestion
    rejected = (
        db.query(EventSuggestion.id)
        .filter(
            EventSuggestion.user_id == user_id,
            EventSuggestion.line_item_id == item.id,
            EventSuggestion.rejected_at.is_not(None),
        )
        .first()
    )
    if rejected:
        return hint_suggestion
    stripe_candidate = map_stripe_category(item.transaction.source_data)
    if not stripe_candidate:
        return hint_suggestion
    category = db.query(Category).filter(Category.user_id == user_id, Category.name == stripe_candidate["category"]).first()
    if not category:
        return hint_suggestion
    metadata = stripe_candidate["source_metadata"]
    if hint_suggestion:
        metadata["name_hint_id"] = hint_suggestion["matched_hint_id"]
        metadata["name_hint_name"] = hint_suggestion["matched_hint_name"]
    default_name = (item.responsible_party or "").strip() or item.description.strip()
    name = hint_suggestion["name"] if hint_suggestion else default_name[:255]
    return {
        "name": name,
        "category": category.name,
        "category_id": category.id,
        "source": "stripe_personal_finance",
        "source_metadata": metadata,
        "matched_hint_id": hint_suggestion["matched_hint_id"] if hint_suggestion else None,
        "matched_hint_name": hint_suggestion["matched_hint_name"] if hint_suggestion else None,
    }
