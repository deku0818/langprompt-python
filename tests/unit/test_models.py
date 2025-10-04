"""Tests for data models."""

from datetime import datetime
from uuid import UUID, uuid4

import pytest

from langprompt.models import (
    PagedResponse,
    Project,
    Prompt,
    PromptVersion,
)


def test_project_model():
    """Test Project model."""
    project_id = uuid4()
    now = datetime.now()

    project = Project(
        id=project_id,
        name="test-project",
        description="Test project description",
        tags=["test", "demo"],
        metadata={"key": "value"},
        created_at=now,
        updated_at=now,
    )

    assert project.id == project_id
    assert project.name == "test-project"
    assert project.description == "Test project description"
    assert project.tags == ["test", "demo"]
    assert project.metadata == {"key": "value"}


def test_prompt_model():
    """Test Prompt model."""
    prompt_id = uuid4()
    project_id = uuid4()
    now = datetime.now()

    prompt = Prompt(
        id=prompt_id,
        name="greeting",
        description="Greeting prompt",
        project_id=project_id,
        type="chat",
        tags=["greeting"],
        created_at=now,
        updated_at=now,
    )

    assert prompt.id == prompt_id
    assert prompt.name == "greeting"
    assert prompt.project_id == project_id
    assert prompt.type == "chat"


def test_prompt_version_model():
    """Test PromptVersion model."""
    version_id = uuid4()
    prompt_id = uuid4()
    now = datetime.now()

    version = PromptVersion(
        id=version_id,
        prompt_id=prompt_id,
        version=1,
        prompt=[{"text": "Hello, world!"}],
        labels=["production"],
        metadata={"author": "test"},
        commit_message="Initial version",
        created_at=now,
        updated_at=now,
    )

    assert version.id == version_id
    assert version.prompt_id == prompt_id
    assert version.version == 1
    assert version.prompt == [{"text": "Hello, world!"}]
    assert version.labels == ["production"]
    assert version.commit_message == "Initial version"


def test_paged_response():
    """Test PagedResponse model."""
    projects = [
        Project(
            id=uuid4(),
            name=f"project-{i}",
            description=None,
            tags=[],
            metadata={},
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        for i in range(5)
    ]

    response = PagedResponse[Project](
        items=projects,
        total=25,
        limit=5,
        offset=0,
        has_next=True,
    )

    assert len(response.items) == 5
    assert response.total == 25
    assert response.limit == 5
    assert response.offset == 0
    assert response.has_next is True


def test_paged_response_last_page():
    """Test PagedResponse on last page."""
    response = PagedResponse[Project](
        items=[],
        total=25,
        limit=5,
        offset=20,
        has_next=False,
    )

    assert response.has_next is False
    assert response.offset == 20
