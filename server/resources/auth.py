from datetime import timedelta

from dao import get_user_by_username, insert, users_collection
from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token
from helpers import check_password, hash_password

auth_blueprint = Blueprint("auth", __name__)

# TODO: Exceptions


@auth_blueprint.route("/api/auth/signup", methods=["POST"])
def signup_user():
    # TODO: check that user does not already exist
    body = request.get_json()
    user = {}
    user["username"] = body["username"]
    user["password_hash"] = hash_password(body["password"])
    insert(users_collection, user)
    # TODO: Return cookie?
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
    return {"token": access_token}, 200
