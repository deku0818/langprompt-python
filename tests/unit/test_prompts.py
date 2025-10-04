"""Tests for prompts resource."""

from datetime import datetime
from uuid import uuid4

import pytest
import respx
from httpx import Response

from langprompt.exceptions import NotFoundError, ValidationError
from langprompt.models import PagedResponse, Prompt, PromptVersion


@pytest.fixture
def project_id():
    """Test project ID."""
    return "550e8400-e29b-41d4-a716-446655440000"


@pytest.fixture
def prompt_id():
    """Test prompt ID."""
    return "660e8400-e29b-41d4-a716-446655440001"


@pytest.fixture
def version_id():
    """Test version ID."""
    return "770e8400-e29b-41d4-a716-446655440002"


@pytest.fixture
def prompt_data(prompt_id, project_id):
    """Sample prompt data."""
    return {
        "id": prompt_id,
        "name": "greeting",
        "description": "Greeting prompt",
        "project_id": project_id,
        "type": "chat",
        "tags": ["greeting"],
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def version_data(version_id, prompt_id):
    """Sample version data without type (to test type inheritance)."""
    return {
        "id": version_id,
        "prompt_id": prompt_id,
        "version": 1,
        "prompt": [{"text": "Hello, world!"}],
        "labels": ["production"],
        "metadata": {"author": "test"},
        "commit_message": "Initial version",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def version_data_with_type(version_id, prompt_id):
    """Sample version data with type."""
    return {
        "id": version_id,
        "prompt_id": prompt_id,
        "version": 1,
        "prompt": [{"text": "Hello, world!"}],
        "type": "chat",
        "labels": ["production"],
        "metadata": {"author": "test"},
        "commit_message": "Initial version",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }


# Synchronous tests


@respx.mock
def test_list_prompts(client, project_id, prompt_data):
    """Test listing all prompts."""
    respx.get(
        f"https://api.test.langprompt.com/api/v1/projects/{project_id}/prompts",
        params={"limit": "20", "offset": "0"},
    ).mock(
        return_value=Response(
            200,
            json={
                "prompts": [prompt_data],
                "total": 1,
                "limit": 20,
                "offset": 0,
            },
        )
    )

    result = client.prompts.list()

    assert isinstance(result, PagedResponse)
    assert len(result.items) == 1
    assert result.items[0].name == "greeting"
    assert result.total == 1
    assert result.limit == 20
    assert result.offset == 0




@respx.mock
def test_get_prompt_by_label(client, project_id, prompt_id, prompt_data, version_data):
    """Test getting prompt version by label using query parameter."""
    # Mock prompt name resolution
    respx.get(
        f"https://api.test.langprompt.com/api/v1/projects/{project_id}/prompts",
        params={"name": "greeting"},
    ).mock(return_value=Response(200, json=prompt_data))

    # Mock version retrieval by label (query parameter)
    respx.get(
        f"https://api.test.langprompt.com/api/v1/projects/{project_id}/prompts/{prompt_id}/versions",
        params={"label": "production"},
    ).mock(return_value=Response(200, json=version_data))

    result = client.prompts.get(prompt_name="greeting", label="production")

    assert isinstance(result, PromptVersion)
    assert result.version == 1
    assert result.labels == ["production"]
    assert result.prompt == [{"text": "Hello, world!"}]
    assert result.type == "chat"  # Type inherited from prompt


@respx.mock
def test_get_prompt_by_version(client, project_id, prompt_id, prompt_data, version_data):
    """Test getting prompt version by version number using query parameter."""
    # Mock prompt name resolution
    respx.get(
        f"https://api.test.langprompt.com/api/v1/projects/{project_id}/prompts",
        params={"name": "greeting"},
    ).mock(return_value=Response(200, json=prompt_data))

    # Mock version retrieval by version number (query parameter)
    respx.get(
        f"https://api.test.langprompt.com/api/v1/projects/{project_id}/prompts/{prompt_id}/versions",
        params={"version": "1"},
    ).mock(return_value=Response(200, json=version_data))

    result = client.prompts.get(prompt_name="greeting", version=1)

    assert isinstance(result, PromptVersion)
    assert result.version == 1
    assert result.prompt == [{"text": "Hello, world!"}]
    assert result.type == "chat"  # Type inherited from prompt


def test_get_prompt_without_label_or_version(client):
    """Test that get() raises ValueError when neither label nor version provided."""
    with pytest.raises(ValueError, match="Must provide exactly one of: label or version"):
        client.prompts.get(prompt_name="greeting")


def test_get_prompt_with_both_label_and_version(client):
    """Test that get() raises ValueError when both label and version provided."""
    with pytest.raises(
        ValueError, match="Must provide exactly one of: label or version"
    ):
        client.prompts.get(prompt_name="greeting", label="production", version=1)


@respx.mock
def test_get_prompt_not_found(client, project_id):
    """Test getting non-existent prompt."""
    # Mock prompt name resolution - not found (empty response)
    respx.get(
        f"https://api.test.langprompt.com/api/v1/projects/{project_id}/prompts",
        params={"name": "nonexistent"},
    ).mock(return_value=Response(200, json={}))

    with pytest.raises(NotFoundError, match="Prompt not found: nonexistent"):
        client.prompts.get(prompt_name="nonexistent", label="production")


@respx.mock
def test_get_version_not_found(client, project_id, prompt_id, prompt_data):
    """Test getting non-existent version."""
    # Mock prompt name resolution
    respx.get(
        f"https://api.test.langprompt.com/api/v1/projects/{project_id}/prompts",
        params={"name": "greeting"},
    ).mock(return_value=Response(200, json={"prompts": [prompt_data]}))

    # Mock version not found (404 or empty)
    respx.get(
        f"https://api.test.langprompt.com/api/v1/projects/{project_id}/prompts/{prompt_id}/versions",
        params={"label": "nonexistent"},
    ).mock(return_value=Response(404, json={"error": "Not found"}))

    with pytest.raises(Exception):  # Could be NotFoundError or other error
        client.prompts.get(prompt_name="greeting", label="nonexistent")


@respx.mock
def test_get_version_with_type_in_response(
    client, project_id, prompt_id, prompt_data, version_data_with_type
):
    """Test that type from API response is used when present."""
    # Mock prompt name resolution
    respx.get(
        f"https://api.test.langprompt.com/api/v1/projects/{project_id}/prompts",
        params={"name": "greeting"},
    ).mock(return_value=Response(200, json=prompt_data))

    # Mock version retrieval with type in response
    respx.get(
        f"https://api.test.langprompt.com/api/v1/projects/{project_id}/prompts/{prompt_id}/versions",
        params={"label": "production"},
    ).mock(return_value=Response(200, json=version_data_with_type))

    result = client.prompts.get(prompt_name="greeting", label="production")

    assert isinstance(result, PromptVersion)
    assert result.type == "chat"  # Type from version response




@respx.mock
def test_get_prompt(client, project_id, prompt_id, prompt_data, version_data):
    """Test get_prompt convenience method."""
    # Mock prompt name resolution
    respx.get(
        f"https://api.test.langprompt.com/api/v1/projects/{project_id}/prompts",
        params={"name": "greeting"},
    ).mock(return_value=Response(200, json=prompt_data))

    # Mock version retrieval
    respx.get(
        f"https://api.test.langprompt.com/api/v1/projects/{project_id}/prompts/{prompt_id}/versions",
        params={"label": "production"},
    ).mock(return_value=Response(200, json=version_data))

    content = client.prompts.get_prompt(prompt_name="greeting", label="production")

    assert content == [{"text": "Hello, world!"}]


# Asynchronous tests


@pytest.mark.asyncio
@respx.mock
async def test_async_list_prompts(async_client, project_id, prompt_data):
    """Test async listing all prompts."""
    respx.get(
        f"https://api.test.langprompt.com/api/v1/projects/{project_id}/prompts",
        params={"limit": "20", "offset": "0"},
    ).mock(
        return_value=Response(
            200,
            json={
                "prompts": [prompt_data],
                "total": 1,
                "limit": 20,
                "offset": 0,
            },
        )
    )

    result = await async_client.prompts.list()

    assert isinstance(result, PagedResponse)
    assert len(result.items) == 1
    assert result.items[0].name == "greeting"
    assert result.limit == 20
    assert result.offset == 0


@pytest.mark.asyncio
@respx.mock
async def test_async_get_prompt_by_label(
    async_client, project_id, prompt_id, prompt_data, version_data
):
    """Test async getting prompt version by label using query parameter."""
    # Mock prompt name resolution
    respx.get(
        f"https://api.test.langprompt.com/api/v1/projects/{project_id}/prompts",
        params={"name": "greeting"},
    ).mock(return_value=Response(200, json=prompt_data))

    # Mock version retrieval by label (query parameter)
    respx.get(
        f"https://api.test.langprompt.com/api/v1/projects/{project_id}/prompts/{prompt_id}/versions",
        params={"label": "production"},
    ).mock(return_value=Response(200, json=version_data))

    result = await async_client.prompts.get(prompt_name="greeting", label="production")

    assert isinstance(result, PromptVersion)
    assert result.version == 1
    assert result.labels == ["production"]
    assert result.type == "chat"  # Type inherited from prompt


@pytest.mark.asyncio
@respx.mock
async def test_async_get_prompt_by_version(
    async_client, project_id, prompt_id, prompt_data, version_data
):
    """Test async getting prompt version by version number using query parameter."""
    # Mock prompt name resolution
    respx.get(
        f"https://api.test.langprompt.com/api/v1/projects/{project_id}/prompts",
        params={"name": "greeting"},
    ).mock(return_value=Response(200, json=prompt_data))

    # Mock version retrieval by version number (query parameter)
    respx.get(
        f"https://api.test.langprompt.com/api/v1/projects/{project_id}/prompts/{prompt_id}/versions",
        params={"version": "1"},
    ).mock(return_value=Response(200, json=version_data))

    result = await async_client.prompts.get(prompt_name="greeting", version=1)

    assert isinstance(result, PromptVersion)
    assert result.version == 1
    assert result.type == "chat"  # Type inherited from prompt


@pytest.mark.asyncio
@respx.mock
async def test_async_get_prompt(
    async_client, project_id, prompt_id, prompt_data, version_data
):
    """Test async get_prompt convenience method."""
    # Mock prompt name resolution
    respx.get(
        f"https://api.test.langprompt.com/api/v1/projects/{project_id}/prompts",
        params={"name": "greeting"},
    ).mock(return_value=Response(200, json=prompt_data))

    # Mock version retrieval
    respx.get(
        f"https://api.test.langprompt.com/api/v1/projects/{project_id}/prompts/{prompt_id}/versions",
        params={"label": "production"},
    ).mock(return_value=Response(200, json=version_data))

    content = await async_client.prompts.get_prompt(
        prompt_name="greeting", label="production"
    )

    assert content == [{"text": "Hello, world!"}]


