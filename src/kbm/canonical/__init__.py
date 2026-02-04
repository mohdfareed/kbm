"""Canonical data store - SQLite persistence for all records.

Provides durable, portable storage that engines can rebuild their indexes from.
Uses async SQLAlchemy 2.0 with aiosqlite for true async database operations.
"""

__all__ = [
    "Attachment",
    "CanonicalStore",
    "Record",
    "with_canonical",
]

from kbm.canonical.models import Attachment, Record
from kbm.canonical.store import CanonicalStore
from kbm.canonical.wrapper import with_canonical
