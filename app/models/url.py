import datetime
import random
import string

from peewee import (
    AutoField,
    BooleanField,
    CharField,
    DateTimeField,
    ForeignKeyField,
    TextField,
)

from app.database import BaseModel
from app.models.user import User


def generate_short_code(length: int = 6) -> str:
    """Generate a random alphanumeric short code."""
    characters = string.ascii_letters + string.digits
    return "".join(random.choices(characters, k=length))


class ShortenedURL(BaseModel):
    """URL model matching the seed CSV schema."""

    id = AutoField()
    user_id = ForeignKeyField(User, backref="urls", column_name="user_id", null=True)
    short_code = CharField(max_length=16, unique=True)
    original_url = CharField(max_length=2048)
    title = CharField(max_length=512, null=True, default="")
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    updated_at = DateTimeField(default=datetime.datetime.utcnow)

    class Meta:
        table_name = "urls"
