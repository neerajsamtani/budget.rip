"""Read-only event prefill shared by the modal's evaluate endpoint and refresh-time suggestions."""

from dataclasses import dataclass

from sqlalchemy.orm import joinedload, selectinload

from models.sql_models import Category, EventHint, EventSuggestion, LineItem
from utils.cel_evaluator import evaluate_hints
from utils.stripe_category_mapping import ACCEPTED_CONFIDENCE_LEVELS, map_stripe_category


@dataclass
class PrefillRules:
    """One user's hints and categories as plain data, so many items can be resolved without more queries."""

    hint_dicts: list[dict]
    categories_by_name: dict[str, Category]


def load_prefill_rules(db, user_id: str) -> PrefillRules:
    hints = (
        db.query(EventHint)
        .options(joinedload(EventHint.prefill_category))
        .filter(EventHint.user_id == user_id, EventHint.is_active.is_(True))
        .order_by(EventHint.display_order)
        .all()
    )
    return PrefillRules(
        hint_dicts=[
            {
                "id": hint.id,
                "name": hint.name,
                "cel_expression": hint.cel_expression,
                "prefill_name": hint.prefill_name,
                **(
                    {"prefill_category": hint.prefill_category.name, "prefill_category_id": hint.prefill_category_id}
                    if hint.prefill_category and hint.prefill_category.user_id == user_id
                    else {"prefill_category": None, "prefill_category_id": None}
                ),
            }
            for hint in hints
        ],
        categories_by_name={c.name: c for c in db.query(Category).filter(Category.user_id == user_id).all()},
    )


def resolve_event_prefill(db, user_id: str, line_item_ids: list[str]) -> dict | None:
    requested_ids = list(dict.fromkeys(line_item_ids))
    if not requested_ids:
        return None
    loaded_items = (
        db.query(LineItem)
        .options(joinedload(LineItem.transaction), joinedload(LineItem.payment_method), selectinload(LineItem.events))
        .filter(LineItem.id.in_(requested_ids))
        .all()
    )
    items_by_id = {item.id: item for item in loaded_items}
    if len(items_by_id) != len(requested_ids):
        return None
    # A dismissed suggestion means the user rejected that item's prefill, so it can't vouch for the group.
    stripe_vetoed = (
        db.query(EventSuggestion.id)
        .filter(
            EventSuggestion.user_id == user_id,
            EventSuggestion.line_item_id.in_(requested_ids),
            EventSuggestion.rejected_at.is_not(None),
        )
        .first()
        is not None
    )
    # Selection order decides the default title, matching the client's first-item fallback.
    items = [items_by_id[item_id] for item_id in requested_ids]
    return suggest_prefill(load_prefill_rules(db, user_id), items, stripe_vetoed=stripe_vetoed)


def suggest_prefill(rules: PrefillRules, items: list[LineItem], stripe_vetoed: bool = False) -> dict | None:
    """Resolve from preloaded rules and items; issues no queries when transaction, payment method and events are loaded."""
    hint_suggestion = (
        evaluate_hints(
            rules.hint_dicts,
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
        if rules.hint_dicts
        else None
    )
    if hint_suggestion:
        matched_hint = next(hint for hint in rules.hint_dicts if hint["id"] == hint_suggestion["matched_hint_id"])
        hint_suggestion.update(
            category_id=matched_hint["prefill_category_id"],
            source="event_hint",
            source_metadata={},
        )
    if hint_suggestion and hint_suggestion["category"]:
        return hint_suggestion

    stripe_suggestion = None if stripe_vetoed else _unanimous_stripe_category(rules, items)
    if not stripe_suggestion:
        return hint_suggestion
    category, metadata = stripe_suggestion
    if hint_suggestion:
        metadata["name_hint_id"] = hint_suggestion["matched_hint_id"]
        metadata["name_hint_name"] = hint_suggestion["matched_hint_name"]
        name = hint_suggestion["name"]
    else:
        name = ((items[0].responsible_party or "").strip() or items[0].description.strip())[:255]
    return {
        "name": name,
        "category": category.name,
        "category_id": category.id,
        "source": "stripe_personal_finance",
        "source_metadata": metadata,
        "matched_hint_id": hint_suggestion["matched_hint_id"] if hint_suggestion else None,
        "matched_hint_name": hint_suggestion["matched_hint_name"] if hint_suggestion else None,
    }


def _unanimous_stripe_category(rules: PrefillRules, items: list[LineItem]) -> tuple[Category, dict] | None:
    """Every item must independently map to the same category; one abstention or conflict vetoes the group."""
    if any(item.amount <= 0 or item.transaction.source != "stripe_api" or item.events for item in items):
        return None
    candidates = [map_stripe_category(item.transaction.source_data) for item in items]
    if not all(candidates) or len({c["category"] for c in candidates}) != 1:
        return None
    category = rules.categories_by_name.get(candidates[0]["category"])
    if not category:
        return None
    evidence = [c["source_metadata"] for c in candidates]
    if len(items) == 1:
        return category, evidence[0]
    pairs = sorted({(e["primary_label"], e["detailed_label"]) for e in evidence}, key=lambda pair: (pair[0], pair[1] or ""))
    return category, {
        "mapping_version": evidence[0]["mapping_version"],
        "selected_count": len(items),
        "labels": [{"primary_label": primary, "detailed_label": detailed} for primary, detailed in pairs],
        # The group is only as trustworthy as its least confident member.
        "confidence_level": min((e["confidence_level"] for e in evidence), key=ACCEPTED_CONFIDENCE_LEVELS.index),
    }
