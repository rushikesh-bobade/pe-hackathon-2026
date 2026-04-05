import datetime

from peewee import (
    AutoField,
    BooleanField,
    CharField,
    DateTimeField,
    ForeignKeyField,
    TextField,
)

from app.database import BaseModel


class User(BaseModel):
    """User model matching the seed CSV schema."""

    id = AutoField()
    username = CharField(max_length=255, unique=True)
    email = CharField(max_length=255, unique=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)

    class Meta:
        table_name = "users"
