"""Configuration management for LangPrompt SDK."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[import-not-found]

from langprompt.exceptions import ConfigurationError


DEFAULT_API_URL = "http://172.31.35.11:8100/api/v1"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0
DEFAULT_MAX_RETRY_DELAY = 30.0
DEFAULT_ENABLE_CACHE = False
DEFAULT_CACHE_TTL = 3600


class Config:
    """Configuration manager with multi-source support.

    Configuration priority (highest to lowest):
    1. Constructor parameters
    2. Environment variables
    3. Project-level config (./.langprompt)
    4. User-level config (~/.langprompt/config)
    5. Default values
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
        """Initialize configuration.

        Args:
            project_name: Project name
            project_id: Project ID (takes priority over project_name)
            api_key: API key for authentication
            base_url: API base URL
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            retry_delay: Initial retry delay in seconds
            max_retry_delay: Maximum retry delay in seconds
            enable_cache: Whether to enable caching
            cache_ttl: Cache TTL in seconds
            config_env: Configuration environment name
        """
        self.config_env = config_env

        # Load from config files
        user_config = self._load_user_config()
        project_config = self._load_project_config()

        # Merge configurations with priority
        env_config = user_config.get(config_env, {})
        project_env_config = project_config.get(config_env, {})

        # Apply configuration priority
        self.project_name = self._get_value(
            "project_name",
            explicit=project_name,
            env_var="LANGPROMPT_PROJECT_NAME",
            project_config=project_env_config,
            user_config=env_config,
        )

        self.project_id = self._get_value(
            "project_id",
            explicit=project_id,
            env_var="LANGPROMPT_PROJECT_ID",
            project_config=project_env_config,
            user_config=env_config,
        )

        self.api_key = self._get_value(
            "api_key",
            explicit=api_key,
            env_var="LANGPROMPT_API_KEY",
            project_config=project_env_config,
            user_config=env_config,
        )

        self.base_url = self._get_value(
            "base_url",
            explicit=base_url,
            env_var="LANGPROMPT_API_URL",
            project_config=project_env_config,
            user_config=env_config,
            default=DEFAULT_API_URL,
        )

        self.timeout = float(
            self._get_value(
                "timeout",
                explicit=timeout,
                project_config=project_env_config,
                user_config=env_config,
                default=DEFAULT_TIMEOUT,
            )
        )

        self.max_retries = int(
            self._get_value(
                "max_retries",
                explicit=max_retries,
                project_config=project_env_config,
                user_config=env_config,
                default=DEFAULT_MAX_RETRIES,
            )
        )

        self.retry_delay = float(
            self._get_value(
                "retry_delay",
                explicit=retry_delay,
                project_config=project_env_config,
                user_config=env_config,
                default=DEFAULT_RETRY_DELAY,
            )
        )

        self.max_retry_delay = float(
            self._get_value(
                "max_retry_delay",
                explicit=max_retry_delay,
                project_config=project_env_config,
                user_config=env_config,
                default=DEFAULT_MAX_RETRY_DELAY,
            )
        )

        self.enable_cache = bool(
            self._get_value(
                "enable_cache",
                explicit=enable_cache,
                project_config=project_env_config,
                user_config=env_config,
                default=DEFAULT_ENABLE_CACHE,
            )
        )

        self.cache_ttl = int(
            self._get_value(
                "cache_ttl",
                explicit=cache_ttl,
                project_config=project_env_config,
                user_config=env_config,
                default=DEFAULT_CACHE_TTL,
            )
        )

        # Validate configuration
        self._validate()

    def _get_value(
        self,
        key: str,
        explicit: Any = None,
        env_var: str | None = None,
        project_config: dict[str, Any] | None = None,
        user_config: dict[str, Any] | None = None,
        default: Any = None,
    ) -> Any:
        """Get configuration value with priority."""
        # 1. Explicit parameter (highest priority)
        if explicit is not None:
            return explicit

        # 2. Environment variable
        if env_var and (env_value := os.environ.get(env_var)):
            return env_value

        # 3. Project-level config
        if project_config and key in project_config:
            return project_config[key]

        # 4. User-level config
        if user_config and key in user_config:
            return user_config[key]

        # 5. Default value (lowest priority)
        return default

    def _load_user_config(self) -> dict[str, Any]:
        """Load user-level configuration from ~/.langprompt/config."""
        config_path = Path.home() / ".langprompt" / "config"
        return self._load_toml_file(config_path)

    def _load_project_config(self) -> dict[str, Any]:
        """Load project-level configuration from ./.langprompt."""
        config_path = Path.cwd() / ".langprompt"
        return self._load_toml_file(config_path)

    def _load_toml_file(self, path: Path) -> dict[str, Any]:
        """Load TOML configuration file."""
        if not path.exists():
            return {}

        try:
            with path.open("rb") as f:
                return tomllib.load(f)
        except Exception as e:
            raise ConfigurationError(
                f"Failed to load config file {path}: {e}",
                error_code="CONFIG_LOAD_ERROR",
                details={"path": str(path), "error": str(e)},
            ) from e

    def _validate(self) -> None:
        """Validate configuration."""
        # Validate base_url
        if not self.base_url:
            raise ConfigurationError(
                "API base URL is required",
                error_code="MISSING_BASE_URL",
            )

        # Ensure HTTPS (unless explicitly http://localhost)
        if not self.base_url.startswith(("https://", "http://")):
            raise ConfigurationError(
                "API base URL must use http协议",
                error_code="INSECURE_URL",
                details={"base_url": self.base_url},
            )

        # Validate timeout
        if self.timeout <= 0:
            raise ConfigurationError(
                "Timeout must be positive",
                error_code="INVALID_TIMEOUT",
                details={"timeout": self.timeout},
            )

        # Validate retries
        if self.max_retries < 0:
            raise ConfigurationError(
                "Max retries must be non-negative",
                error_code="INVALID_MAX_RETRIES",
                details={"max_retries": self.max_retries},
            )

        # Validate retry delays
        if self.retry_delay <= 0:
            raise ConfigurationError(
                "Retry delay must be positive",
                error_code="INVALID_RETRY_DELAY",
                details={"retry_delay": self.retry_delay},
            )

        if self.max_retry_delay < self.retry_delay:
            raise ConfigurationError(
                "Max retry delay must be >= retry delay",
                error_code="INVALID_MAX_RETRY_DELAY",
                details={
                    "retry_delay": self.retry_delay,
                    "max_retry_delay": self.max_retry_delay,
                },
            )

        # Validate cache TTL
        if self.cache_ttl <= 0:
            raise ConfigurationError(
                "Cache TTL must be positive",
                error_code="INVALID_CACHE_TTL",
                details={"cache_ttl": self.cache_ttl},
            )

    def __repr__(self) -> str:
        """Return string representation of config."""
        api_key_display = f"{self.api_key[:10]}..." if self.api_key else "None"
        return (
            f"Config("
            f"project_id={self.project_id}, "
            f"project_name={self.project_name}, "
            f"api_key={api_key_display}, "
            f"base_url={self.base_url}, "
            f"timeout={self.timeout}, "
            f"enable_cache={self.enable_cache})"
        )
