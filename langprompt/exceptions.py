"""LangPrompt SDK exceptions hierarchy."""

from __future__ import annotations

from typing import Any


class LangPromptError(Exception):
    """Base exception for all LangPrompt SDK errors."""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
        status_code: int | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.status_code = status_code

    def __str__(self) -> str:
        parts = [self.message]
        if self.error_code:
            parts.append(f"(code: {self.error_code})")
        if self.status_code:
            parts.append(f"[HTTP {self.status_code}]")
        return " ".join(parts)


class AuthenticationError(LangPromptError):
    """Authentication failed (HTTP 401).

    Raised when the API key is missing, invalid, or expired.
    """

    def __init__(
        self,
        message: str = "Authentication failed",
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, error_code, details, status_code=401)


class PermissionError(LangPromptError):
    """Permission denied (HTTP 403).

    Raised when the API key does not have sufficient permissions
    to access the requested resource.
    """

    def __init__(
        self,
        message: str = "Permission denied",
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, error_code, details, status_code=403)


class NotFoundError(LangPromptError):
    """Resource not found (HTTP 404).

    Raised when the requested resource (project, prompt, version) does not exist.
    """

    def __init__(
        self,
        message: str = "Resource not found",
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, error_code, details, status_code=404)


class ValidationError(LangPromptError):
    """Request validation failed (HTTP 422).

    Raised when request parameters fail validation.
    """

    def __init__(
        self,
        message: str = "Validation failed",
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, error_code, details, status_code=422)


class RateLimitError(LangPromptError):
    """Rate limit exceeded (HTTP 429).

    Raised when too many requests are made in a short time period.
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
        retry_after: int | None = None,
    ):
        super().__init__(message, error_code, details, status_code=429)
        self.retry_after = retry_after


class ServerError(LangPromptError):
    """Server error (HTTP 5xx).

    Raised when the server encounters an internal error.
    """

    def __init__(
        self,
        message: str = "Server error",
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
        status_code: int = 500,
    ):
        super().__init__(message, error_code, details, status_code)


class NetworkError(LangPromptError):
    """Network communication error.

    Raised when a network error occurs (connection failed, etc).
    """

    def __init__(
        self,
        message: str = "Network error",
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, error_code, details)


class TimeoutError(LangPromptError):
    """Request timeout error.

    Raised when a request times out.
    """

    def __init__(
        self,
        message: str = "Request timeout",
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, error_code, details)


class ConfigurationError(LangPromptError):
    """Configuration error.

    Raised when SDK configuration is invalid or incomplete.
    """

    def __init__(
        self,
        message: str = "Configuration error",
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, error_code, details)
