"""Main LangPrompt SDK client."""

from __future__ import annotations

from typing import Any

from langprompt.cache import Cache
from langprompt.config import Config
from langprompt.http import AsyncHttpClient, HttpClient
from langprompt.resources import (
    AsyncProjectsResource,
    AsyncPromptsResource,
    ProjectsResource,
    PromptsResource,
)


class LangPrompt:
    """Synchronous LangPrompt SDK client.

    Example:
        >>> client = LangPrompt(
        ...     project_name="my-project",
        ...     api_key="your-api-key"
        ... )
        >>> project = client.projects.get()
        >>> prompt = client.prompts.get("greeting", label="production")
    """

    def __init__(
        self,
        project_name: str | None = None,
        project_id: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        retry_delay: float | None = None,
        max_retry_delay: float | None = None,
        enable_cache: bool | None = None,
        cache_ttl: int | None = None,
        config_env: str = "default",
    ):
        """Initialize LangPrompt client.

        Args:
            project_name: Project name
            project_id: Project ID (takes priority over project_name)
            api_key: API key for authentication
            base_url: API base URL
            timeout: Request timeout in seconds (default: 30.0)
            max_retries: Maximum number of retries (default: 3)
            retry_delay: Initial retry delay in seconds (default: 1.0)
            max_retry_delay: Maximum retry delay in seconds (default: 30.0)
            enable_cache: Whether to enable caching (default: False)
            cache_ttl: Cache TTL in seconds (default: 3600)
            config_env: Configuration environment name (default: "default")
        """
        # Initialize configuration
        self._config = Config(
            project_name=project_name,
            project_id=project_id,
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
            max_retry_delay=max_retry_delay,
            enable_cache=enable_cache,
            cache_ttl=cache_ttl,
            config_env=config_env,
        )

        # Initialize cache
        self._cache = Cache(
            enabled=self._config.enable_cache,
            default_ttl=self._config.cache_ttl,
        )

        # Initialize HTTP client
        self._http_client = HttpClient(self._config)

        # Initialize resource modules
        self.projects = ProjectsResource(self._http_client, self._config, self._cache)
        self.prompts = PromptsResource(self._http_client, self._config, self._cache)

    def __enter__(self) -> "LangPrompt":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()

    def close(self) -> None:
        """Close client and cleanup resources."""
        self._http_client.close()

    @property
    def config(self) -> Config:
        """Get configuration."""
        return self._config

    @property
    def cache(self) -> Cache:
        """Get cache instance."""
        return self._cache


class AsyncLangPrompt:
    """Asynchronous LangPrompt SDK client.

    Example:
        >>> async with AsyncLangPrompt(
        ...     project_name="my-project",
        ...     api_key="your-api-key"
        ... ) as client:
        ...     project = await client.projects.get()
        ...     prompt = await client.prompts.get("greeting", label="production")
    """

    def __init__(
        self,
        project_name: str | None = None,
        project_id: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        retry_delay: float | None = None,
        max_retry_delay: float | None = None,
        enable_cache: bool | None = None,
        cache_ttl: int | None = None,
        config_env: str = "default",
    ):
        """Initialize async LangPrompt client.

        Args:
            project_name: Project name
            project_id: Project ID (takes priority over project_name)
            api_key: API key for authentication
            base_url: API base URL
            timeout: Request timeout in seconds (default: 30.0)
            max_retries: Maximum number of retries (default: 3)
            retry_delay: Initial retry delay in seconds (default: 1.0)
            max_retry_delay: Maximum retry delay in seconds (default: 30.0)
            enable_cache: Whether to enable caching (default: False)
            cache_ttl: Cache TTL in seconds (default: 3600)
            config_env: Configuration environment name (default: "default")
        """
        # Initialize configuration
        self._config = Config(
            project_name=project_name,
            project_id=project_id,
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
            max_retry_delay=max_retry_delay,
            enable_cache=enable_cache,
            cache_ttl=cache_ttl,
            config_env=config_env,
        )

        # Initialize cache
        self._cache = Cache(
            enabled=self._config.enable_cache,
            default_ttl=self._config.cache_ttl,
        )

        # Initialize HTTP client
        self._http_client = AsyncHttpClient(self._config)

        # Initialize resource modules
        self.projects = AsyncProjectsResource(
            self._http_client, self._config, self._cache
        )
        self.prompts = AsyncPromptsResource(
            self._http_client, self._config, self._cache
        )

    async def __aenter__(self) -> "AsyncLangPrompt":
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Close client and cleanup resources."""
        await self._http_client.close()

    @property
    def config(self) -> Config:
        """Get configuration."""
        return self._config

    @property
    def cache(self) -> Cache:
        """Get cache instance."""
        return self._cache
