"""Project data model."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class Project(BaseModel):
    """Project model.

    Attributes:
        id: Project unique identifier
        name: Project name
        description: Project description
        tags: Project tags for categorization
        metadata: Additional metadata
        created_at: Creation timestamp
        updated_at: Last update timestamp
        user_role: User's role in the project (owner, admin, member, viewer)
    """

    id: UUID
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    tags: list[str] | None = Field(default=None)
    metadata: dict[str, Any] | None = Field(default=None)
    created_at: datetime
    updated_at: datetime | None = None
    user_role: str | None = None

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
        }


class ProjectListResponse(BaseModel):
    """Project list response with pagination.

    Attributes:
        projects: List of projects
        total: Total number of projects
        limit: Number of items per page
        offset: Number of items to skip
    """

    projects: list[Project]
    total: int
    limit: int
    offset: int
