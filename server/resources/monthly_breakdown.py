import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List

from apiflask import APIBlueprint
from flask_jwt_extended import jwt_required

from dao import get_categorized_data
from helpers import empty_list
from resources._common import JWT_SECURITY
from resources.schemas.monthly_breakdown import MonthlyBreakdownResponse

logger = logging.getLogger(__name__)

monthly_breakdown_blueprint = APIBlueprint("monthly_breakdown", __name__)


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
        if cur.month == 12:
            cur = cur.replace(year=cur.year + 1, month=1)
        else:
            cur = cur.replace(month=cur.month + 1)
    return months


@monthly_breakdown_blueprint.get("/api/monthly_breakdown")
@monthly_breakdown_blueprint.output(MonthlyBreakdownResponse)
@monthly_breakdown_blueprint.doc(security=JWT_SECURITY)
@jwt_required()
def get_monthly_breakdown_api():
    """Get monthly spending breakdown grouped by category for graphing."""
    categorized_data: List[Dict[str, Any]] = get_categorized_data()
    categories: Dict[str, List[Dict[str, Any]]] = defaultdict(empty_list)
    all_dates: List[str] = []

    for row in categorized_data:
        category: str = row["category"]
        formatted_date: str = f"{row['month']}-{row['year']}"
        categories[category].append({"date": formatted_date, "amount": row["totalExpense"]})
        all_dates.append(formatted_date)

    if not all_dates:
        logger.info("No categorized data found for monthly breakdown")
        return MonthlyBreakdownResponse(root={})

    all_dates_dt = [datetime.strptime(d, "%m-%Y") for d in all_dates]
    full_range = month_year_range(all_dates_dt)

    for category, info in categories.items():
        info_dates = {x["date"] for x in info}
        unseen_dates = set(full_range).difference(info_dates)
        info.extend([{"date": x, "amount": 0.0} for x in unseen_dates])
        info.sort(key=lambda x: datetime.strptime(x["date"], "%m-%Y").date())

    total_categories = len(categories)
    total_amount = sum(sum(item["amount"] for item in category_data) for category_data in categories.values())
    logger.info(f"Generated monthly breakdown: {total_categories} categories, total amount: ${total_amount:.2f}")
    return MonthlyBreakdownResponse(root=categories)
