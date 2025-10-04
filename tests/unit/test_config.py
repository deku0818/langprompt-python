"""Tests for configuration module."""

import os
import tempfile
from pathlib import Path

import pytest

from langprompt.config import Config
from langprompt.exceptions import ConfigurationError


def test_config_defaults():
    """Test default configuration values."""
    config = Config(
        project_name="test",
        api_key="key",
        base_url="https://api.langprompt.com/api/v1",
        timeout=30.0,
        max_retries=3,
        enable_cache=False,
    )

    assert config.project_name == "test"
    assert config.api_key == "key"
    assert config.base_url == "https://api.langprompt.com/api/v1"
    assert config.timeout == 30.0
    assert config.max_retries == 3
    assert config.enable_cache is False


def test_config_explicit_params():
    """Test explicit parameters take priority."""
    config = Config(
        project_name="test",
        api_key="key",
        timeout=60.0,
        max_retries=5,
        enable_cache=True,
    )

    assert config.timeout == 60.0
    assert config.max_retries == 5
    assert config.enable_cache is True


def test_config_env_vars(monkeypatch):
    """Test environment variables."""
    monkeypatch.setenv("LANGPROMPT_PROJECT_NAME", "env-project")
    monkeypatch.setenv("LANGPROMPT_API_KEY", "env-api-key")
    monkeypatch.setenv("LANGPROMPT_API_URL", "https://custom.api.com/v1")

    config = Config()

    assert config.project_name == "env-project"
    assert config.api_key == "env-api-key"
    assert config.base_url == "https://custom.api.com/v1"


def test_config_priority(monkeypatch):
    """Test configuration priority: explicit > env > default."""
    monkeypatch.setenv("LANGPROMPT_PROJECT_NAME", "env-project")

    config = Config(project_name="explicit-project")

    # Explicit param should take priority over env var
    assert config.project_name == "explicit-project"

def test_config_timeout_validation():
    """Test timeout validation."""
    with pytest.raises(ConfigurationError, match="Timeout must be positive"):
        Config(
            project_name="test",
            timeout=0,
        )

    with pytest.raises(ConfigurationError, match="Timeout must be positive"):
        Config(
            project_name="test",
            timeout=-1,
        )


def test_config_retries_validation():
    """Test retries validation."""
    with pytest.raises(ConfigurationError, match="Max retries must be non-negative"):
        Config(
            project_name="test",
            max_retries=-1,
        )


def test_config_repr():
    """Test configuration string representation."""
    config = Config(
        project_id="12345",
        project_name="test",
        api_key="very-long-api-key-12345678",
    )

    repr_str = repr(config)
    assert "project_id=12345" in repr_str
    assert "project_name=test" in repr_str
    # API key should be truncated
    assert "very-long-" in repr_str
    assert "12345678" not in repr_str
