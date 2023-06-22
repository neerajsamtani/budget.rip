from collections import defaultdict
from datetime import datetime

from dao import get_categorized_data
from flask import Blueprint
from helpers import empty_list

monthly_breakdown = Blueprint("monthly_breakdown", __name__)

# TODO: Exceptions


@monthly_breakdown.route("/api/monthly_breakdown")
def get_monthly_breakdown():
    """
    Get Monthly Breakdown For Plotly Graph
    """
    categorized_data = get_categorized_data()
    categories = defaultdict(empty_list)
    seen_dates = set()
    for row in categorized_data:
        category = row["category"]
        formatted_date = f"{row['month']}-{row['year']}"
        seen_dates.add(formatted_date)
        categories[category].append(
            {"date": formatted_date, "amount": row["totalExpense"]}
        )
    # Ensure no categories have missing dates
    for category, info in categories.items():
        unseen_dates = seen_dates.difference([x["date"] for x in info])
        info.extend([{"date": x, "amount": 0.0} for x in unseen_dates])
        info.sort(key=lambda x: datetime.strptime(x["date"], "%m-%Y").date())
    return categories