import logging
from datetime import timedelta

from apiflask import APIBlueprint, abort
from flask import after_this_request
from flask_jwt_extended import (
    create_access_token,
    get_current_user,
    jwt_required,
    set_access_cookies,
    unset_jwt_cookies,
)

from constants import GATED_USERS
from dao import get_user_by_email
from helpers import check_password, hash_password
from resources._common import AUTH_ERROR_RESPONSES, JWT_SECURITY
from resources.schemas.auth import (
    LoginIn,
    LoginResponse,
    LogoutResponse,
    SignupIn,
    SignupResponse,
    UserOut,
)
from utils.id_generator import generate_id
from utils.pg_bulk_ops import upsert_user

logger = logging.getLogger(__name__)

auth_blueprint = APIBlueprint("auth", __name__)


@auth_blueprint.post("/api/auth/signup")
@auth_blueprint.input(SignupIn, arg_name="body")
@auth_blueprint.output(SignupResponse, status_code=201)
@auth_blueprint.doc(responses=AUTH_ERROR_RESPONSES)
def signup_user_api(body: SignupIn):
    for field in ["first_name", "last_name", "email", "password"]:
        if not getattr(body, field):
            logger.warning(f"Signup attempt with missing field: {field}")
            abort(400, message=f"Missing required field: {field}")
    if get_user_by_email(body.email):
        logger.warning(f"Signup attempt with existing email: {body.email}")
        abort(400, message="User Already Exists")
    elif body.email not in GATED_USERS:
        logger.warning(f"Signup attempt by non-gated user: {body.email}")
        abort(403, message="User Not Signed Up For Private Beta")

    user = {
        "id": generate_id("user"),
        "first_name": body.first_name,
        "last_name": body.last_name,
        "email": body.email,
        "password_hash": hash_password(body.password),
    }

    user_created = upsert_user(user)
    if user_created:
        logger.info(f"New user created: {body.email}")
        return SignupResponse(message="Created User"), 201
    else:
        logger.warning(f"User already exists: {body.email}")
        abort(400, message="User Already Exists")


@auth_blueprint.post("/api/auth/login")
@auth_blueprint.input(LoginIn, arg_name="body")
@auth_blueprint.output(LoginResponse)
@auth_blueprint.doc(responses=AUTH_ERROR_RESPONSES)
def login_user_api(body: LoginIn):
    for field in ["email", "password"]:
        if not getattr(body, field):
            logger.warning(f"Login attempt with missing field: {field}")
            abort(400, message=f"Missing required field: {field}")
    user = get_user_by_email(body.email)
    if user is None:
        logger.warning(f"Login attempt with non-existent email: {body.email}")
        abort(401, message="Email or password invalid")
    if not check_password(user["password_hash"], body.password):
        logger.warning(f"Login attempt with invalid password for: {body.email}")
        abort(401, message="Email or password invalid")

    expires = timedelta(days=3)
    access_token = create_access_token(identity=str(user["id"]), expires_delta=expires)

    # JWTs are stored in httponly cookies; set_access_cookies must run after APIFlask
    # serializes the response, so we use after_this_request
    @after_this_request
    def set_cookies(response):
        set_access_cookies(response, access_token)
        return response

    logger.info(f"User logged in successfully: {body.email}")
    return LoginResponse(login=True)


# JWTs are stored in httponly cookies, so the frontend cannot clear them directly.
# The backend must send an unset-cookie response to log the user out.
@auth_blueprint.post("/api/auth/logout")
@auth_blueprint.output(LogoutResponse)
def logout_api():
    @after_this_request
    def clear_cookies(response):
        unset_jwt_cookies(response)
        return response

    logger.info("User logged out")
    return LogoutResponse(logout=True)


@auth_blueprint.get("/api/auth/me")
@auth_blueprint.output(UserOut)
@auth_blueprint.doc(security=JWT_SECURITY, responses=AUTH_ERROR_RESPONSES)
@jwt_required()
def get_current_user_api():
    """Returns the current authenticated user's information."""
    user = get_current_user()
    if user is None:
        abort(404, message="User not found")
    return UserOut(
        id=str(user.get("id")),
        email=user.get("email"),
        first_name=user.get("first_name"),
        last_name=user.get("last_name"),
    )
