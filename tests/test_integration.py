"""
Integration tests for the URL Shortener API.
Tests the full request/response cycle using Flask's test client.
Uses an in-memory SQLite database — no real PostgreSQL needed.
"""

import pytest
from peewee import SqliteDatabase

from app import create_app
from app.database import db
from app.models.user import User
from app.models.url import ShortenedURL
from app.models.event import Event

# ─── Fixtures ────────────────────────────────────────────────────────────────

TEST_DB = SqliteDatabase(":memory:")
MODELS = [User, ShortenedURL, Event]


@pytest.fixture()
def app():
    """Create a Flask test app wired to an in-memory SQLite database."""
    db.initialize(TEST_DB)
    TEST_DB.connect(reuse_if_open=True)
    TEST_DB.create_tables(MODELS, safe=True)

    flask_app = create_app(testing=True)

    yield flask_app

    TEST_DB.drop_tables(MODELS)
    TEST_DB.close()


@pytest.fixture()
def client(app):
    """Return a Flask test client."""
    return app.test_client()


# ─── /health ─────────────────────────────────────────────────────────────────

class TestHealthEndpoint:
    """Integration tests for the /health endpoint."""

    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_json(self, client):
        response = client.get("/health")
        data = response.get_json()
        assert data is not None
        assert data["status"] == "ok"

    def test_health_content_type(self, client):
        response = client.get("/health")
        assert "application/json" in response.content_type


# ─── POST /shorten ───────────────────────────────────────────────────────────

