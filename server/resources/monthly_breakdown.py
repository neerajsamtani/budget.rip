import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List

from flask import Blueprint, Response, jsonify
from flask_jwt_extended import jwt_required

from dao import get_categorized_data
from helpers import empty_list

monthly_breakdown_blueprint = Blueprint("monthly_breakdown", __name__)

# TODO: Exceptions


def month_year_range(all_dates_dt: List[datetime]) -> List[str]:
    """Generate all month-year strings (m-YYYY) from min to max date inclusive."""
    if not all_dates_dt:
        return []
    min_date = min(all_dates_dt)
    max_date = max(all_dates_dt)
    months = []
    cur = min_date
    while cur <= max_date:
        months.append(f"{cur.month}-{cur.year}")
        # Move to next month
        if cur.month == 12:
            cur = cur.replace(year=cur.year + 1, month=1)
        else:
            cur = cur.replace(month=cur.month + 1)
    return months


@monthly_breakdown_blueprint.route("/api/monthly_breakdown")
@jwt_required()
def get_monthly_breakdown_api() -> tuple[Response, int]:
    """
    Get Monthly Breakdown For Plotly Graph
    """
    categorized_data: List[Dict[str, Any]] = get_categorized_data()
    categories: Dict[str, List[Dict[str, Any]]] = defaultdict(empty_list)
    seen_dates: set[str] = set()
    all_dates: List[str] = []
    for row in categorized_data:
        category: str = row["category"]
        formatted_date: str = f"{row['month']}-{row['year']}"
        seen_dates.add(formatted_date)
        categories[category].append(
            {"date": formatted_date, "amount": row["totalExpense"]}
        )
        all_dates.append(formatted_date)
    if not all_dates:
        logging.info("No categorized data found for monthly breakdown")
        return jsonify({}), 200
    # Find min and max date
    all_dates_dt = [datetime.strptime(d, "%m-%Y") for d in all_dates]
    full_range = month_year_range(all_dates_dt)
    # Ensure no categories have missing dates in the full range
    for category, info in categories.items():
        info_dates = {x["date"] for x in info}
        unseen_dates = set(full_range).difference(info_dates)
        info.extend([{"date": x, "amount": 0.0} for x in unseen_dates])
        info.sort(key=lambda x: datetime.strptime(x["date"], "%m-%Y").date())

    total_categories = len(categories)
    total_amount = sum(
        sum(item["amount"] for item in category_data)
        for category_data in categories.values()
    )
    logging.info(
        f"Generated monthly breakdown: {total_categories} categories, total amount: ${total_amount:.2f}"
    )
    return jsonify(categories), 200
