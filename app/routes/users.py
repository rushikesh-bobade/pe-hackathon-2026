from flask import Blueprint, jsonify, request
from peewee import DoesNotExist

from app.models.user import User

users_bp = Blueprint("users", __name__)


@users_bp.route("/users", methods=["GET"])
def list_users():
    """List all users."""
    users = User.select().order_by(User.created_at.desc())
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
