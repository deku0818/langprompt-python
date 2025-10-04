"""Common data models."""

from __future__ import annotations

from typing import Generic, TypeVar
from pydantic import BaseModel, Field


T = TypeVar("T")


class PagedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper.

    Attributes:
        items: List of items in current response
        total: Total number of items across all responses
        limit: Maximum number of items per request
        offset: Number of items skipped
        has_next: Whether there are more items
    """

    items: list[T]
    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)
    has_next: bool
