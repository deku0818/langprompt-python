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


# Create prompt tests


@respx.mock
def test_create_version_for_existing_prompt(client, project_id, prompt_id, prompt_data):
    """Test creating a new version for existing prompt."""
    created_version = {
        "id": "770e8400-e29b-41d4-a716-446655440002",
        "prompt_id": prompt_id,
        "version": 2,
        "prompt": [{"role": "user", "content": "你好{name}"}],
        "type": "text",
        "labels": ["production"],
        "metadata": {"test": "value"},
        "commit_message": "提交信息",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }

    # Mock prompt name resolution - found
    respx.get(
        f"https://api.test.langprompt.com/api/v1/projects/{project_id}/prompts",
        params={"name": "greeting"},
    ).mock(return_value=Response(200, json=prompt_data))

    # Mock version creation
    respx.post(
        f"https://api.test.langprompt.com/api/v1/projects/{project_id}/prompts/{prompt_id}/versions"
    ).mock(return_value=Response(200, json=created_version))

    result = client.prompts.create(
        name="greeting",
        prompt="你好{name}",
        type="text",
        metadata={"test": "value"},
        labels=["production"],
        commit_message="提交信息",
    )

    assert isinstance(result, PromptVersion)
    assert result.version == 2
    assert result.prompt == [{"role": "user", "content": "你好{name}"}]
    assert result.type == "text"
    assert result.labels == ["production"]
    assert result.metadata == {"test": "value"}


@respx.mock
def test_create_version_chat_type(client, project_id, prompt_id, prompt_data):
    """Test creating a chat version for existing prompt."""
    created_version = {
        "id": "770e8400-e29b-41d4-a716-446655440002",
        "prompt_id": prompt_id,
        "version": 2,
        "prompt": [
            {"role": "system", "content": "系统提示词"},
            {"role": "user", "content": "你好{name}"},
        ],
        "type": "chat",
        "labels": ["production"],
        "metadata": {},
        "commit_message": "提交信息",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }

    # Mock prompt name resolution - found
    respx.get(
        f"https://api.test.langprompt.com/api/v1/projects/{project_id}/prompts",
        params={"name": "greeting"},
    ).mock(return_value=Response(200, json=prompt_data))

    # Mock version creation
    respx.post(
        f"https://api.test.langprompt.com/api/v1/projects/{project_id}/prompts/{prompt_id}/versions"
    ).mock(return_value=Response(200, json=created_version))

    result = client.prompts.create(
        name="greeting",
        prompt=[
            {"role": "system", "content": "系统提示词"},
            {"role": "user", "content": "你好{name}"},
        ],
        type="chat",
        metadata={},
        labels=["production"],
        commit_message="提交信息",
    )

    assert isinstance(result, PromptVersion)
    assert result.version == 2
    assert len(result.prompt) == 2
    assert result.type == "chat"


@respx.mock
def test_create_prompt_not_found_without_force(client, project_id):
    """Test that creating version for non-existent prompt without force raises NotFoundError."""
    # Mock prompt name resolution - not found
    respx.get(
        f"https://api.test.langprompt.com/api/v1/projects/{project_id}/prompts",
        params={"name": "nonexistent"},
    ).mock(return_value=Response(200, json={}))

    with pytest.raises(NotFoundError, match="not found.*force=True"):
        client.prompts.create(
            name="nonexistent",
            prompt="Some content",
            type="text",
        )


@respx.mock
def test_create_with_force_creates_prompt(client, project_id):
    """Test creating prompt with force=True when prompt doesn't exist."""
    created_prompt_id = "660e8400-e29b-41d4-a716-446655440001"

    created_prompt = {
        "id": created_prompt_id,
        "name": "new-prompt",
        "type": "text",
        "description": "",
        "tags": [],
        "project_id": project_id,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }

    created_version = {
        "id": "770e8400-e29b-41d4-a716-446655440002",
        "prompt_id": created_prompt_id,
        "version": 1,
        "prompt": [{"role": "user", "content": "New prompt"}],
        "type": "text",
        "labels": [],
        "metadata": {},
        "commit_message": "Initial version",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }

    # Mock prompt name resolution - not found
    respx.get(
        f"https://api.test.langprompt.com/api/v1/projects/{project_id}/prompts",
        params={"name": "new-prompt"},
    ).mock(return_value=Response(200, json={}))

    # Mock prompt creation (Step 1)
    respx.post(
        f"https://api.test.langprompt.com/api/v1/projects/{project_id}/prompts"
    ).mock(return_value=Response(200, json=created_prompt))

    # Mock version creation (Step 2)
    respx.post(
        f"https://api.test.langprompt.com/api/v1/projects/{project_id}/prompts/{created_prompt_id}/versions"
    ).mock(return_value=Response(200, json=created_version))

    result = client.prompts.create(
        name="new-prompt",
        prompt="New prompt",
        type="text",
        force=True,
    )

    assert isinstance(result, PromptVersion)
    assert result.version == 1


