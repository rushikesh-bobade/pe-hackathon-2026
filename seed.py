"""
seed.py — Idempotent CSV Data Seeder for the MLH PE Hackathon.

Loads users.csv, urls.csv, and events.csv into the database.
Safe to run multiple times — checks if data already exists before inserting.

Usage:
    uv run seed.py
"""

import csv
import logging
import os
import sys

from dotenv import load_dotenv
from peewee import chunked

# ─── Setup logging ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SEED] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("seed")

# ─── Bootstrap the app so the DB proxy is initialized ───────────────────────
load_dotenv()

from app.database import db, init_db  # noqa: E402
from app import create_app  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.url import ShortenedURL  # noqa: E402
from app.models.event import Event  # noqa: E402

# Determine CSV directory (same as this script's location)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def csv_path(filename: str) -> str:
    """Return absolute path to a CSV file in the project root."""
    path = os.path.join(BASE_DIR, filename)
    if not os.path.exists(path):
        log.error(f"CSV file not found: {path}")
        sys.exit(1)
    return path


def is_seeded(model, expected_csv: str) -> bool:
    """Check if a table already has data (idempotency check)."""
    count = model.select().count()
    if count > 0:
        log.info(f"  ✓ {model.__name__} already has {count} rows — skipping.")
        return True
    return False


def parse_bool(value: str) -> bool:
    """Parse a boolean string from CSV."""
    return value.strip().lower() in ("true", "1", "yes", "t")


def seed_users():
    """Seed users from users.csv."""
    log.info("─── Seeding Users ───")
    if is_seeded(User, "users.csv"):
        return

    filepath = csv_path("users.csv")
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            rows.append({
                "id": int(row["id"]),
                "username": row["username"],
                "email": row["email"],
                "created_at": row["created_at"],
            })

    with db.atomic():
        for batch in chunked(rows, 100):
            User.insert_many(batch).execute()

    log.info(f"  ✓ Inserted {len(rows)} users.")


def seed_urls():
    """Seed URLs from urls.csv."""
    log.info("─── Seeding URLs ───")
    if is_seeded(ShortenedURL, "urls.csv"):
        return

    filepath = csv_path("urls.csv")
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            rows.append({
                "id": int(row["id"]),
                "user_id": int(row["user_id"]),
                "short_code": row["short_code"],
                "original_url": row["original_url"],
                "title": row.get("title", ""),
                "is_active": parse_bool(row.get("is_active", "true")),
                "created_at": row["created_at"],
                "updated_at": row.get("updated_at", row["created_at"]),
            })

    with db.atomic():
        for batch in chunked(rows, 100):
            ShortenedURL.insert_many(batch).execute()

    log.info(f"  ✓ Inserted {len(rows)} URLs.")


def seed_events():
    """Seed events from events.csv."""
    log.info("─── Seeding Events ───")
    if is_seeded(Event, "events.csv"):
        return

    filepath = csv_path("events.csv")
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            rows.append({
                "id": int(row["id"]),
                "url_id": int(row["url_id"]),
                "user_id": int(row["user_id"]),
                "event_type": row["event_type"],
                "timestamp": row["timestamp"],
                "details": row.get("details", ""),
            })

    with db.atomic():
        for batch in chunked(rows, 100):
            Event.insert_many(batch).execute()

    log.info(f"  ✓ Inserted {len(rows)} events.")


def main():
    log.info("=" * 50)
    log.info("  MLH PE Hackathon — Database Seeder")
    log.info("=" * 50)

    # Create the Flask app to initialize DB connection
    app = create_app()

    with app.app_context():
        # Ensure tables exist
        db.create_tables([User, ShortenedURL, Event], safe=True)
        log.info("Tables created/verified.")

        # Seed in FK dependency order: Users → URLs → Events
        seed_users()
        seed_urls()
        seed_events()

    log.info("=" * 50)
    log.info("  Seeding complete! ✅")
    log.info("=" * 50)


if __name__ == "__main__":
    main()
