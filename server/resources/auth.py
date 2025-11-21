import logging

logger = logging.getLogger(__name__)
from datetime import timedelta
from typing import Any, Dict, Optional

from flask import Blueprint, Response, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    set_access_cookies,
    unset_jwt_cookies,
)

from constants import GATED_USERS
from dao import get_user_by_email, insert, users_collection
from helpers import check_password, hash_password
from utils.dual_write import dual_write_operation
from utils.id_generator import generate_id
from utils.pg_bulk_ops import upsert_user

auth_blueprint = Blueprint("auth", __name__)

# TODO: Exceptions


@auth_blueprint.route("/api/auth/signup", methods=["POST"])
def signup_user_api() -> tuple[Response, int]:
    body: Dict[str, Any] = request.get_json()
    user: Dict[str, Any] = {}
    required_fields = ["first_name", "last_name", "email", "password"]
    for field in required_fields:
        if field not in body or not body[field]:
            logger.warning(f"Signup attempt with missing field: {field}")
            return jsonify({"error": f"Missing required field: {field}"}), 400
    if get_user_by_email(body["email"]):
        logger.warning(f"Signup attempt with existing email: {body['email']}")
        return jsonify("User Already Exists"), 400
    elif body["email"] not in GATED_USERS:
        # For now, the user must be gated
        logger.warning(f"Signup attempt by non-gated user: {body['email']}")
        return jsonify("User Not Signed Up For Private Beta"), 403
    else:
        user["id"] = generate_id("user")
        user["first_name"] = body["first_name"]
        user["last_name"] = body["last_name"]
        user["email"] = body["email"]
        user["password_hash"] = hash_password(body["password"])
        dual_write_operation(
            mongo_write_func=lambda: insert(users_collection, user),
            pg_write_func=lambda db: upsert_user(db, user),
            operation_name="create_user",
        )
        logger.info(f"New user created: {body['email']}")
        return jsonify("Created User"), 201


@auth_blueprint.route("/api/auth/login", methods=["POST"])
def login_user_api() -> tuple[Response, int]:
    body: Dict[str, Any] = request.get_json()
    required_fields = ["email", "password"]
    for field in required_fields:
        if field not in body or not body[field]:
            logger.warning(f"Login attempt with missing field: {field}")
            return jsonify({"error": f"Missing required field: {field}"}), 400
    user: Optional[Dict[str, Any]] = get_user_by_email(body["email"])
    if user is None:
        logger.warning(f"Login attempt with non-existent email: {body['email']}")
        return jsonify({"error": "Email or password invalid"}), 401
    authorized: bool = check_password(user["password_hash"], body["password"])
    if not authorized:
        logger.warning(f"Login attempt with invalid password for: {body['email']}")
        return jsonify({"error": "Email or password invalid"}), 401

    expires: timedelta = timedelta(days=3)
    access_token: str = create_access_token(identity=str(user["_id"]), expires_delta=expires)

    # Set the JWT cookies in the response
    resp: Response = jsonify({"login": True})
    set_access_cookies(resp, access_token)
    logger.info(f"User logged in successfully: {body['email']}")
    return resp, 200


# Because the JWTs are stored in an httponly cookie now, we cannot
# log the user out by simply deleting the cookie in the frontend.
# We need the backend to send us a response to delete the cookies
# in order to logout. unset_jwt_cookies is a helper function to
# do just that.
@auth_blueprint.route("/api/auth/logout", methods=["POST"])
def logout_api() -> tuple[Response, int]:
    resp: Response = jsonify({"logout": True})
    unset_jwt_cookies(resp)
    logger.info("User logged out")
    return resp, 200
