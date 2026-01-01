from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, current_user
from pydantic import ValidationError
from app.models import db, User
from app.security import (
    generate_tokens,
    limiter,
    UserRegistration,
    UserLogin,
)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
@limiter.limit("5 per hour")
def register():
    """Register a new user."""
    try:
        data = UserRegistration(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": "Validation failed", "details": e.errors()}), 400

    if User.query.filter_by(email=data.email).first():
        return jsonify({"error": "Email already registered"}), 409

    user = User(email=data.email, name=data.name)
    user.set_password(data.password)

    db.session.add(user)
    db.session.commit()

    tokens = generate_tokens(user)
    return jsonify({
        "message": "Registration successful",
        "user": user.to_dict(),
        **tokens,
    }), 201


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    """Authenticate user and return tokens."""
    try:
        data = UserLogin(**request.get_json())
    except ValidationError as e:
        return jsonify({"error": "Validation failed", "details": e.errors()}), 400

    user = User.query.filter_by(email=data.email).first()

    if not user or not user.check_password(data.password):
        return jsonify({"error": "Invalid email or password"}), 401

    if not user.is_active:
        return jsonify({"error": "Account is disabled"}), 403

    tokens = generate_tokens(user)
    return jsonify({
        "message": "Login successful",
        "user": user.to_dict(),
        **tokens,
    }), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user():
    """Get current authenticated user."""
    return jsonify({"user": current_user.to_dict()}), 200


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh_token():
    """Refresh access token."""
    from flask_jwt_extended import create_access_token
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify({"access_token": access_token, "token_type": "Bearer"}), 200