class TestShortenEndpoint:
    """Integration tests for the POST /shorten endpoint."""

    def test_shorten_valid_url_returns_201(self, client):
        response = client.post(
            "/shorten",
            json={"url": "https://example.com"},
        )
        assert response.status_code == 201

    def test_shorten_returns_short_code(self, client):
        response = client.post(
            "/shorten",
            json={"url": "https://example.com"},
        )
        data = response.get_json()
        assert "short_code" in data
        assert len(data["short_code"]) == 6

    def test_shorten_returns_original_url(self, client):
        response = client.post(
            "/shorten",
            json={"url": "https://example.com"},
        )
        data = response.get_json()
        assert data["original_url"] == "https://example.com"

    def test_shorten_saves_to_db(self, client):
        client.post("/shorten", json={"url": "https://stored.com"})
        count = ShortenedURL.select().where(
            ShortenedURL.original_url == "https://stored.com"
        ).count()
        assert count == 1

    def test_shorten_missing_url_field_returns_400(self, client):
        response = client.post("/shorten", json={"not_url": "value"})
        assert response.status_code == 400

    def test_shorten_empty_body_returns_400(self, client):
        response = client.post(
            "/shorten",
            data="",
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_shorten_invalid_url_returns_400(self, client):
        response = client.post(
            "/shorten",
            json={"url": "not-a-real-url"},
        )
        assert response.status_code == 400

    def test_shorten_ftp_url_returns_400(self, client):
        response = client.post(
            "/shorten",
            json={"url": "ftp://example.com"},
        )
        assert response.status_code == 400

    def test_shorten_empty_url_string_returns_400(self, client):
        response = client.post("/shorten", json={"url": ""})
        assert response.status_code == 400

    def test_shorten_non_string_url_returns_400(self, client):
        response = client.post("/shorten", json={"url": 12345})
        assert response.status_code == 400

    def test_shorten_http_url_is_valid(self, client):
        response = client.post(
            "/shorten",
            json={"url": "http://example.com"},
        )
        assert response.status_code == 201

    def test_shorten_returns_short_url_field(self, client):
        response = client.post(
            "/shorten",
            json={"url": "https://example.com"},
        )
        data = response.get_json()
        assert "short_url" in data

    def test_shorten_multiple_urls_get_different_codes(self, client):
        r1 = client.post("/shorten", json={"url": "https://one.com"})
        r2 = client.post("/shorten", json={"url": "https://two.com"})
        assert r1.get_json()["short_code"] != r2.get_json()["short_code"]

    def test_shorten_error_response_is_json(self, client):
        response = client.post("/shorten", json={"url": "bad-url"})
        assert response.get_json() is not None


# ─── GET /<short_code> ───────────────────────────────────────────────────────

class TestRedirectEndpoint:
    """Integration tests for the GET /<short_code> redirect endpoint."""

    def test_redirect_valid_code_returns_302(self, client):
        shorten_resp = client.post(
            "/shorten",
            json={"url": "https://redirect.com"},
        )
        code = shorten_resp.get_json()["short_code"]
        response = client.get(f"/{code}")
        assert response.status_code == 302

    def test_redirect_goes_to_original_url(self, client):
        shorten_resp = client.post(
            "/shorten",
            json={"url": "https://original-destination.com"},
        )
        code = shorten_resp.get_json()["short_code"]
        response = client.get(f"/{code}")
        assert response.location == "https://original-destination.com"

    def test_redirect_unknown_code_returns_404(self, client):
        response = client.get("/nonexistent")
        assert response.status_code == 404

    def test_redirect_unknown_code_returns_json(self, client):
        response = client.get("/nonexistent")
        data = response.get_json()
        assert data is not None
        assert "error" in data

    def test_redirect_invalid_code_with_special_chars_returns_400(self, client):
        response = client.get("/bad!code")
        assert response.status_code == 400


# ─── GET /urls ───────────────────────────────────────────────────────────────

class TestListUrlsEndpoint:
    """Integration tests for the GET /urls endpoint."""

    def test_list_urls_returns_200(self, client):
        response = client.get("/urls")
        assert response.status_code == 200

    def test_list_urls_returns_json_list(self, client):
        response = client.get("/urls")
        data = response.get_json()
        assert isinstance(data, list)

    def test_list_urls_shows_created_entry(self, client):
        client.post("/shorten", json={"url": "https://listed.com"})
        response = client.get("/urls")
        data = response.get_json()
        urls = [item["original_url"] for item in data]
        assert "https://listed.com" in urls

    def test_list_urls_empty_when_no_entries(self, client):
        response = client.get("/urls")
        assert response.get_json() == []


# ─── GET /users ──────────────────────────────────────────────────────────────

class TestUsersEndpoint:
    """Integration tests for the /users endpoint."""

    def test_list_users_returns_200(self, client):
        response = client.get("/users")
        assert response.status_code == 200

    def test_list_users_returns_json_list(self, client):
        response = client.get("/users")
        data = response.get_json()
        assert isinstance(data, list)

    def test_get_user_not_found(self, client):
        response = client.get("/users/99999")
        assert response.status_code == 404

    def test_create_user(self, client):
        response = client.post(
            "/users",
            json={"username": "newuser", "email": "new@test.com"},
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["username"] == "newuser"
        assert data["email"] == "new@test.com"
        assert "id" in data

    def test_create_user_missing_fields(self, client):
        response = client.post("/users", json={"username": "only_name"})
        assert response.status_code == 400

    def test_create_user_empty_body(self, client):
        response = client.post(
            "/users", data="", content_type="application/json"
        )
        assert response.status_code == 400

    def test_create_user_duplicate(self, client):
        client.post(
            "/users",
            json={"username": "dup_user", "email": "dup@test.com"},
        )
        response = client.post(
            "/users",
            json={"username": "dup_user", "email": "dup2@test.com"},
        )
        assert response.status_code == 409

    def test_get_user_by_id(self, client):
        create = client.post(
            "/users",
            json={"username": "findme", "email": "find@test.com"},
        )
        user_id = create.get_json()["id"]
        response = client.get(f"/users/{user_id}")
        assert response.status_code == 200
        assert response.get_json()["username"] == "findme"

    def test_update_user(self, client):
        create = client.post(
            "/users",
            json={"username": "original", "email": "orig@test.com"},
        )
        user_id = create.get_json()["id"]
        response = client.put(
            f"/users/{user_id}",
            json={"username": "updated"},
        )
        assert response.status_code == 200
        assert response.get_json()["username"] == "updated"

    def test_update_user_not_found(self, client):
        response = client.put(
            "/users/99999",
            json={"username": "nope"},
        )
        assert response.status_code == 404

    def test_update_user_empty_body(self, client):
        create = client.post(
            "/users",
            json={"username": "emptyupd", "email": "emptyupd@test.com"},
        )
        user_id = create.get_json()["id"]
        response = client.put(
            f"/users/{user_id}",
            data="",
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_delete_user(self, client):
        create = client.post(
            "/users",
            json={"username": "deleteme", "email": "del@test.com"},
        )
        user_id = create.get_json()["id"]
        response = client.delete(f"/users/{user_id}")
        assert response.status_code == 204
        # Confirm deleted
        get_resp = client.get(f"/users/{user_id}")
        assert get_resp.status_code == 404

    def test_delete_user_not_found(self, client):
        response = client.delete("/users/99999")
        assert response.status_code == 404

    def test_list_users_pagination(self, client):
        for i in range(5):
            client.post(
                "/users",
                json={"username": f"page_user_{i}", "email": f"p{i}@test.com"},
            )
        response = client.get("/users?page=1&per_page=2")
        data = response.get_json()
        assert len(data) == 2


# ─── /events ─────────────────────────────────────────────────────────────────

class TestEventsEndpoint:
    """Integration tests for the /events endpoint."""

    def test_list_events_returns_200(self, client):
        response = client.get("/events")
        assert response.status_code == 200

    def test_list_events_returns_json_list(self, client):
        response = client.get("/events")
        data = response.get_json()
        assert isinstance(data, list)

    def test_list_events_empty(self, client):
        response = client.get("/events")
        assert response.get_json() == []

    def test_get_event_not_found(self, client):
        response = client.get("/events/99999")
        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data

    def test_list_events_filter_by_url_id(self, client):
        response = client.get("/events?url_id=1")
        assert response.status_code == 200

    def test_list_events_filter_by_user_id(self, client):
        response = client.get("/events?user_id=1")
        assert response.status_code == 200


# ─── Global Error Handlers (Gold Tier) ───────────────────────────────────────

class TestErrorHandlers:
    """Tests for global JSON error handlers."""

    def test_404_returns_json(self, client):
        response = client.get("/this/route/does/not/exist")
        data = response.get_json()
        assert data is not None
        assert "error" in data

    def test_404_status_code(self, client):
        response = client.get("/this/route/does/not/exist")
        assert response.status_code == 404

    def test_405_returns_json(self, client):
        response = client.post("/health")
        assert response.status_code == 405
        data = response.get_json()
        assert data is not None

