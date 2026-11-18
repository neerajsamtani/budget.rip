"""Read-only event prefill shared by the modal's evaluate endpoint and refresh-time suggestions.

Precedence: the first matching hint that sets a category wins outright. Otherwise a confident,
unanimous Stripe category is used, titled by the first matching name-only hint if any. Otherwise
a matching name-only hint still supplies a title without a category.
"""

from dataclasses import dataclass

from sqlalchemy import exists
from sqlalchemy.orm import joinedload

from helpers import default_name_cleanup
from models.sql_models import Category, EventHint, EventLineItem, EventSuggestion, LineItem
from utils.cel_evaluator import evaluate_hints
from utils.stripe_category_mapping import ACCEPTED_CONFIDENCE_LEVELS, map_stripe_category


@dataclass
class PrefillRules:
    """One user's hints and categories as plain data, so many items can be resolved without more queries."""

    categorized_hints: list[dict]
    name_only_hints: list[dict]
    categories_by_name: dict[str, Category]


def load_prefill_rules(db, user_id: str) -> PrefillRules:
    hints = (
        db.query(EventHint)
        .options(joinedload(EventHint.prefill_category))
        .filter(EventHint.user_id == user_id, EventHint.is_active.is_(True))
        .order_by(EventHint.display_order)
        .all()
    )
    rules = PrefillRules(
        categorized_hints=[],
        name_only_hints=[],
        categories_by_name={c.name: c for c in db.query(Category).filter(Category.user_id == user_id).all()},
    )
    for hint in hints:
        category = hint.prefill_category if hint.prefill_category and hint.prefill_category.user_id == user_id else None
        hint_dict = {
            "id": hint.id,
            "name": hint.name,
            "cel_expression": hint.cel_expression,
            "prefill_name": hint.prefill_name,
            "prefill_category": category.name if category else None,
            "prefill_category_id": category.id if category else None,
        }
        (rules.categorized_hints if category else rules.name_only_hints).append(hint_dict)
    return rules


def resolve_event_prefill(db, user_id: str, line_item_ids: list[str]) -> dict | None:
    requested_ids = list(dict.fromkeys(line_item_ids))
    if not requested_ids:
        return None
    # Flag reviewed and dismissed items in the same query; each extra round trip delays the modal.
    is_reviewed = exists().where(EventLineItem.line_item_id == LineItem.id)
    was_dismissed = exists().where(
        EventSuggestion.line_item_id == LineItem.id,
        EventSuggestion.user_id == user_id,
        EventSuggestion.rejected_at.is_not(None),
    )
    rows = (
        db.query(LineItem, is_reviewed.label("is_reviewed"), was_dismissed.label("was_dismissed"))
        .options(joinedload(LineItem.transaction), joinedload(LineItem.payment_method))
        .filter(LineItem.id.in_(requested_ids))
        .all()
    )
    items_by_id = {row.LineItem.id: row.LineItem for row in rows}
    if len(items_by_id) != len(requested_ids):
        return None
    # The user rejected a suggestion for one of these items, so don't offer it again in the modal.
    if any(row.was_dismissed for row in rows):
        return None
    # Selection order decides the default title, matching the client's first-item fallback.
    items = [items_by_id[item_id] for item_id in requested_ids]
    # Reviewed items already have a category through their event, so Stripe shouldn't suggest another.
    return suggest_prefill(load_prefill_rules(db, user_id), items, allow_stripe=not any(row.is_reviewed for row in rows))


def suggest_prefill(rules: PrefillRules, items: list[LineItem], allow_stripe: bool = True) -> dict | None:
    """Resolve from preloaded rules; issues no queries when each item's transaction and payment method are loaded."""
    hint_inputs = [
        {
            "description": item.description or "",
            "amount": float(item.amount),
            "responsible_party": item.responsible_party or "",
            "payment_method": item.payment_method.name if item.payment_method else "",
        }
        for item in items
    ]
    categorized = evaluate_hints(rules.categorized_hints, hint_inputs) if rules.categorized_hints else None
    if categorized:
        return {**categorized, "source": "event_hint", "source_metadata": {}}

    name_hint = evaluate_hints(rules.name_only_hints, hint_inputs) if rules.name_only_hints else None
    stripe_suggestion = _unanimous_stripe_category(rules, items) if allow_stripe else None
    if not stripe_suggestion:
        return {**name_hint, "source": "event_hint", "source_metadata": {}} if name_hint else None

    category, metadata = stripe_suggestion
    if name_hint:
        metadata["name_hint_id"] = name_hint["matched_hint_id"]
        metadata["name_hint_name"] = name_hint["matched_hint_name"]
        name = name_hint["name"]
    else:
        # A merchant name is already clean; a raw bank description gets the modal's default cleanup.
        name = ((items[0].responsible_party or "").strip() or default_name_cleanup(items[0].description))[:255]
    return {
        "name": name,
        "category": category.name,
        "category_id": category.id,
        "source": "stripe_personal_finance",
        "source_metadata": metadata,
        "matched_hint_id": name_hint["matched_hint_id"] if name_hint else None,
        "matched_hint_name": name_hint["matched_hint_name"] if name_hint else None,
    }


def _unanimous_stripe_category(rules: PrefillRules, items: list[LineItem]) -> tuple[Category, dict] | None:
    """Every item must independently map to the same category; one abstention or conflict vetoes the group."""
    if any(item.amount <= 0 or item.transaction.source != "stripe_api" for item in items):
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
