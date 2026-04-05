from flask import Blueprint, jsonify, request
from peewee import DoesNotExist

from app.models.event import Event

events_bp = Blueprint("events", __name__)


@events_bp.route("/events", methods=["GET"])
def list_events():
    """List all events, optionally filtered by url_id or user_id."""
    query = Event.select().order_by(Event.timestamp.desc())

    url_id = request.args.get("url_id")
    if url_id:
        query = query.where(Event.url_id == int(url_id))

    user_id = request.args.get("user_id")
    if user_id:
        query = query.where(Event.user_id == int(user_id))

    return jsonify(
        [
            {
                "id": e.id,
                "url_id": e.url_id_id,
                "user_id": e.user_id_id,
                "event_type": e.event_type,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                "details": e.details,
            }
            for e in query.limit(100)
        ]
    )


@events_bp.route("/events/<int:event_id>", methods=["GET"])
def get_event(event_id: int):
    """Get a single event by ID."""
    try:
        e = Event.get_by_id(event_id)
        return jsonify(
            {
                "id": e.id,
                "url_id": e.url_id_id,
                "user_id": e.user_id_id,
                "event_type": e.event_type,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                "details": e.details,
            }
        )
    except DoesNotExist:
        return jsonify({"error": "Event not found"}), 404
