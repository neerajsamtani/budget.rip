"""Conservative expense mapping for Stripe personal-finance classifications.

Field shape verified by a read-only preview API response on 2026-11-16;
see tests/fixtures/stripe_personal_finance_evidence.json.
"""

MAPPING_VERSION = 1

# Only mapped pairs are listed; all other pairs abstain.
CATEGORY_BY_PAIR = {
    ("entertainment", "casinos_and_gambling"): "Entertainment",
    ("entertainment", "live_events_and_attractions"): "Entertainment",
    ("entertainment", "music_and_audio"): "Entertainment",
    ("entertainment", "tv_and_movies"): "Entertainment",
    ("entertainment", "video_games"): "Entertainment",
    ("entertainment", "other_entertainment"): "Entertainment",
    ("food_and_drink", "beer_wine_and_liquor"): "Alcohol",
    ("food_and_drink", "coffee"): "Dining",
    ("food_and_drink", "fast_food"): "Dining",
    ("food_and_drink", "groceries"): "Groceries",
    ("food_and_drink", "restaurants"): "Dining",
    ("food_and_drink", "vending_machines"): "Dining",
    ("food_and_drink", "other_food_and_drink"): "Dining",
    ("general_merchandise", "books_and_periodicals"): "Shopping",
    ("general_merchandise", "clothing_and_accessories"): "Shopping",
    ("general_merchandise", "convenience_stores"): "Shopping",
    ("general_merchandise", "department_stores"): "Shopping",
    ("general_merchandise", "discount_stores"): "Shopping",
    ("general_merchandise", "electronics"): "Shopping",
    ("general_merchandise", "gifts_and_novelties"): "Shopping",
    ("general_merchandise", "office_supplies"): "Shopping",
    ("general_merchandise", "online_marketplaces"): "Shopping",
    ("general_merchandise", "pet_supplies"): "Shopping",
    ("general_merchandise", "sporting_goods"): "Shopping",
    ("general_merchandise", "superstores"): "Shopping",
    ("general_merchandise", "tobacco_and_vape"): "Shopping",
    ("general_merchandise", "other_general_merchandise"): "Shopping",
    ("home_improvement", "furniture"): "Shopping",
    ("home_improvement", "hardware"): "Shopping",
    ("medical", "dental_care"): "Medical",
    ("medical", "eye_care"): "Medical",
    ("medical", "nursing_care"): "Medical",
    ("medical", "pharmacies_and_supplements"): "Medical",
    ("medical", "primary_care"): "Medical",
    ("medical", "veterinary_services"): "Medical",
    ("medical", "other_medical"): "Medical",
    ("rent_and_utilities", "gas_and_electricity"): "Rent",
    ("rent_and_utilities", "internet_and_cable"): "Rent",
    ("rent_and_utilities", "rent"): "Rent",
    ("rent_and_utilities", "sewer_and_waste_services"): "Rent",
    ("rent_and_utilities", "telephone"): "Rent",
    ("rent_and_utilities", "water_utility"): "Rent",
    ("rent_and_utilities", "other_rent_and_utilities"): "Rent",
    ("transportation", "bike_and_scooter_rentals"): "Transit",
    ("transportation", "public_transportation"): "Transit",
    ("transportation", "taxis_and_rideshares"): "Transit",
    ("travel", "flights"): "Travel",
    ("travel", "lodging"): "Travel",
    ("travel", "rental_cars"): "Travel",
    ("travel", "other_travel"): "Travel",
}

PRIMARY_FALLBACKS = {
    "entertainment": "Entertainment",
    "general_merchandise": "Shopping",
    "medical": "Medical",
    "travel": "Travel",
    "rent_and_utilities": "Rent",
}


def map_stripe_category(source_data: object) -> dict | None:
    """Return category evidence only for one valid, confident classification."""
    if not isinstance(source_data, dict):
        return None
    classifications = source_data.get("classifications")
    if not isinstance(classifications, list) or any(not isinstance(c, dict) for c in classifications):
        return None
    matches = [c for c in classifications if c.get("type") == "personal_finance"]
    if len(matches) != 1:
        return None
    labels = matches[0].get("personal_finance")
    if not isinstance(labels, dict):
        return None
    confidence = labels.get("confidence_level")
    primary = labels.get("primary_label")
    detailed = labels.get("detailed_label")
    if confidence not in ("high", "very_high") or not isinstance(primary, str):
        return None
    if detailed is None:
        category = PRIMARY_FALLBACKS.get(primary)
    elif isinstance(detailed, str):
        category = CATEGORY_BY_PAIR.get((primary, detailed))
    else:
        return None
    if category is None:
        return None
    return {
        "category": category,
        "source_metadata": {
            "mapping_version": MAPPING_VERSION,
            "primary_label": primary,
            "detailed_label": detailed,
            "confidence_level": confidence,
        },
    }
