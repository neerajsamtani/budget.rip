from datetime import timedelta

from dao import get_user_by_username, insert, users_collection
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    set_access_cookies,
    unset_jwt_cookies,
)
from helpers import check_password, hash_password
from constants import GATED_USERS

auth_blueprint = Blueprint("auth", __name__)

# TODO: Exceptions


@auth_blueprint.route("/api/auth/signup", methods=["POST"])
def signup_user():
    body = request.get_json()
    user = {}
    if get_user_by_username(body["username"]):
        return jsonify("User Already Exists")
    elif body["username"] not in GATED_USERS:
        # For now, the user must be gated
        return jsonify("User Not Signed Up For Private Beta")
    else:
        user["username"] = body["username"]
        user["password_hash"] = hash_password(body["password"])
        insert(users_collection, user)
        return jsonify("Created User")


@auth_blueprint.route("/api/auth/login", methods=["POST"])
def login_user():
    body = request.get_json()
    user = get_user_by_username(body["username"])
    authorized = check_password(user["password_hash"], body["password"])
    if not authorized:
        return {"error": "Email or password invalid"}, 401

    expires = timedelta(days=3)
    access_token = create_access_token(identity=str(user["_id"]), expires_delta=expires)

    # Set the JWT cookies in the response
    resp = jsonify({"login": True})
    set_access_cookies(resp, access_token)
    return resp, 200


# Because the JWTs are stored in an httponly cookie now, we cannot
# log the user out by simply deleting the cookie in the frontend.
# We need the backend to send us a response to delete the cookies
# in order to logout. unset_jwt_cookies is a helper function to
# do just that.
@auth_blueprint.route("/api/auth/logout", methods=["POST"])
def logout():
    resp = jsonify({"logout": True})
    unset_jwt_cookies(resp)
    return resp, 200
