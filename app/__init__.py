from dotenv import load_dotenv
from flask import Flask, jsonify

from app.database import db, init_db
from app.routes import register_routes


def create_app(testing: bool = False):
    load_dotenv()

    app = Flask(__name__)
    app.config["TESTING"] = testing

    if not testing:
        # Production: wire up PostgreSQL and create tables
        init_db(app)

        from app import models  # noqa: F401
        from app.models.url import ShortenedURL

        with app.app_context():
            db.create_tables([ShortenedURL], safe=True)
    else:
        # Testing: the test fixture already called db.initialize()
        # with an in-memory SQLite. Do NOT register connect/close
        # hooks — the fixture manages the connection lifetime.
        from app import models  # noqa: F401

    register_routes(app)

    # ─── Health Check (Bronze Tier) ─────────────────────────────────────────
    @app.route("/health")
    def health():
        """Health check endpoint. Returns 200 OK when service is alive."""
        return jsonify(status="ok"), 200

    # ─── Global Error Handlers (Gold Tier) ──────────────────────────────────
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify(error="Bad Request", message=str(e.description)), 400

    @app.errorhandler(404)
    def not_found(e):
        return (
            jsonify(
                error="Not Found",
                message="The requested resource does not exist.",
            ),
            404,
        )

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify(error="Method Not Allowed", message=str(e.description)), 405

    @app.errorhandler(500)
    def internal_error(e):
        return (
            jsonify(
                error="Internal Server Error",
                message="An unexpected error occurred. Please try again later.",
            ),
            500,
        )

    return app
