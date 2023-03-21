from datetime import date, datetime, timedelta
from functools import wraps
import json
import os
import secrets

import bcrypt
from dotenv import load_dotenv
from flask import Flask, request, abort
from flask_cors import CORS
import jwt

from budgee.db import Database
from budgee.schemas import AccountSchema, EntrySchema, UserSchema


app = Flask(__name__)
secret = secrets.token_hex()
CORS(app, supports_credentials=True)

if (app.debug):
    load_dotenv(".env.test")
else:
    load_dotenv()

DB_USER = os.environ["BUDGIE_DB_USER"]
DB_PASSWORD = os.environ["BUDGIE_DB_PASSWORD"]
DB_HOST = os.environ["BUDGIE_DB_HOST"]
DB_PORT = os.environ["BUDGIE_DB_PORT"]
DB_DATABASE = os.environ["BUDGIE_DB_DATABASE"]

DB_STRING = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}"
)

backend = Database(DB_STRING)


def json_response(content):
    return app.response_class(response=content, mimetype="application/json")


def auth_required(route):
    @wraps(route)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization").split()[1]
        try:
            token = jwt.decode(token, secret, algorithms=["HS256"])
        except jwt.InvalidSignatureError:
            abort(401)
        email = token["user_id"]
        backend.set_current_user(email)
        return route(*args, **kwargs)

    return wrapper


@app.route("/")
def index():
    return "<h1>Welcome to budgie API</h1>"


@app.route("/account", methods=["GET", "POST"])
@auth_required
def account():
    args = request.args.to_dict()
    if request.method == "GET":
        return json_response(
            AccountSchema(many=True).dumps(backend.list_accounts(**args))
        )
    if request.method == "POST":
        acc = AccountSchema().load(request.get_json())
        backend.create_account(acc)
        return json_response(AccountSchema().dumps(acc))


@app.route("/entry", methods=["GET", "POST"])
@auth_required
def entries():
    args = request.args.to_dict()
    if request.method == "GET":
        entries = EntrySchema(many=True).dumps(backend.list_entries(**args))
        return json_response(entries)
    if request.method == "POST":
        entry = EntrySchema().load(request.get_json())
        if not backend.add_entry(entry):
            return abort(404)
        return json_response(EntrySchema().dumps(entry))


@app.route("/entry/<int:entry_id>", methods=["DELETE"])
@auth_required
def entry(entry_id):
    if request.method == "DELETE":
        deleted = backend.delete_entry(entry_id)
        if not deleted:
            abort(404)

    return ""


@app.route("/auth/register", methods=["POST"])
def register():
    user_data = request.get_json()
    user = user_data
    user["salt"] = bcrypt.gensalt()
    user["password"] = bcrypt.hashpw(user_data["password"].encode(), user["salt"])
    user["created"] = date.today().isoformat()
    user = UserSchema().load(user)
    backend.create_user(user)
    # TODO: Add proper response if user exists or not
    return ""


@app.route("/auth/login", methods=["GET"])
def login():
    password = request.authorization.password
    email = request.authorization.username

    user = backend.get_user(email)
    if not user or not bcrypt.checkpw(password.encode(), user["password"].encode()):
        return json_response(json.dumps({"token": None}))

    expiry_time = datetime.utcnow() + timedelta(minutes=30)
    token = jwt.encode(
        {"user_id": user["email"], "exp": expiry_time}, secret, algorithm="HS256"
    )
    return json_response(json.dumps({"token": token}))
