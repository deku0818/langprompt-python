"""Base resource class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from langprompt.cache import Cache
    from langprompt.config import Config
    from langprompt.http import AsyncHttpClient, HttpClient


class BaseResource:
    """Base class for synchronous resource modules."""

    def __init__(
        self,
        http_client: "HttpClient",
        config: "Config",
        cache: "Cache",
    ):
        """Initialize resource.

        Args:
            http_client: HTTP client
            config: Configuration
            cache: Cache instance
        """
        self._http = http_client
        self._config = config
        self._cache = cache

    def _get_json(self, response: Any) -> Any:
        """Parse JSON response and unwrap if needed."""
        data = response.json()

        # Unwrap server response format: {"success": true, "data": {...}}
        if isinstance(data, dict) and "success" in data and "data" in data:
            return data["data"]

        return data


class AsyncBaseResource:
    """Base class for asynchronous resource modules."""

    def __init__(
        self,
        http_client: "AsyncHttpClient",
        config: "Config",
        cache: "Cache",
    ):
        """Initialize async resource.

        Args:
            http_client: Async HTTP client
            config: Configuration
            cache: Cache instance
        """
        self._http = http_client
        self._config = config
        self._cache = cache

    def _get_json(self, response: Any) -> Any:
        """Parse JSON response and unwrap if needed."""
        data = response.json()

        # Unwrap server response format: {"success": true, "data": {...}}
        if isinstance(data, dict) and "success" in data and "data" in data:
            return data["data"]

        return data
