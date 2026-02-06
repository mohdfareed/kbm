"""Canonical data store - SQLite persistence for all records.

Provides durable, portable storage that engines can rebuild their indexes from.
Uses async SQLAlchemy 2.0 with aiosqlite for true async database operations.
"""

__all__ = [
    "Attachment",
    "CanonicalStore",
    "Record",
]

from kbm.store.canonical import CanonicalStore
from kbm.store.models import Attachment, Record
