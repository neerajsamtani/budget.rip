import json
import logging
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

from flask import Blueprint, Response, jsonify, request
from flask_jwt_extended import jwt_required

from helpers import html_date_to_posix, sort_by_date_description, str_to_bool
from queries import get_all_line_items, get_line_item_by_id

logger = logging.getLogger(__name__)

line_items_blueprint = Blueprint("line_items", __name__)


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


@line_items_blueprint.route("/api/line_items", methods=["GET"])
@jwt_required()
def all_line_items_api() -> tuple[Response, int]:
    """
    Get All Line Items
        - Payment Method (optional)
        - Only Line Items To Review (optional)
        - Limit (optional)
        - Offset (optional)
    """
    only_line_items_to_review: Optional[bool] = str_to_bool(request.args.get("only_line_items_to_review"))
    payment_method: Optional[str] = request.args.get("payment_method")
    limit: Optional[int] = int(request.args["limit"]) if "limit" in request.args else None
    offset: int = int(request.args.get("offset", 0))
    line_items: List[Dict[str, Any]] = all_line_items(only_line_items_to_review, payment_method, limit, offset)
    line_items_total: float = sum(line_item["amount"] for line_item in line_items)
    logger.info(f"Retrieved {len(line_items)} line items (total: ${line_items_total:.2f})")
    return jsonify({"total": line_items_total, "data": line_items}), 200


def all_line_items(
    only_line_items_to_review: Optional[bool] = None,
    payment_method: Optional[str] = None,
    limit: Optional[int] = None,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    line_items: List[Dict[str, Any]] = get_all_line_items(
        payment_method=payment_method,
        only_unreviewed=bool(only_line_items_to_review),
        limit=limit,
        offset=offset,
    )
    line_items = sort_by_date_description(line_items)
    return line_items


@line_items_blueprint.route("/api/line_items/<line_item_id>", methods=["GET"])
@jwt_required()
def get_line_item_api(line_item_id: str) -> tuple[Response, int]:
    """
    Get A Line Item
    """
    line_item: Optional[Dict[str, Any]] = get_line_item_by_id(line_item_id)
    if line_item is None:
        logger.warning(f"Line item not found: {line_item_id}")
        return jsonify({"error": "Line item not found"}), 404
    logger.info(f"Retrieved line item: {line_item_id}")
    return jsonify(line_item), 200


@line_items_blueprint.route("/api/line_items/<line_item_id>", methods=["PUT"])
@jwt_required()
def update_line_item_api(line_item_id: str) -> tuple[Response, int]:
    """
    Update a manual line item.

    Synced API-backed line items are intentionally read-only so refreshes from
    the source system remain the authority for their normalized fields.
    """
    from models.database import SessionLocal
    from models.sql_models import LineItem as SQLLineItem, PaymentMethod

    data: Dict[str, Any] = request.get_json() or {}
    required_fields = ["date", "responsible_party", "description", "amount", "payment_method_id"]
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

    try:
        posix_date = html_date_to_posix(data["date"])
        transaction_date = datetime.fromtimestamp(posix_date, UTC)
    except Exception:
        return jsonify({"error": "Invalid date"}), 400

    try:
        amount = Decimal(str(data["amount"]))
    except (InvalidOperation, TypeError, ValueError):
        return jsonify({"error": "Invalid amount"}), 400

    description = str(data["description"]).strip()
    if not description:
        return jsonify({"error": "Description is required"}), 400

    responsible_party = str(data.get("responsible_party") or "").strip()
    notes = data.get("notes")
    notes = None if notes is None else str(notes)

    with SessionLocal.begin() as db:
        line_item = (
            db.query(SQLLineItem)
            .filter(SQLLineItem.id == line_item_id)
            .first()
        )
        if line_item is None:
            return jsonify({"error": "Line item not found"}), 404

        if not line_item.transaction or line_item.transaction.source != "manual":
            return jsonify({"error": "Synced line items cannot be edited"}), 400

        payment_method = db.query(PaymentMethod).filter(PaymentMethod.id == data["payment_method_id"]).first()
        if not payment_method:
            return jsonify({"error": f"Payment method not found: {data['payment_method_id']}"}), 400

        line_item.date = transaction_date
        line_item.amount = amount
        line_item.description = description
        line_item.payment_method_id = data["payment_method_id"]
        line_item.responsible_party = responsible_party
        line_item.notes = notes

        line_item.transaction.transaction_date = transaction_date
        line_item.transaction.source_data = {
            **(line_item.transaction.source_data or {}),
            "date": posix_date,
            "person": responsible_party,
            "description": description,
            "amount": float(amount),
            "payment_method_id": data["payment_method_id"],
        }

    updated_line_item = get_line_item_by_id(line_item_id)
    logger.info(f"Updated line item: {line_item_id}")
    return jsonify(updated_line_item), 200
