import os

from peewee import DatabaseProxy, Model, PostgresqlDatabase, SqliteDatabase

db = DatabaseProxy()


class BaseModel(Model):
    class Meta:
        database = db


def init_db(app):
    """Initialize the database connection.

    Uses SQLite for local development (DATABASE_TYPE=sqlite),
    PostgreSQL for production and CI environments.
    """
    db_type = os.environ.get("DATABASE_TYPE", "postgres")

    if db_type == "sqlite":
        database = SqliteDatabase(
            os.environ.get("DATABASE_NAME", "hackathon.db"),
        )
    else:
        database = PostgresqlDatabase(
            os.environ.get("DATABASE_NAME", "hackathon_db"),
            host=os.environ.get("DATABASE_HOST", "localhost"),
            port=int(os.environ.get("DATABASE_PORT", 5432)),
            user=os.environ.get("DATABASE_USER", "postgres"),
            password=os.environ.get("DATABASE_PASSWORD", "postgres"),
        )

    db.initialize(database)

    @app.before_request
    def _db_connect():
        db.connect(reuse_if_open=True)

    @app.teardown_appcontext
    def _db_close(exc):
        if not db.is_closed():
            db.close()
