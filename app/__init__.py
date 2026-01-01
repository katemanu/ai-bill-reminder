import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from app.config import config
from app.models import db
from app.security import jwt, limiter, rate_limit_exceeded_handler
from app.routes import auth_bp, bills_bp

migrate = Migrate()


def create_app(config_name=None):
    """Application factory pattern."""
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    # Register error handlers
    app.register_error_handler(429, rate_limit_exceeded_handler)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(bills_bp)

    # Health check endpoint
    @app.route("/health")
    def health():
        return jsonify({"status": "healthy", "service": "ai-bill-reminder"}), 200

    # Security headers middleware
    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response

    # Create tables
    with app.app_context():
        db.create_all()

    return app
