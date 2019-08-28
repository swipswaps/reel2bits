from flask import Blueprint, request, jsonify, abort, current_app
from models import db, User, user_datastore, Role, create_actor, OAuth2Token, OAuth2Client
from flask_security.utils import hash_password
from flask_security import confirmable as FSConfirmable
from app_oauth import authorization, require_oauth
from authlib.flask.oauth2 import current_token
from datas_helpers import to_json_account
import re

bp_api_v1_accounts = Blueprint("bp_api_v1_accounts", __name__)

username_is_legal = re.compile("^[a-zA-Z0-9]+$")

# Parameters needed:
#  nickname(==username), email, fullname, password, confirm, agreement, locale(dropped here for now)
# Optionals:
#  bio
@bp_api_v1_accounts.route("/api/v1/accounts", methods=["POST"])
def accounts():
    """
    Register an account
    The method is available to apps with a token obtained via the client credentials grant.
    It creates a user and account records, as well as an access token for the app that initiated the request.
    The method returns the access token, which the app should save for later.
    ---
    tags:
        - Accounts
    definitions:
      Token:
        type: object
        properties:
            access_token:
                type: string
            token_type:
                type: string
            scope:
                type: string
            created_at:
                type: integer
    responses:
      200:
        description: Returns Token
        schema:
            $ref: '#/definitions/Token'
    """
    errors = {}

    # Get the bearer token
    bearer = None
    if "Authorization" in request.headers:
        b = request.headers.get("Authorization")
        b = b.strip().split(" ")
        if len(b) == 2:
            bearer = b[1]
        else:
            errors["bearer"] = ["API Bearer Authorization format issue"]
    else:
        current_app.logging.info("/api/v1/accounts: no Authorization bearer given")

    if not request.json:
        abort(400)

    if "nickname" not in request.json:
        errors["nickname"] = ["nickname is missing"]
    if "email" not in request.json:
        errors["email"] = ["email is missing"]
    if "fullname" not in request.json:
        errors["fullname"] = ["fullname is missing"]
    if "password" not in request.json:
        errors["password"] = ["password is missing"]
    if "confirm" not in request.json:
        errors["confirm"] = ["password confirm is missing"]
    if "agreement" not in request.json:
        errors["agreement"] = ["agreement is missing"]

    if len(errors) > 0:
        return jsonify({"error": str(errors)}), 400

    if request.json["password"] != request.json["confirm"]:
        return jsonify({"error": str({"confirm": ["passwords doesn't match"]})}), 400

    if "agreement" not in request.json:
        return jsonify({"error": str({"agreement": ["you need to accept the terms and conditions"]})}), 400

    # Check if user already exists by username
    user = User.query.filter(User.name == request.json["username"]).first()
    if user:
        return jsonify({"error": str({"ap_id": ["has already been taken"]})}), 400

    # Check if user already exists by email
    user = User.query.filter(User.email == request.json["email"]).first()
    if user:
        return jsonify({"error": str({"email": ["has already been taken"]})}), 400

    # Check username is valid
    # /^[a-zA-Z\d]+$/
    if not username_is_legal.match(request.json["username"]):
        return jsonify({"error": str({"ap_id": ["should contains only letters and numbers"]})}), 400

    # Proceed to register the user
    role = Role.query.filter(Role.name == "user").first()
    if not role:
        return jsonify({"error": "server error"}), 500

    u = user_datastore.create_user(
        name=request.json["username"],
        email=request.json["email"],
        display_name=request.json["fullname"],
        password=hash_password(request.json["password"]),
        roles=[role],
    )

    actor = create_actor(u)
    actor.user = u
    actor.user_id = u.id
    if "bio" in request.json:
        actor.summary = request.json["bio"]

    db.session.add(actor)
    db.session.commit()

    if FSConfirmable.requires_confirmation(u):
        FSConfirmable.send_confirmation_instructions(u)

    # get the matching item from the given bearer
    bearer_item = OAuth2Token.query.filter(OAuth2Token.access_token == bearer).first()
    if not bearer_item:
        abort(400)
    client_item = OAuth2Client.query.filter(OAuth2Client.client_id == bearer_item.client_id).first()
    if not client_item:
        abort(400)

    # https://github.com/lepture/authlib/blob/master/authlib/oauth2/rfc6749/grants/base.py#L51
    token = authorization.generate_token(
        client_item.client_id, "client_credentials", user=u, scope=client_item.scope, expires_in=None
    )

    tok = OAuth2Token()
    tok.user_id = u.id
    tok.client_id = client_item.client_id
    # the frontend should request an app every time it doesn't have one in local storage
    # and this app should allow delivering a somewhat non usuable Token
    # token which gets sent to this endpoint and gets used to get back the right client_id
    # to associate in the database...
    tok.token_type = token["token_type"]
    tok.access_token = token["access_token"]
    tok.refresh_token = None
    tok.scope = token["scope"]
    tok.revoked = False
    tok.expires_in = token["expires_in"]
    db.session.add(tok)
    db.session.commit()

    return jsonify({**token, "created_at": tok.issued_at}), 200


