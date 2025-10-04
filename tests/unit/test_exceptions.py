"""Tests for exception classes."""

import pytest

from langprompt.exceptions import (
    AuthenticationError,
    ConfigurationError,
    LangPromptError,
    NetworkError,
    NotFoundError,
    PermissionError,
    RateLimitError,
    ServerError,
    TimeoutError,
    ValidationError,
)


def test_base_exception():
    """Test base LangPromptError."""
    error = LangPromptError(
        message="Test error",
        error_code="TEST_ERROR",
        details={"key": "value"},
        status_code=400,
    )

    assert str(error) == "Test error (code: TEST_ERROR) [HTTP 400]"
    assert error.message == "Test error"
    assert error.error_code == "TEST_ERROR"
    assert error.details == {"key": "value"}
    assert error.status_code == 400


def test_authentication_error():
    """Test AuthenticationError."""
    error = AuthenticationError(message="Invalid API key")
    assert error.status_code == 401
    assert "Invalid API key" in str(error)


def test_permission_error():
    """Test PermissionError."""
    error = PermissionError(message="Access denied")
    assert error.status_code == 403
    assert "Access denied" in str(error)


def test_not_found_error():
    """Test NotFoundError."""
    error = NotFoundError(message="Resource not found")
    assert error.status_code == 404
    assert "Resource not found" in str(error)


def test_validation_error():
    """Test ValidationError."""
    error = ValidationError(message="Invalid parameters")
    assert error.status_code == 422
    assert "Invalid parameters" in str(error)


def test_rate_limit_error():
    """Test RateLimitError."""
    error = RateLimitError(message="Too many requests", retry_after=60)
    assert error.status_code == 429
    assert error.retry_after == 60
    assert "Too many requests" in str(error)


def test_server_error():
    """Test ServerError."""
    error = ServerError(message="Internal server error", status_code=500)
    assert error.status_code == 500
    assert "Internal server error" in str(error)


def test_network_error():
    """Test NetworkError."""
    error = NetworkError(message="Connection failed")
    assert "Connection failed" in str(error)


def test_timeout_error():
    """Test TimeoutError."""
    error = TimeoutError(message="Request timeout")
    assert "Request timeout" in str(error)


def test_configuration_error():
    """Test ConfigurationError."""
    error = ConfigurationError(message="Invalid config")
    assert "Invalid config" in str(error)
