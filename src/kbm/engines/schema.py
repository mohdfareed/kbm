"""MCP tool surface schemas: descriptions and annotations for engine operations."""

__all__: list[str] = []  # no public API - consumed only by base_engine

from datetime import datetime
from typing import Annotated

from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field

# MARK: Tool descriptions
# The user-facing text that describes each tool's purpose and behavior.

INFO_DESCRIPTION = (
    "Get knowledge base metadata.\n\n"
    "Returns engine type, record count, and configuration details."
)

QUERY_DESCRIPTION = "Search the knowledge base."

INSERT_DESCRIPTION = "Add text content to the knowledge base."

INSERT_FILE_DESCRIPTION = (
    "Add a file to the knowledge base.\n\n"
    "Supports PDF, images, and other document formats\n"
    "depending on engine."
)

DELETE_DESCRIPTION = "Remove a record from the knowledge base."

LIST_RECORDS_DESCRIPTION = "List records in the knowledge base."

# MARK: Tool annotations
#   readOnlyHint    → clients may skip confirmation
#   destructiveHint → clients may warn before executing
#   idempotentHint  → clients may retry safely

INFO_ANNOTATIONS = ToolAnnotations(
    readOnlyHint=True,
    openWorldHint=False,
)
QUERY_ANNOTATIONS = ToolAnnotations(
    readOnlyHint=True,
    openWorldHint=False,
)
INSERT_ANNOTATIONS = ToolAnnotations(
    destructiveHint=False,
    idempotentHint=False,
)
INSERT_FILE_ANNOTATIONS = ToolAnnotations(
    destructiveHint=False,
    idempotentHint=False,
)
DELETE_ANNOTATIONS = ToolAnnotations(
    destructiveHint=True,
)
LIST_RECORDS_ANNOTATIONS = ToolAnnotations(
    readOnlyHint=True,
    openWorldHint=False,
    idempotentHint=True,
)

# MARK: Parameter types
# JSON-schema descriptions that models receive

QueryText = Annotated[
    str,
    Field(description="Search text to find matching records."),
]
TopK = Annotated[
    int,
    Field(description="Maximum number of results to return."),
]
Content = Annotated[
    str,
    Field(description="Text content to store."),
]
FilePath = Annotated[
    str,
    Field(description="Local path to file, OR filename when content is provided."),
]
FileContent = Annotated[
    str | None,
    Field(
        description="Base64-encoded file data. If provided, file_path is the filename."
    ),
]
RecordId = Annotated[
    str,
    Field(description="ID of the record to delete."),
]
Limit = Annotated[
    int,
    Field(description="Maximum number of records to return."),
]
Offset = Annotated[
    int,
    Field(description="Number of records to skip for pagination."),
]

# MARK: Return types


class InfoResponse(BaseModel):
    engine: str = Field(description="Storage engine type.")
    records: int = Field(description="Total number of records stored.")
    metadata: dict[str, str] = Field(
        default={}, description="Engine-specific configuration details."
    )
    instructions: str = Field(
        default="",
        description="How to effectively use this knowledge base. "
        "Describes the engine's capabilities and best practices.",
    )


class QueryResult(BaseModel):
    content: str = Field(description="Matching record content.")
    # Optional query result metadata
    id: str | None = Field(
        default=None, description="Unique record identifier, if available."
    )
    created_at: datetime | None = Field(
        default=None, description="When the record was created, if available."
    )
    score: float | None = Field(
        default=None, description="Relevance score, if available."
    )


class QueryResponse(BaseModel):
    results: list[QueryResult] = Field(
        description="Matching records, ranked by relevance."
    )
    query: str = Field(description="The original search query.")
    total: int = Field(description="Number of results returned.")


class InsertResponse(BaseModel):
    id: str = Field(description="ID of the newly created record.")
    message: str = Field(default="Inserted", description="Status message.")


class DeleteResponse(BaseModel):
    id: str = Field(description="ID of the targeted record.")
    found: bool = Field(description="Whether the record existed.")
    message: str = Field(default="Deleted", description="Status message.")


class RecordSummary(BaseModel):
    id: str = Field(description="Unique record identifier.")
    created_at: datetime = Field(description="When the record was created.")
    content_type: str = Field(description="Type of stored content (text, file).")
    preview: str = Field(description="Truncated content preview.")


class ListResponse(BaseModel):
    records: list[RecordSummary] = Field(description="Page of record summaries.")
    total: int = Field(description="Total records in the knowledge base.")
    limit: int = Field(description="Maximum records per page.")
    offset: int = Field(description="Number of records skipped.")
