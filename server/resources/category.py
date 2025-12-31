"""
Category API endpoints.

Provides CRUD operations for expense categories.
"""

import logging
from typing import Any

from flask import Blueprint, Response, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import IntegrityError

from models.database import SessionLocal
from models.sql_models import Category
from utils.id_generator import generate_id

logger = logging.getLogger(__name__)

categories_blueprint = Blueprint("categories", __name__)


def _serialize_category(category: Category) -> dict[str, Any]:
    """Convert Category ORM object to dict."""
    return {
        "id": category.id,
        "name": category.name,
    }


@categories_blueprint.route("/api/categories", methods=["GET"])
@jwt_required()
def get_all_categories() -> tuple[Response, int]:
    """Get all categories, ordered by name."""
    db = SessionLocal()
    try:
        categories = (
            db.query(Category)
            .order_by(Category.name)
            .all()
        )
        logger.info(f"Retrieved {len(categories)} categories")
        return jsonify({"data": [_serialize_category(c) for c in categories]}), 200
    finally:
        db.close()


@categories_blueprint.route("/api/categories/<category_id>", methods=["GET"])
@jwt_required()
def get_category(category_id: str) -> tuple[Response, int]:
    """Get a single category by ID."""
    db = SessionLocal()
    try:
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            return jsonify({"error": "Category not found"}), 404
        return jsonify({"data": _serialize_category(category)}), 200
    finally:
        db.close()


@categories_blueprint.route("/api/categories", methods=["POST"])
@jwt_required()
def create_category() -> tuple[Response, int]:
    """Create a new category."""
    data = request.get_json()

    # Validate required fields
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Category name is required"}), 400

    db = SessionLocal()
    try:
        # Check for duplicate name (case-insensitive)
        existing = db.query(Category).filter(Category.name.ilike(name)).first()
        if existing:
            return jsonify({"error": f"Category '{name}' already exists"}), 400

        category = Category(
            id=generate_id("cat"),
            name=name,
        )
        db.add(category)
        db.commit()
        db.refresh(category)

        logger.info(f"Created category: {category.id}")
        return jsonify({"data": _serialize_category(category)}), 201
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating category: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@categories_blueprint.route("/api/categories/<category_id>", methods=["PUT"])
@jwt_required()
def update_category(category_id: str) -> tuple[Response, int]:
    """Update an existing category."""
    data = request.get_json()

    db = SessionLocal()
    try:
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            return jsonify({"error": "Category not found"}), 404

        # Update name if provided
        if "name" in data:
            name = data["name"].strip()
            if not name:
                return jsonify({"error": "Category name cannot be empty"}), 400

            # Check for duplicate name (excluding current category)
            existing = db.query(Category).filter(Category.name.ilike(name), Category.id != category_id).first()
            if existing:
                return jsonify({"error": f"Category '{name}' already exists"}), 400

            category.name = name

        db.commit()
        db.refresh(category)

        logger.info(f"Updated category: {category_id}")
        return jsonify({"data": _serialize_category(category)}), 200
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating category: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@categories_blueprint.route("/api/categories/<category_id>", methods=["DELETE"])
@jwt_required()
def delete_category(category_id: str) -> tuple[Response, int]:
    """
    Delete a category.

    Will fail if the category is in use by any events (database RESTRICT constraint).
    """
    db = SessionLocal()
    try:
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            return jsonify({"error": "Category not found"}), 404

        db.delete(category)
        db.commit()

        logger.info(f"Deleted category: {category_id}")
        return jsonify({"message": "Category deleted"}), 200
    except IntegrityError:
        db.rollback()
        logger.warning(f"Cannot delete category {category_id}: in use by events")
        return jsonify({"error": "Cannot delete category: it is in use by one or more events"}), 400
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting category: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()