@bp_api_v1_accounts.route("/api/v1/accounts/verify_credentials", methods=["GET"])
@require_oauth("read")
def accounts_verify_credentials():
    """
    User’s own account.
    ---
    tags:
        - Accounts
    security:
        - OAuth2:
            - read
    definitions:
      Field:
        type: object
        properties:
            name:
                type: string
                nullable: false
            value:
                type: string
                nullable: false
            verified_at:
                type: integer
                nullable: true
      Emoji:
        type: object
        properties:
            shortcode:
                type: string
                nullable: false
            static_url:
                type: string
                format: uri
                nullable: false
            url:
                type: string
                format: uri
                nullable: false
            visible_in_picker:
                type: boolean
                nullable: false
      Source:
        type: object
        properties:
            privacy:
                type: string
                nullable: true
            sensitive:
                type: boolean
                nullable: true
            language:
                type: string
                nullable: true
            note:
                type: string
                nullable: false
            fields:
                type: array
                nullable: false
                items:
                    type: object
                    $ref: '#/definitions/Field'
      AccountPleroma:
        type: object
        properties:
            pleroma:
                type: object
                properties:
                    is_admin:
                        type: boolean
      Account:
        type: object
        properties:
            id:
                type: string
                nullable: false
            username:
                type: string
                nullable: false
            acct:
                type: string
                nullable: false
            display_name:
                type: integer
                nullable: false
            locked:
                type: boolean
                nullable: false
            created_at:
                type: integer
                nullable: false
            followers_count:
                type: integer
                nullable: false
            following_count:
                type: integer
                nullable: false
            statuses_count:
                type: integer
                nullable: false
            note:
                type: string
                nullable: false
            url:
                type: string
                format: uri
                nullable: false
            avatar:
                type: string
                format: uri
                nullable: false
            avatar_static:
                type: string
                format: uri
                nullable: false
            header:
                type: string
                format: uri
                nullable: false
            header_static:
                type: string
                format: uri
                nullable: false
            emojis:
                type: hash
                nullable: false
                items:
                    type: object
                    $ref: '#/definitions/Emoji'
            moved:
                type: object
                $ref: '#/definitions/Account'
                nullable: true
            fields:
                type: array
                nullable: true
                items:
                    type: object
                    $ref: '#/definitions/Field'
            bot:
                type: boolean
                nullable: true
    responses:
        200:
            description: Returns Account with extra Source and Pleroma attributes.
            schema:
                allOf:
                    - $ref: '#/definitions/Account'
                    - $ref: '#/definitions/Source'
                    - $ref: '#/definitions/AccountPleroma'
    """
    user = current_token.user
    return jsonify(to_json_account(user))
