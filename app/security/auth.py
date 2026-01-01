from functools import wraps
from flask import jsonify, current_app
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    verify_jwt_in_request,
)
from app.models import User

jwt = JWTManager()


@jwt.user_identity_loader
def user_identity_lookup(user):
    """Convert user to identity for JWT token."""
    if isinstance(user, User):
        return str(user.id)
    return str(user)


@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    """Load user from JWT identity."""
    identity = jwt_data["sub"]
    print(f"DEBUG: Looking up user with identity: {identity}")
    user = User.query.filter_by(id=int(identity)).first()
    print(f"DEBUG: Found user: {user}")
    return user


@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    """Handle expired tokens."""
    return jsonify({"error": "Token has expired", "code": "token_expired"}), 401


@jwt.invalid_token_loader
def invalid_token_callback(error):
    """Handle invalid tokens."""
    print(f"DEBUG: Invalid token error: {error}")
    return jsonify({"error": "Invalid token", "code": "invalid_token"}), 401


@jwt.unauthorized_loader
def missing_token_callback(error):
    """Handle missing tokens."""
    return jsonify({"error": "Authorization required", "code": "missing_token"}), 401


def generate_tokens(user):
    """Generate access and refresh tokens for a user."""
    access_token = create_access_token(identity=user)
    refresh_token = create_refresh_token(identity=user)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
    }
