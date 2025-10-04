"""Prompt version data model."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class PromptVersion(BaseModel):
    """Prompt version model.

    Versions follow Git-like immutability:
    - Immutable fields: prompt, version, commit_message, created_at
    - Mutable fields: labels, metadata, updated_at

    Attributes:
        id: Version unique identifier
        prompt_id: Parent prompt ID
        project_id: Project ID (optional)
        version: Version number (immutable, auto-incremented)
        prompt: Prompt content as list (immutable)
        type: Prompt type (inherited from parent prompt)
        labels: Version labels (mutable, e.g., "production", "staging")
        metadata: Additional metadata (mutable, can be null)
        commit_message: Commit message describing changes (immutable)
        created_at: Creation timestamp (immutable)
        updated_at: Last update timestamp
        created_by: Creator user ID (optional)
    """

    id: UUID
    prompt_id: UUID
    project_id: UUID | None = None
    version: int = Field(ge=1)
    prompt: list[Any]
    type: str | None = None
    labels: list[str] | None = None
    metadata: dict[str, Any] | None = Field(default=None)
    commit_message: str | None = None
    created_at: datetime
    updated_at: datetime
    created_by: UUID | None = None

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
        }


class PromptContent(BaseModel):
    """Simplified prompt content response.

    Used when only content is needed without full version metadata.
    """

    content: dict[str, Any]
    version: int = Field(ge=1)
    labels: list[str] = Field(default_factory=list)
