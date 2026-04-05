import datetime

from peewee import (
    AutoField,
    CharField,
    DateTimeField,
    ForeignKeyField,
    TextField,
)

from app.database import BaseModel
from app.models.user import User
from app.models.url import ShortenedURL


class Event(BaseModel):
    """Event/analytics model matching the seed CSV schema."""

    id = AutoField()
    url_id = ForeignKeyField(ShortenedURL, backref="events", column_name="url_id")
    user_id = ForeignKeyField(User, backref="events", column_name="user_id")
    event_type = CharField(max_length=50)
    timestamp = DateTimeField(default=datetime.datetime.utcnow)
    details = TextField(default="")

    class Meta:
        table_name = "events"
