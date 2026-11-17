import json
from pathlib import Path

import pytest

from utils.stripe_category_mapping import map_stripe_category

INVENTORY = json.loads((Path(__file__).parent / "fixtures/stripe_personal_finance_mapping.json").read_text())


def source(primary="food_and_drink", detailed="groceries", confidence="high"):
    return {
        "classifications": [
            {
                "type": "personal_finance",
                "personal_finance": {
                    "primary_label": primary,
                    "detailed_label": detailed,
                    "confidence_level": confidence,
                },
            }
        ]
    }


@pytest.mark.parametrize("rule", INVENTORY["rules"])
def test_every_published_pair_has_its_exact_mapping_or_abstention(rule):
    result = map_stripe_category(source(rule["primary_label"], rule["detailed_label"]))
    if rule["category_name"] is None:
        assert result is None
    else:
        assert result == {
            "category": rule["category_name"],
            "source_metadata": {
                "mapping_version": 1,
                "primary_label": rule["primary_label"],
                "detailed_label": rule["detailed_label"],
                "confidence_level": "high",
            },
        }


@pytest.mark.parametrize("primary", sorted({r["primary_label"] for r in INVENTORY["rules"]}))
def test_only_five_primaries_support_missing_detail(primary):
    result = map_stripe_category(source(primary, None))
    assert (result["category"] if result else None) == INVENTORY["primary_only_fallbacks"].get(primary)


@pytest.mark.parametrize("confidence", [None, "", "low", "medium", {}, [], "HIGH"])
def test_merchant_confidence_cannot_substitute_for_classification_confidence(confidence):
    data = source(confidence=confidence)
    data["merchant"] = {"name": "Store", "confidence_level": "very_high"}
    assert map_stripe_category(data) is None


@pytest.mark.parametrize("merchant_confidence", [None, "low", "high", "very_high"])
@pytest.mark.parametrize("confidence", ["high", "very_high"])
def test_category_confidence_is_independent_of_merchant_confidence(merchant_confidence, confidence):
    data = source(confidence=confidence)
    data["merchant"] = {"confidence_level": merchant_confidence}
    assert map_stripe_category(data)["category"] == "Groceries"


@pytest.mark.parametrize(
    "data",
    [
        None,
        [],
        {},
        {"classifications": {}},
        {"classifications": [None]},
        {"classifications": [{"type": "money_movement", "personal_finance": {}}]},
        {"classifications": [{"type": "personal_finance", "personal_finance": []}]},
        source("unknown", "groceries"),
        source("medical", "groceries"),
        source(detailed="unknown"),
        source(detailed=""),
        source(detailed=[]),
        source(primary=[]),
        {"classifications": source()["classifications"] * 2},
        {"classifications": source()["classifications"] + source("medical", "dental_care")["classifications"]},
    ],
)
def test_unknown_mismatched_conflicting_or_malformed_data_abstains(data):
    assert map_stripe_category(data) is None


def test_sanitized_api_evidence_has_the_verified_nested_fields():
    evidence = json.loads((Path(__file__).parent / "fixtures/stripe_personal_finance_evidence.json").read_text())
    assert evidence == {
        "type": "personal_finance",
        "personal_finance": {
            "confidence_level": "low",
            "detailed_label": "other_income",
            "primary_label": "income",
        },
    }
    assert map_stripe_category({"classifications": [evidence]}) is None


def test_initial_inventory_has_128_pairs_and_all_seven_rent_utilities_map_to_rent():
    rules = INVENTORY["rules"]
    assert len(rules) == 128
    assert sum(r["category_name"] is not None for r in rules) == 50
    utilities = [r for r in rules if r["primary_label"] == "rent_and_utilities"]
    assert len(utilities) == 7
    assert {map_stripe_category(source(r["primary_label"], r["detailed_label"]))["category"] for r in utilities} == {"Rent"}
