"""pytest configuration and shared fixtures."""
import os

import pytest

# Force test environment before any app imports
os.environ.setdefault("DATABASE_NAME", "test_db")
os.environ.setdefault("DATABASE_HOST", "localhost")
os.environ.setdefault("DATABASE_PORT", "5432")
os.environ.setdefault("DATABASE_USER", "postgres")
os.environ.setdefault("DATABASE_PASSWORD", "postgres")
