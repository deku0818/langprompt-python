"""HTTP client with retry support."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from langprompt.config import Config
from langprompt.exceptions import (
    AuthenticationError,
    LangPromptError,
    NetworkError,
    NotFoundError,
    PermissionError,
    RateLimitError,
    ServerError,
    TimeoutError,
    ValidationError,
)
from langprompt.http.retry import retry_async, retry_sync


logger = logging.getLogger(__name__)


def _parse_error_response(response: httpx.Response) -> dict[str, Any]:
    """Parse error response from API."""
    try:
        data = response.json()
        return {
            "error_code": data.get("error_code"),
            "message": data.get("message", response.text),
            "details": data.get("details", {}),
        }
    except Exception:
        return {
            "error_code": None,
            "message": response.text or f"HTTP {response.status_code}",
            "details": {},
        }


def _handle_error_response(response: httpx.Response) -> None:
    """Convert HTTP error response to appropriate exception."""
    error_data = _parse_error_response(response)

    if response.status_code == 401:
        raise AuthenticationError(
            message=error_data["message"],
            error_code=error_data["error_code"],
            details=error_data["details"],
        )
    elif response.status_code == 403:
        raise PermissionError(
            message=error_data["message"],
            error_code=error_data["error_code"],
            details=error_data["details"],
        )
    elif response.status_code == 404:
        raise NotFoundError(
            message=error_data["message"],
            error_code=error_data["error_code"],
            details=error_data["details"],
        )
    elif response.status_code == 422:
        raise ValidationError(
            message=error_data["message"],
            error_code=error_data["error_code"],
            details=error_data["details"],
        )
    elif response.status_code == 429:
        retry_after = response.headers.get("Retry-After")
        raise RateLimitError(
            message=error_data["message"],
            error_code=error_data["error_code"],
            details=error_data["details"],
            retry_after=int(retry_after) if retry_after else None,
        )
    elif response.status_code >= 500:
        raise ServerError(
            message=error_data["message"],
            error_code=error_data["error_code"],
            details=error_data["details"],
            status_code=response.status_code,
        )
    else:
        raise LangPromptError(
            message=error_data["message"],
            error_code=error_data["error_code"],
            details=error_data["details"],
            status_code=response.status_code,
        )


class HttpClient:
    """Synchronous HTTP client with retry support."""

    def __init__(self, config: Config):
        """Initialize HTTP client.

        Args:
            config: Configuration object
        """
        self.config = config
        self._client: httpx.Client | None = None

    def __enter__(self) -> "HttpClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()

    def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            self._client.close()
            self._client = None

    @property
    def client(self) -> httpx.Client:
        """Get or create httpx client."""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                headers=self._get_headers(),
            )
        return self._client

    def _get_headers(self) -> dict[str, str]:
        """Get request headers."""
        headers = {
            "User-Agent": "langprompt-python/0.1.0",
            "Accept": "application/json",
        }

        if self.config.api_key:
            headers["X-API-Key"] = self.config.api_key

        return headers

    def _make_request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make HTTP request with error handling."""
        try:
            response = self.client.request(method, path, **kwargs)
            response.raise_for_status()
            return response
        except httpx.TimeoutException as e:
            raise TimeoutError(
                message=f"Request timeout: {e}",
                error_code="TIMEOUT",
            ) from e
        except httpx.NetworkError as e:
            raise NetworkError(
                message=f"Network error: {e}",
                error_code="NETWORK_ERROR",
            ) from e
        except httpx.HTTPStatusError as e:
            _handle_error_response(e.response)
            raise  # Should never reach here

    def request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make HTTP request with retry logic.

        Args:
            method: HTTP method
            path: Request path
            **kwargs: Additional request parameters

        Returns:
            HTTP response

        Raises:
            LangPromptError: On error
        """
        return retry_sync(
            lambda: self._make_request(method, path, **kwargs),
            max_retries=self.config.max_retries,
            base_delay=self.config.retry_delay,
            max_delay=self.config.max_retry_delay,
        )

    def get(self, path: str, **kwargs: Any) -> httpx.Response:
        """Make GET request."""
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> httpx.Response:
        """Make POST request."""
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> httpx.Response:
        """Make PUT request."""
        return self.request("PUT", path, **kwargs)

    def patch(self, path: str, **kwargs: Any) -> httpx.Response:
        """Make PATCH request."""
        return self.request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> httpx.Response:
        """Make DELETE request."""
        return self.request("DELETE", path, **kwargs)


class AsyncHttpClient:
    """Asynchronous HTTP client with retry support."""

    def __init__(self, config: Config):
        """Initialize async HTTP client.

        Args:
            config: Configuration object
        """
        self.config = config
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "AsyncHttpClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create async httpx client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout,
                headers=self._get_headers(),
            )
        return self._client

    def _get_headers(self) -> dict[str, str]:
        """Get request headers."""
        headers = {
            "User-Agent": "langprompt-python/0.1.0",
            "Accept": "application/json",
        }

        if self.config.api_key:
            headers["X-API-Key"] = self.config.api_key

        return headers

    async def _make_request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make async HTTP request with error handling."""
        try:
            response = await self.client.request(method, path, **kwargs)
            response.raise_for_status()
            return response
        except httpx.TimeoutException as e:
            raise TimeoutError(
                message=f"Request timeout: {e}",
                error_code="TIMEOUT",
            ) from e
        except httpx.NetworkError as e:
            raise NetworkError(
                message=f"Network error: {e}",
                error_code="NETWORK_ERROR",
            ) from e
        except httpx.HTTPStatusError as e:
            _handle_error_response(e.response)
            raise  # Should never reach here

    async def request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make async HTTP request with retry logic.

        Args:
            method: HTTP method
            path: Request path
            **kwargs: Additional request parameters

        Returns:
            HTTP response

        Raises:
            LangPromptError: On error
        """
        return await retry_async(
            lambda: self._make_request(method, path, **kwargs),
            max_retries=self.config.max_retries,
            base_delay=self.config.retry_delay,
            max_delay=self.config.max_retry_delay,
        )

    async def get(self, path: str, **kwargs: Any) -> httpx.Response:
        """Make async GET request."""
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs: Any) -> httpx.Response:
        """Make async POST request."""
        return await self.request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs: Any) -> httpx.Response:
        """Make async PUT request."""
        return await self.request("PUT", path, **kwargs)

    async def patch(self, path: str, **kwargs: Any) -> httpx.Response:
        """Make async PATCH request."""
        return await self.request("PATCH", path, **kwargs)

    async def delete(self, path: str, **kwargs: Any) -> httpx.Response:
        """Make async DELETE request."""
        return await self.request("DELETE", path, **kwargs)
