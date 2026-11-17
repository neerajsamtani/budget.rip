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
    suggestion = evaluate_hints(
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
    if suggestion:
        winner = next(h for h in hints if h.id == suggestion["matched_hint_id"])
        suggestion.update(
            category_id=winner.prefill_category_id if suggestion["category"] else None,
            source="event_hint",
            source_metadata={},
        )
    if len(requested_ids) > 1 or (suggestion and suggestion["category"]):
        return suggestion

    item = items[0]
    if item.amount <= 0 or item.transaction.source != "stripe_api" or item.events:
        return suggestion
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
        return suggestion
    candidate = map_stripe_category(item.transaction.source_data)
    if not candidate:
        return suggestion
    category = db.query(Category).filter(Category.user_id == user_id, Category.name == candidate["category"]).first()
    if not category:
        return suggestion
    metadata = candidate["source_metadata"]
    if suggestion:
        metadata["name_hint_id"] = suggestion["matched_hint_id"]
        metadata["name_hint_name"] = suggestion["matched_hint_name"]
    return {
        "name": suggestion["name"]
        if suggestion
        else (item.responsible_party or "").strip()[:255] or item.description.strip()[:255],
        "category": category.name,
        "category_id": category.id,
        "source": "stripe_personal_finance",
        "source_metadata": metadata,
        "matched_hint_id": suggestion["matched_hint_id"] if suggestion else None,
        "matched_hint_name": suggestion["matched_hint_name"] if suggestion else None,
    }