@respx.mock
def test_create_force_requires_type_when_not_exists(client, project_id):
    """Test that force=True requires type parameter when prompt doesn't exist."""
    # Mock prompt name resolution - not found
    respx.get(
        f"https://api.test.langprompt.com/api/v1/projects/{project_id}/prompts",
        params={"name": "new-prompt"},
    ).mock(return_value=Response(200, json={}))

    with pytest.raises(ValueError, match="'type' is required"):
        client.prompts.create(
            name="new-prompt",
            prompt="Some content",
            force=True,
            # type not provided
        )


def test_create_prompt_invalid_type(client):
    """Test that invalid type raises ValidationError."""
    with pytest.raises(ValidationError, match="Invalid prompt type"):
        client.prompts.create(
            name="test",
            prompt="content",
            type="invalid",
        )


def test_create_prompt_text_type_wrong_format(client):
    """Test that passing list for text type raises ValidationError."""
    with pytest.raises(ValidationError, match="Prompt must be a string"):
        client.prompts.create(
            name="test",
            prompt=[{"role": "user", "content": "test"}],
            type="text",
        )


def test_create_prompt_chat_type_wrong_format(client):
    """Test that passing string for chat type raises ValidationError."""
    with pytest.raises(ValidationError, match="Prompt must be a list"):
        client.prompts.create(
            name="test",
            prompt="some string",
            type="chat",
        )


# Async create prompt tests


@pytest.mark.asyncio
@respx.mock
async def test_async_create_version_for_existing(
    async_client, project_id, prompt_id, prompt_data
):
    """Test async creating a new version for existing prompt."""
    created_version = {
        "id": "770e8400-e29b-41d4-a716-446655440002",
        "prompt_id": prompt_id,
        "version": 2,
        "prompt": [{"role": "user", "content": "你好{name}"}],
        "type": "text",
        "labels": ["production"],
        "metadata": {"test": "value"},
        "commit_message": "提交信息",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }

    # Mock prompt name resolution - found
    respx.get(
        f"https://api.test.langprompt.com/api/v1/projects/{project_id}/prompts",
        params={"name": "greeting"},
    ).mock(return_value=Response(200, json=prompt_data))

    # Mock version creation
    respx.post(
        f"https://api.test.langprompt.com/api/v1/projects/{project_id}/prompts/{prompt_id}/versions"
    ).mock(return_value=Response(200, json=created_version))

    result = await async_client.prompts.create(
        name="greeting",
        prompt="你好{name}",
        type="text",
        metadata={"test": "value"},
        labels=["production"],
        commit_message="提交信息",
    )

    assert isinstance(result, PromptVersion)
    assert result.version == 2
    assert result.prompt == [{"role": "user", "content": "你好{name}"}]
    assert result.type == "text"


@pytest.mark.asyncio
@respx.mock
async def test_async_create_with_force(async_client, project_id):
    """Test async creating prompt with force=True when doesn't exist."""
    created_prompt_id = "660e8400-e29b-41d4-a716-446655440001"

    created_prompt = {
        "id": created_prompt_id,
        "name": "new-prompt",
        "type": "text",
        "description": "",
        "tags": [],
        "project_id": project_id,
        "created_at": "2024-01-02T00:00:00Z",
        "updated_at": "2024-01-02T00:00:00Z",
    }

    created_version = {
        "id": "770e8400-e29b-41d4-a716-446655440003",
        "prompt_id": created_prompt_id,
        "version": 1,
        "prompt": [{"role": "user", "content": "Updated content"}],
        "type": "text",
        "labels": ["staging"],
        "metadata": {},
        "commit_message": "Initial version",
        "created_at": "2024-01-02T00:00:00Z",
        "updated_at": "2024-01-02T00:00:00Z",
    }

    # Mock prompt name resolution - not found
    respx.get(
        f"https://api.test.langprompt.com/api/v1/projects/{project_id}/prompts",
        params={"name": "new-prompt"},
    ).mock(return_value=Response(200, json={}))

    # Mock prompt creation (Step 1)
    respx.post(
        f"https://api.test.langprompt.com/api/v1/projects/{project_id}/prompts"
    ).mock(return_value=Response(200, json=created_prompt))

    # Mock version creation (Step 2)
    respx.post(
        f"https://api.test.langprompt.com/api/v1/projects/{project_id}/prompts/{created_prompt_id}/versions"
    ).mock(return_value=Response(200, json=created_version))

    result = await async_client.prompts.create(
        name="new-prompt",
        prompt="Updated content",
        type="text",
        labels=["staging"],
        force=True,
    )

    assert isinstance(result, PromptVersion)
    assert result.version == 1


