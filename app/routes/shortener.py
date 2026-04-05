import datetime
from urllib.parse import urlparse

from flask import Blueprint, jsonify, redirect, request
from peewee import DoesNotExist, IntegrityError

from app.models.url import ShortenedURL, generate_short_code

shortener_bp = Blueprint("shortener", __name__)


def is_valid_url(url: str) -> bool:
    """Validate that the given string is a proper HTTP/HTTPS URL."""
    try:
        if " " in url:
            return False
        result = urlparse(url)
        return result.scheme in ("http", "https") and bool(result.netloc)
    except Exception:
        return False


# ─── POST /urls — Create a shortened URL ─────────────────────────────────────

@shortener_bp.route("/urls", methods=["POST"])
def create_url():
    """Create a shortened URL (evaluator-compatible endpoint)."""
    data = request.get_json(silent=True)

    if not data or "original_url" not in data:
        return jsonify({"error": "Missing 'original_url' field in request body"}), 400

    original_url = data["original_url"]

    if not isinstance(original_url, str) or not original_url.strip():
        return jsonify({"error": "URL must be a non-empty string"}), 400

    original_url = original_url.strip()

    if not is_valid_url(original_url):
        return jsonify({"error": "Invalid URL. Must be a valid HTTP or HTTPS URL"}), 400

    user_id = data.get("user_id")
    title = data.get("title", "")
    is_active = data.get("is_active", True)

    for _ in range(5):
        short_code = generate_short_code()
        try:
            url_entry = ShortenedURL.create(
                original_url=original_url,
                short_code=short_code,
                user_id=user_id,
                title=title,
                is_active=is_active,
            )
            return (
                jsonify(
                    {
                        "id": url_entry.id,
                        "short_code": url_entry.short_code,
                        "original_url": url_entry.original_url,
                        "title": url_entry.title,
                        "is_active": url_entry.is_active,
                        "user_id": url_entry.user_id_id if url_entry.user_id_id else None,
                        "short_url": f"{request.host_url}{url_entry.short_code}",
                        "created_at": url_entry.created_at.isoformat(),
                        "updated_at": url_entry.updated_at.isoformat() if url_entry.updated_at else None,
                    }
                ),
                201,
            )
        except IntegrityError:
            continue

    return jsonify({"error": "Failed to generate a unique short code. Please try again."}), 500


# ─── POST /shorten — Legacy shorten endpoint ─────────────────────────────────

@shortener_bp.route("/shorten", methods=["POST"])
def shorten_url():
    """Shorten a URL (legacy endpoint)."""
    data = request.get_json(silent=True)

    if not data or "url" not in data:
        return jsonify({"error": "Missing 'url' field in request body"}), 400

    original_url = data["url"]

    if not isinstance(original_url, str) or not original_url.strip():
        return jsonify({"error": "URL must be a non-empty string"}), 400

    original_url = original_url.strip()

    if not is_valid_url(original_url):
        return jsonify({"error": "Invalid URL. Must be a valid HTTP or HTTPS URL", "example": "https://example.com"}), 400

    for _ in range(5):
        short_code = generate_short_code()
        try:
            url_entry = ShortenedURL.create(
                original_url=original_url,
                short_code=short_code,
            )
            return (
                jsonify(
                    {
                        "short_code": url_entry.short_code,
                        "original_url": url_entry.original_url,
                        "short_url": f"{request.host_url}{url_entry.short_code}",
                        "created_at": url_entry.created_at.isoformat(),
                    }
                ),
                201,
            )
        except IntegrityError:
            continue

    return jsonify({"error": "Failed to generate a unique short code. Please try again."}), 500


# ─── GET /urls — List all URLs with filtering ────────────────────────────────

@shortener_bp.route("/urls", methods=["GET"])
def list_urls():
    """List all shortened URLs with optional filtering."""
    query = ShortenedURL.select().order_by(ShortenedURL.created_at.desc())

    user_id = request.args.get("user_id")
    if user_id:
        query = query.where(ShortenedURL.user_id == int(user_id))

    is_active = request.args.get("is_active")
    if is_active is not None:
        active_val = is_active.lower() in ("true", "1", "yes")
        query = query.where(ShortenedURL.is_active == active_val)

    return jsonify(
        [
            {
                "id": u.id,
                "short_code": u.short_code,
                "original_url": u.original_url,
                "title": u.title,
                "is_active": u.is_active,
                "user_id": u.user_id_id if u.user_id_id else None,
                "short_url": f"{request.host_url}{u.short_code}",
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "updated_at": u.updated_at.isoformat() if u.updated_at else None,
            }
            for u in query
        ]
    )


# ─── GET /urls/<id> — Get a single URL by ID ─────────────────────────────────

@shortener_bp.route("/urls/<int:url_id>", methods=["GET"])
def get_url(url_id: int):
    """Get a single URL by ID."""
    try:
        u = ShortenedURL.get_by_id(url_id)
        return jsonify(
            {
                "id": u.id,
                "short_code": u.short_code,
                "original_url": u.original_url,
                "title": u.title,
                "is_active": u.is_active,
                "user_id": u.user_id_id if u.user_id_id else None,
                "short_url": f"{request.host_url}{u.short_code}",
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "updated_at": u.updated_at.isoformat() if u.updated_at else None,
            }
        )
    except DoesNotExist:
        return jsonify({"error": "URL not found"}), 404


# ─── PUT /urls/<id> — Update a URL ───────────────────────────────────────────

@shortener_bp.route("/urls/<int:url_id>", methods=["PUT"])
def update_url(url_id: int):
    """Update an existing URL."""
    try:
        url_entry = ShortenedURL.get_by_id(url_id)
    except DoesNotExist:
        return jsonify({"error": "URL not found"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    if "title" in data:
        url_entry.title = data["title"]
    if "is_active" in data:
        url_entry.is_active = data["is_active"]
    if "original_url" in data:
        url_entry.original_url = data["original_url"]

    url_entry.updated_at = datetime.datetime.utcnow()
    url_entry.save()

    return jsonify(
        {
            "id": url_entry.id,
            "short_code": url_entry.short_code,
            "original_url": url_entry.original_url,
            "title": url_entry.title,
            "is_active": url_entry.is_active,
            "user_id": url_entry.user_id_id if url_entry.user_id_id else None,
            "short_url": f"{request.host_url}{url_entry.short_code}",
            "created_at": url_entry.created_at.isoformat() if url_entry.created_at else None,
            "updated_at": url_entry.updated_at.isoformat() if url_entry.updated_at else None,
        }
    )


# ─── DELETE /urls/<id> — Delete a URL ─────────────────────────────────────────

@shortener_bp.route("/urls/<int:url_id>", methods=["DELETE"])
def delete_url(url_id: int):
    """Delete a URL by ID."""
    try:
        url_entry = ShortenedURL.get_by_id(url_id)
    except DoesNotExist:
        return jsonify({"error": "URL not found"}), 404

    url_entry.delete_instance()
    return "", 204


# ─── GET /<short_code> — Redirect ────────────────────────────────────────────

@shortener_bp.route("/<string:short_code>", methods=["GET"])
def redirect_to_url(short_code: str):
    """Redirect a short code to the original URL."""
    if not short_code or not short_code.isalnum():
        return jsonify({"error": "Invalid short code format"}), 400

    try:
        url_entry = ShortenedURL.get(ShortenedURL.short_code == short_code)
        if not url_entry.is_active:
            return jsonify({"error": "This URL has been deactivated"}), 410
        return redirect(url_entry.original_url, code=302)
    except DoesNotExist:
        return jsonify({"error": "Short URL not found", "short_code": short_code}), 404
