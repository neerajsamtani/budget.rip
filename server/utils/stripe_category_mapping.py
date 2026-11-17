"""Conservative expense mapping for Stripe personal-finance classifications.

Field shape verified by a read-only preview API response on 2026-11-16;
see tests/fixtures/stripe_personal_finance_evidence.json.
"""

MAPPING_VERSION = 1

# Exact published pairs, including intentional abstentions.
CATEGORY_BY_PAIR = {
    ("bank_fees", "atm_fees"): None,
    ("bank_fees", "cash_advance_fees"): None,
    ("bank_fees", "foreign_transaction_fees"): None,
    ("bank_fees", "insufficient_funds_fees"): None,
    ("bank_fees", "interest_charge"): None,
    ("bank_fees", "late_fees"): None,
    ("bank_fees", "overdraft_fees"): None,
    ("bank_fees", "other_bank_fees"): None,
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
    ("general_services", "accounting_and_financial_planning"): None,
    ("general_services", "automotive_services"): None,
    ("general_services", "childcare"): None,
    ("general_services", "consulting_and_legal"): None,
    ("general_services", "education"): None,
    ("general_services", "insurance"): None,
    ("general_services", "postage_and_shipping"): None,
    ("general_services", "storage"): None,
    ("general_services", "other_general_services"): None,
    ("government_and_non_profit", "donations"): None,
    ("government_and_non_profit", "government_departments_and_agencies"): None,
    ("government_and_non_profit", "tax_payment"): None,
    ("government_and_non_profit", "other_government_and_non_profit"): None,
    ("home_improvement", "furniture"): "Shopping",
    ("home_improvement", "hardware"): "Shopping",
    ("home_improvement", "home_repair_and_maintenance"): None,
    ("home_improvement", "home_security"): None,
    ("home_improvement", "other_home_improvement"): None,
    ("income", "child_support_income"): None,
    ("income", "contractor_income"): None,
    ("income", "dividends"): None,
    ("income", "gig_economy_income"): None,
    ("income", "interest_earned"): None,
    ("income", "long_term_disability_income"): None,
    ("income", "military_income"): None,
    ("income", "rental_income"): None,
    ("income", "retirement_and_pension_income"): None,
    ("income", "salary"): None,
    ("income", "tax_refund"): None,
    ("income", "unemployment_income"): None,
    ("income", "other_income"): None,
    ("loan_disbursements", "auto_loan_disbursement"): None,
    ("loan_disbursements", "cash_advances"): None,
    ("loan_disbursements", "earned_wage_access"): None,
    ("loan_disbursements", "mortgage_disbursement"): None,
    ("loan_disbursements", "personal_loan_disbursement"): None,
    ("loan_disbursements", "student_loan_disbursement"): None,
    ("loan_disbursements", "other_loan_disbursements"): None,
    ("loan_payments", "buy_now_pay_later_payment"): None,
    ("loan_payments", "car_loan_payment"): None,
    ("loan_payments", "cash_advance_repayment"): None,
    ("loan_payments", "credit_card_payment"): None,
    ("loan_payments", "earned_wage_access_repayment"): None,
    ("loan_payments", "mortgage_payment"): None,
    ("loan_payments", "personal_loan_payment"): None,
    ("loan_payments", "student_loan_payment"): None,
    ("loan_payments", "other_loan_payments"): None,
    ("medical", "dental_care"): "Medical",
    ("medical", "eye_care"): "Medical",
    ("medical", "nursing_care"): "Medical",
    ("medical", "pharmacies_and_supplements"): "Medical",
    ("medical", "primary_care"): "Medical",
    ("medical", "veterinary_services"): "Medical",
    ("medical", "other_medical"): "Medical",
    ("personal_care", "gyms_and_fitness_centers"): None,
    ("personal_care", "hair_and_beauty"): None,
    ("personal_care", "laundry_and_dry_cleaning"): None,
    ("personal_care", "other_personal_care"): None,
    ("rent_and_utilities", "gas_and_electricity"): "Rent",
    ("rent_and_utilities", "internet_and_cable"): "Rent",
    ("rent_and_utilities", "rent"): "Rent",
    ("rent_and_utilities", "sewer_and_waste_services"): "Rent",
    ("rent_and_utilities", "telephone"): "Rent",
    ("rent_and_utilities", "water_utility"): "Rent",
    ("rent_and_utilities", "other_rent_and_utilities"): "Rent",
    ("transfer_in", "account_transfer_in"): None,
    ("transfer_in", "deposit"): None,
    ("transfer_in", "investment_and_retirement_funds_transfer_in"): None,
    ("transfer_in", "savings_transfer_in"): None,
    ("transfer_in", "transfer_in_from_apps"): None,
    ("transfer_in", "wire_transfer_in"): None,
    ("transfer_in", "other_transfer_in"): None,
    ("transfer_out", "account_transfer_out"): None,
    ("transfer_out", "crypto_transfer_out"): None,
    ("transfer_out", "investment_and_retirement_funds_transfer_out"): None,
    ("transfer_out", "savings_transfer_out"): None,
    ("transfer_out", "transfer_out_to_apps"): None,
    ("transfer_out", "wire_transfer_out"): None,
    ("transfer_out", "withdrawal"): None,
    ("transfer_out", "other_transfer_out"): None,
    ("transportation", "bike_and_scooter_rentals"): "Transit",
    ("transportation", "gas"): None,
    ("transportation", "parking"): None,
    ("transportation", "public_transportation"): "Transit",
    ("transportation", "taxis_and_rideshares"): "Transit",
    ("transportation", "tolls"): None,
    ("transportation", "other_transportation"): None,
    ("travel", "flights"): "Travel",
    ("travel", "lodging"): "Travel",
    ("travel", "rental_cars"): "Travel",
    ("travel", "other_travel"): "Travel",
    ("other", "other"): None,
    ("unknown", "unknown"): None,
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
