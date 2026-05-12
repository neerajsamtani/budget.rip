"""
Category API endpoints.

Provides CRUD operations for expense categories.
"""

import logging

from apiflask import APIBlueprint, abort
from flask_jwt_extended import get_current_user, jwt_required
from sqlalchemy.exc import IntegrityError

from helpers import get_or_404
from models.database import SessionLocal
from models.sql_models import Category
from resources._common import JWT_SECURITY, STANDARD_ERROR_RESPONSES
from resources.schemas.category import (
    CategoryCreateIn,
    CategoryListResponse,
    CategorySingleResponse,
    CategoryUpdateIn,
    MessageResponse,
)
from utils.id_generator import generate_id

logger = logging.getLogger(__name__)

categories_blueprint = APIBlueprint("categories", __name__)


@categories_blueprint.get("/api/categories")
@categories_blueprint.output(CategoryListResponse)
@categories_blueprint.doc(security=JWT_SECURITY)
@jwt_required()
def get_all_categories():
    """Get all categories for the current user, ordered by name."""
    user_id = get_current_user()["id"]

    with SessionLocal.begin() as db:
        categories = db.query(Category).filter(Category.user_id == user_id).order_by(Category.name).all()
        return CategoryListResponse(data=[{"id": c.id, "name": c.name} for c in categories])


@categories_blueprint.get("/api/categories/<category_id>")
@categories_blueprint.output(CategorySingleResponse)
@categories_blueprint.doc(security=JWT_SECURITY, responses=STANDARD_ERROR_RESPONSES)
@jwt_required()
def get_category(category_id: str):
    """Get a single category by ID for the current user."""
    user_id = get_current_user()["id"]

    with SessionLocal.begin() as db:
        category = get_or_404(
            db.query(Category).filter(Category.id == category_id, Category.user_id == user_id).first(),
            "Category not found",
        )
        return CategorySingleResponse(data={"id": category.id, "name": category.name})


@categories_blueprint.post("/api/categories")
@categories_blueprint.input(CategoryCreateIn, arg_name="body")
@categories_blueprint.output(CategorySingleResponse, status_code=201)
@categories_blueprint.doc(security=JWT_SECURITY, responses=STANDARD_ERROR_RESPONSES)
@jwt_required()
def create_category(body: CategoryCreateIn):
    """Create a new category for the current user."""
    user_id = get_current_user()["id"]

    name = body.name.strip()
    if not name:
        abort(400, message="Category name is required")

    body = CategoryCreateIn(name=name)

    with SessionLocal.begin() as db:
        existing = db.query(Category).filter(Category.user_id == user_id, Category.name.ilike(body.name)).first()
        if existing:
            abort(400, message=f"Category '{body.name}' already exists")

        category = Category(id=generate_id("cat"), user_id=user_id, name=body.name)
        db.add(category)

        logger.info(f"Created category: {category.id} for user {user_id}")
        return CategorySingleResponse(data={"id": category.id, "name": category.name}), 201


@categories_blueprint.put("/api/categories/<category_id>")
@categories_blueprint.input(CategoryUpdateIn, arg_name="body")
@categories_blueprint.output(CategorySingleResponse)
@categories_blueprint.doc(security=JWT_SECURITY, responses=STANDARD_ERROR_RESPONSES)
@jwt_required()
def update_category(category_id: str, body: CategoryUpdateIn):
    """Update an existing category for the current user."""
    user_id = get_current_user()["id"]

    with SessionLocal.begin() as db:
        category = get_or_404(
            db.query(Category).filter(Category.id == category_id, Category.user_id == user_id).first(),
            "Category not found",
        )

        if body.name is not None:
            name = body.name.strip()
            if not name:
                abort(400, message="Category name cannot be empty")
            existing = (
                db.query(Category)
                .filter(Category.user_id == user_id, Category.name.ilike(name), Category.id != category_id)
                .first()
            )
            if existing:
                abort(400, message=f"Category '{name}' already exists")
            category.name = name

        return CategorySingleResponse(data={"id": category.id, "name": category.name})


@categories_blueprint.delete("/api/categories/<category_id>")
@categories_blueprint.output(MessageResponse, status_code=204)
@categories_blueprint.doc(security=JWT_SECURITY, responses=STANDARD_ERROR_RESPONSES)
@jwt_required()
def delete_category(category_id: str):
    """
    Delete a category for the current user.

    Will fail if the category is in use by any events (database RESTRICT constraint).
    """
    user_id = get_current_user()["id"]

    try:
        with SessionLocal.begin() as db:
            category = get_or_404(
                db.query(Category).filter(Category.id == category_id, Category.user_id == user_id).first(),
                "Category not found",
            )
            db.delete(category)
            logger.info(f"Deleted category: {category_id} for user {user_id}")
            return MessageResponse(message="Category deleted"), 204
    except IntegrityError:
        logger.warning(f"Cannot delete category {category_id}: in use by events")
        abort(400, message="Cannot delete category: it is in use by one or more events")
