"""Pytest configuration and fixtures."""

import pytest
import pytest_asyncio

from langprompt import LangPrompt, AsyncLangPrompt
from langprompt.config import Config


@pytest.fixture
def config():
    """Create test configuration."""
    return Config(
        project_name="test-project",
        project_id="550e8400-e29b-41d4-a716-446655440000",
        api_key="test-api-key",
        base_url="https://api.test.langprompt.com/api/v1",
        timeout=10.0,
        max_retries=2,
        enable_cache=False,
    )


@pytest.fixture
def client(config):
    """Create synchronous test client."""
    client = LangPrompt(
        project_name=config.project_name,
        project_id=config.project_id,
        api_key=config.api_key,
        base_url=config.base_url,
        timeout=config.timeout,
        max_retries=config.max_retries,
    )
    yield client
    client.close()


@pytest_asyncio.fixture
async def async_client(config):
    """Create asynchronous test client."""
    client = AsyncLangPrompt(
        project_name=config.project_name,
        project_id=config.project_id,
        api_key=config.api_key,
        base_url=config.base_url,
        timeout=config.timeout,
        max_retries=config.max_retries,
    )
    yield client
    await client.close()
