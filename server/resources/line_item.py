import json
import logging
from typing import Any, Dict, List, Optional

from apiflask import APIBlueprint
from flask import request
from flask_jwt_extended import jwt_required

from dao import get_all_line_items, get_line_item_by_id
from helpers import sort_by_date_amount_descending, str_to_bool
from resources.schemas.line_item import ErrorResponse, LineItemListResponse, LineItemOut

logger = logging.getLogger(__name__)

line_items_blueprint = APIBlueprint("line_items", __name__)

_SECURITY = [{"jwtCookie": []}]
_ERROR_RESPONSES = {
    404: {"description": "Not found", "schema": ErrorResponse},
}


class LineItem:
    """
    Line item data transfer object.

    Fields:
        source_id: External API transaction ID (e.g., Venmo's ID). Used during creation
                   to link line items to their source transactions.
        transaction_id: Database transaction foreign key (txn_xxx). Populated after
                       line items are inserted into the database.
    """

    def __init__(
        self,
        date: float,
        responsible_party: str,
        payment_method: str,
        description: str,
        amount: float,
        id: str = "",
        source_id: str = "",
        transaction_id: str = "",
    ) -> None:
        self.id = id
        self.date = date
        self.responsible_party = responsible_party
        self.payment_method = payment_method
        self.description = description
        self.amount = amount
        self.source_id = source_id  # External API ID (e.g., Venmo's transaction ID)
        self.transaction_id = transaction_id  # Database transaction FK (e.g., txn_abc123)

    def serialize(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "date": self.date,
            "responsible_party": self.responsible_party,
            "payment_method": self.payment_method,
            "description": self.description,
            "amount": self.amount,
        }

    def __repr__(self) -> str:
        return f"""{{
        id: {self.id}
        date: {self.date}
        responsible_party: {self.responsible_party}
        payment_method: {self.payment_method}
        description: {self.description}
        amount: {self.amount}
        }}
        """

    def to_json(self) -> str:
        """
        convert the instance of this class to json
        """
        return json.dumps(self, indent=4, default=lambda o: o.__dict__)


@line_items_blueprint.get("/api/line_items")
@line_items_blueprint.output(LineItemListResponse)
@line_items_blueprint.doc(security=_SECURITY)
@jwt_required()
def all_line_items_api():
    """Get all line items, optionally filtered by payment method or review status."""
    only_line_items_to_review: Optional[bool] = str_to_bool(request.args.get("only_line_items_to_review"))
    payment_method: Optional[str] = request.args.get("payment_method")
    items = all_line_items(only_line_items_to_review, payment_method)
    line_items_total: float = sum(item["amount"] for item in items)
    logger.info(f"Retrieved {len(items)} line items (total: ${line_items_total:.2f})")
    return LineItemListResponse(total=line_items_total, data=items)


def all_line_items(
    only_line_items_to_review: Optional[bool] = None,
    payment_method: Optional[str] = None,
) -> List[Dict[str, Any]]:
    filters: Dict[str, Any] = {}
    if payment_method not in ["All", None]:
        filters["payment_method"] = payment_method

    if only_line_items_to_review:
        # Only get line items that don't have an event associated
        filters["event_id"] = {"$exists": False}

    line_items: List[Dict[str, Any]] = get_all_line_items(filters)
    line_items = sort_by_date_amount_descending(line_items)
    return line_items


@line_items_blueprint.get("/api/line_items/<line_item_id>")
@line_items_blueprint.output(LineItemOut)
@line_items_blueprint.doc(responses=_ERROR_RESPONSES)
def get_line_item_api(line_item_id: str):
    """Get a single line item by ID."""
    from helpers import get_or_404

    line_item = get_or_404(get_line_item_by_id(line_item_id), "Line item not found")
    logger.info(f"Retrieved line item: {line_item_id}")
    return LineItemOut(**line_item)
