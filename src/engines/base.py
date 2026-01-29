"""Abstract engine interface."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydantic import BaseModel


class Operation(str, Enum):
    """Engine operation types."""

    QUERY = "query"
    INSERT = "insert"
    INSERT_FILE = "insert_file"
    DELETE = "delete"
    LIST = "list"


class Engine(ABC):
    """Abstract base class for storage engines."""

    @classmethod
    @abstractmethod
    def get_schemas(cls) -> dict[Operation, type["BaseModel"]]:
        """Return the Pydantic models for this engine's operations.

        Returns:
            Dict mapping Operation enum to their parameter models.
        """
        ...

    @abstractmethod
    async def query(self, query: str, params: "BaseModel") -> str:
        """Query the knowledge base.

        Args:
            query: The query string.
            params: Engine-specific query parameters.

        Returns:
            Query results as a string.
        """
        ...

    @abstractmethod
    async def insert(self, content: str, params: "BaseModel") -> str:
        """Insert text content into the knowledge base.

        Args:
            content: The text content to insert.
            params: Engine-specific insert parameters.

        Returns:
            Record ID or confirmation message.
        """
        ...

    @abstractmethod
    async def insert_file(self, file_path: str, params: "BaseModel") -> str:
        """Insert a file into the knowledge base.

        Args:
            file_path: Path to the file to insert.
            params: Engine-specific insert parameters.

        Returns:
            Record ID or confirmation message.
        """
        ...

    @abstractmethod
    async def delete(self, record_id: str, params: "BaseModel") -> str:
        """Delete a record from the knowledge base.

        Args:
            record_id: The ID of the record to delete.
            params: Engine-specific delete parameters.

        Returns:
            Confirmation message.
        """
        ...

    @abstractmethod
    async def list(self, params: "BaseModel") -> str:
        """List records in the knowledge base.

        Args:
            params: Engine-specific list parameters.

        Returns:
            List of records as formatted string.
        """
        ...

    @abstractmethod
    async def info(self) -> str:
        """Get information about the knowledge base.

        Returns:
            Memory metadata as formatted string.
        """
        ...
