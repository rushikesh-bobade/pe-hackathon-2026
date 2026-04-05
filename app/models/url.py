import datetime
import random
import string

from peewee import CharField, DateTimeField

from app.database import BaseModel


def generate_short_code(length: int = 6) -> str:
    """Generate a random alphanumeric short code."""
    characters = string.ascii_letters + string.digits
    return "".join(random.choices(characters, k=length))


class ShortenedURL(BaseModel):
    """Model for storing shortened URLs."""

    original_url = CharField(max_length=2048)
    short_code = CharField(max_length=16, unique=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)

    class Meta:
        table_name = "shortened_urls"
