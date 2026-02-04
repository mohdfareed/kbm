"""Response models for MCP tools."""

__all__ = [
    "DeleteResponse",
    "InfoResponse",
    "InsertResponse",
    "ListResponse",
    "QueryResponse",
    "QueryResult",
    "RecordSummary",
]

from datetime import datetime

from pydantic import BaseModel


class InfoResponse(BaseModel):
    engine: str
    records: int
    metadata: dict[str, str] = {}


class QueryResult(BaseModel):
    id: str
    content: str
    created_at: datetime
    score: float | None = None


class QueryResponse(BaseModel):
    results: list[QueryResult]
    query: str
    total: int


class InsertResponse(BaseModel):
    id: str
    message: str = "Inserted"


class DeleteResponse(BaseModel):
    id: str
    found: bool
    message: str = "Deleted"


class RecordSummary(BaseModel):
    id: str
    created_at: datetime
    content_type: str
    preview: str


class ListResponse(BaseModel):
    records: list[RecordSummary]
    total: int
    limit: int
    offset: int
