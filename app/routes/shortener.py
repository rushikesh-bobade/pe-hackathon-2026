from urllib.parse import urlparse

from flask import Blueprint, jsonify, redirect, request
from peewee import DoesNotExist, IntegrityError

from app.models.url import ShortenedURL, generate_short_code

shortener_bp = Blueprint("shortener", __name__)


def is_valid_url(url: str) -> bool:
    """Validate that the given string is a proper HTTP/HTTPS URL."""
    try:
        # Reject URLs with spaces (urlparse won't catch these)
        if " " in url:
            return False
        result = urlparse(url)
        return result.scheme in ("http", "https") and bool(result.netloc)
    except Exception:
        return False


@shortener_bp.route("/shorten", methods=["POST"])
def shorten_url():
    """
    Shorten a URL.

    Request body (JSON):
        { "url": "https://example.com" }

    Responses:
        201 - Successfully created
        400 - Missing or invalid URL
        500 - Internal server error
    """
    data = request.get_json(silent=True)

    if not data or "url" not in data:
        return jsonify({"error": "Missing 'url' field in request body"}), 400

    original_url = data["url"]

    if not isinstance(original_url, str) or not original_url.strip():
        return jsonify({"error": "URL must be a non-empty string"}), 400

    original_url = original_url.strip()

    if not is_valid_url(original_url):
        return (
            jsonify(
                {
                    "error": "Invalid URL. Must be a valid HTTP or HTTPS URL",
                    "example": "https://example.com",
                }
            ),
            400,
        )

    # Try up to 5 times to generate a unique short code
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
            # Short code collision — retry
            continue

    return jsonify({"error": "Failed to generate a unique short code. Please try again."}), 500


@shortener_bp.route("/<string:short_code>", methods=["GET"])
def redirect_to_url(short_code: str):
    """
    Redirect a short code to the original URL.

    Responses:
        302 - Redirect to original URL
        404 - Short code not found
    """
    if not short_code or not short_code.isalnum():
        return jsonify({"error": "Invalid short code format"}), 400

    try:
        url_entry = ShortenedURL.get(ShortenedURL.short_code == short_code)
        return redirect(url_entry.original_url, code=302)
    except DoesNotExist:
        return (
            jsonify(
                {
                    "error": "Short URL not found",
                    "short_code": short_code,
                }
            ),
            404,
        )


@shortener_bp.route("/urls", methods=["GET"])
def list_urls():
    """
    List all shortened URLs.

    Responses:
        200 - List of all shortened URLs
    """
    urls = ShortenedURL.select().order_by(ShortenedURL.created_at.desc())
    return jsonify(
        [
            {
                "short_code": u.short_code,
                "original_url": u.original_url,
                "short_url": f"{request.host_url}{u.short_code}",
                "created_at": u.created_at.isoformat(),
            }
            for u in urls
        ]
    )
