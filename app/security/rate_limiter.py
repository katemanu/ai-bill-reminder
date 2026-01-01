from flask import jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per hour"],
    storage_uri="memory://",
)


@limiter.request_filter
def ip_whitelist():
    """Skip rate limiting for health checks."""
    from flask import request
    return request.endpoint == "health"


def rate_limit_exceeded_handler(e):
    """Handle rate limit exceeded errors."""
    return jsonify({
        "error": "Rate limit exceeded",
        "code": "rate_limit_exceeded",
        "message": "Too many requests. Please slow down.",
    }), 429
