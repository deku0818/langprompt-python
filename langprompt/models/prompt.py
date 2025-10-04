"""Prompt data model."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class Prompt(BaseModel):
    """Prompt model.

    Attributes:
        id: Prompt unique identifier
        name: Prompt name (supports categorization like "category/prompt_name")
        description: Prompt description
        project_id: Parent project ID
        type: Prompt type
        tags: Prompt tags for categorization
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: UUID
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    project_id: UUID
    type: str
    tags: list[str] | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
        }
