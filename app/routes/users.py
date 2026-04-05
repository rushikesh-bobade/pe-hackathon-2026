import csv
import io
import os

from flask import Blueprint, jsonify, request
from peewee import DoesNotExist, IntegrityError

from app.models.user import User

users_bp = Blueprint("users", __name__)


@users_bp.route("/users", methods=["GET"])
def list_users():
    """List all users with pagination support."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    total = User.select().count()
    users = (
        User.select()
        .order_by(User.id)
        .paginate(page, per_page)
    )

    return jsonify(
        [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ]
    )


@users_bp.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id: int):
    """Get a single user by ID."""
    try:
        u = User.get_by_id(user_id)
        return jsonify(
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
        )
    except DoesNotExist:
        return jsonify({"error": "User not found"}), 404


@users_bp.route("/users", methods=["POST"])
def create_user():
    """Create a new user."""
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Request body is required"}), 400

    username = data.get("username")
    email = data.get("email")

    if not username or not email:
        return jsonify({"error": "Both 'username' and 'email' are required"}), 400

    try:
        user = User.create(username=username, email=email)
        return (
            jsonify(
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                }
            ),
            201,
        )
    except IntegrityError:
        return jsonify({"error": "Username or email already exists"}), 409


@users_bp.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id: int):
    """Update an existing user."""
    try:
        user = User.get_by_id(user_id)
    except DoesNotExist:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    if "username" in data:
        user.username = data["username"]
    if "email" in data:
        user.email = data["email"]

    try:
        user.save()
        return jsonify(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            }
        )
    except IntegrityError:
        return jsonify({"error": "Username or email already exists"}), 409


@users_bp.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id: int):
    """Delete a user by ID."""
    try:
        user = User.get_by_id(user_id)
    except DoesNotExist:
        return jsonify({"error": "User not found"}), 404

    user.delete_instance()
    return "", 204


@users_bp.route("/users/bulk", methods=["POST"])
def bulk_load_users():
    """Bulk load users from the users.csv file."""
    from peewee import chunked

    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "users.csv")

    if not os.path.exists(csv_path):
        return jsonify({"error": "users.csv not found"}), 404

    # Check if already loaded
    existing = User.select().count()
    if existing > 0:
        return jsonify({"message": f"Users already loaded ({existing} records)", "count": existing}), 200

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            rows.append(
                {
                    "id": int(row["id"]),
                    "username": row["username"],
                    "email": row["email"],
                    "created_at": row["created_at"],
                }
            )

    from app.database import db

    with db.atomic():
        for batch in chunked(rows, 100):
            User.insert_many(batch).execute()

    return jsonify({"message": f"Loaded {len(rows)} users", "count": len(rows)}), 201
