"""Prompts resource module."""

from __future__ import annotations

from ast import Return
from typing import TYPE_CHECKING, Any, Union

from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    PromptTemplate,
)

from langprompt.models import PagedResponse, Prompt, PromptContent, PromptVersion
from langprompt.resources.base import AsyncBaseResource, BaseResource

if TYPE_CHECKING:
    from langprompt.cache import Cache
    from langprompt.config import Config
    from langprompt.http import AsyncHttpClient, HttpClient


class PromptsResource(BaseResource):
    """Prompts resource for synchronous operations."""

    def __init__(
        self,
        http_client: "HttpClient",
        config: "Config",
        cache: "Cache",
    ):
        """Initialize prompts resource."""
        super().__init__(http_client, config, cache)
        self._resolved_project_id: str | None = None
        self._prompt_cache: dict[
            str, tuple[str, str]
        ] = {}  # {prompt_name: (prompt_id, prompt_type)}

    def _get_project_id(self) -> str:
        """Get project ID, resolving from project_name if necessary."""
        # Return cached project_id if already resolved
        if self._resolved_project_id:
            return self._resolved_project_id

        # Use configured project_id if available
        if self._config.project_id:
            self._resolved_project_id = self._config.project_id
            return self._resolved_project_id

        # Resolve from project_name
        if self._config.project_name:
            # Query projects API to get project by name
            # API returns single project object when querying by name
            response = self._http.get(
                "/projects", params={"name": self._config.project_name}
            )
            data = self._get_json(response)

            # API returns single project object directly
            if not data:
                from langprompt.exceptions import NotFoundError

                raise NotFoundError(f"Project not found: {self._config.project_name}")

            self._resolved_project_id = data["id"]
            return self._resolved_project_id

        # Neither project_id nor project_name is configured
        raise ValueError("Either project_id or project_name must be configured")

    def _resolve_prompt_id(self, prompt_name: str) -> tuple[str, str]:
        """Resolve prompt name to prompt ID and type.

        Args:
            prompt_name: Prompt name

        Returns:
            Tuple of (prompt_id, prompt_type)

        Raises:
            NotFoundError: If prompt not found
        """
        # Check cache first
        if prompt_name in self._prompt_cache:
            return self._prompt_cache[prompt_name]

        project_id = self._get_project_id()
        response = self._http.get(
            f"/projects/{project_id}/prompts", params={"name": prompt_name}
        )
        data = self._get_json(response)

        # Handle response format
        if isinstance(data, dict) and "id" in data:
            prompt_id = data["id"]
            prompt_type = data.get("type", "")
            self._prompt_cache[prompt_name] = (prompt_id, prompt_type)
            return prompt_id, prompt_type

        # If not a valid prompt object, it's not found
        from langprompt.exceptions import NotFoundError

        raise NotFoundError(f"Prompt not found: {prompt_name}")

    def list(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> PagedResponse[Prompt]:
        """List all prompts in the project.

        Args:
            limit: Maximum number of items to return
            offset: Number of items to skip

        Returns:
            PagedResponse of Prompts

        Raises:
            ValidationError: If parameters invalid
        """
        params: dict[str, Any] = {
            "limit": limit,
            "offset": offset,
        }

        project_id = self._get_project_id()
        response = self._http.get(f"/projects/{project_id}/prompts", params=params)
        data = self._get_json(response)

        # Handle server response format
        prompts_list = data.get("prompts", data.get("items", []))
        total = data.get("total", 0)

        # Calculate pagination info
        has_next = offset + len(prompts_list) < total

        return PagedResponse[Prompt](
            items=[Prompt(**item) for item in prompts_list],
            total=total,
            limit=limit,
            offset=offset,
            has_next=has_next,
        )

    def get(
        self,
        prompt_name: str,
        label: str | None = None,
        version: int | None = None,
    ) -> PromptVersion:
        """Get prompt version by label or version number.

        Must provide either label OR version (not both).

        Args:
            prompt_name: Prompt name
            label: Version label (e.g., "production", "staging")
            version: Version number

        Returns:
            PromptVersion object

        Raises:
            ValueError: If neither or both label and version provided
            NotFoundError: If prompt/version not found
        """
        if (label is None and version is None) or (label and version):
            raise ValueError("Must provide exactly one of: label or version")

        # Build cache key
        identifier = label if label else str(version)
        cache_key = self._cache.make_key(
            self._config.project_id or "_",
            "version",
            prompt_name,
            identifier,
        )

        # Check cache
        cached = self._cache.get(cache_key)
        if cached:
            return PromptVersion(**cached)

        # Resolve prompt name to ID and get type
        project_id = self._get_project_id()
        prompt_id, prompt_type = self._resolve_prompt_id(prompt_name)

        # Build request with query parameters
        params = {}
        if label:
            params["label"] = label
        else:
            params["version"] = version

        response = self._http.get(
            f"/projects/{project_id}/prompts/{prompt_id}/versions", params=params
        )
        data = self._get_json(response)

        # Add type if not present in response
        if "type" not in data:
            data["type"] = prompt_type

        # Cache result (version content is immutable, can cache longer)
        ttl = None if version else self._config.cache_ttl
        self._cache.set(cache_key, data, ttl=ttl)

        return PromptVersion(**data)

    def get_prompt(
        self,
        prompt_name: str,
        label: str = "production",
        version: int | None = None,
    ) -> list[Any]:
        """Get prompt content.

        Convenience method to get only the prompt field.

        Args:
            prompt_name: Prompt name
            label: Version label (default: "production")
            version: Version number (overrides label if provided)

        Returns:
            Prompt content list
        """
        prompt_version = self.get(
            prompt_name=prompt_name,
            label=None if version else label,
            version=version,
        )
        return prompt_version.prompt

    def get_lp(
        self,
        prompt_name: str,
        label: str | None = None,
        version: int | None = None,
    ) -> Union[PromptTemplate, ChatPromptTemplate]:
        """Get LangChain Prompt.

        Convenience method to get only the prompt field.

        Args:
            prompt_name: Prompt name
            label: Version label (default: "production")
            version: Version number (overrides label if provided)

        Returns:
            Prompt content list
        """
        prompt_version = self.get(
            prompt_name=prompt_name,
            label=None if version else label,
            version=version,
        )
        return self._get_langchain_prompt(prompt_version)

    def _get_langchain_prompt(
        self, prompt_version: PromptVersion
    ) -> Union[PromptTemplate, ChatPromptTemplate]:
        # https://python.langchain.com/docs/concepts/prompt_templates/
        match prompt_version.type:
            case "text":
                return PromptTemplate.from_template(prompt_version.prompt[0]["content"])
            case "chat":
                chat_prompt = []
                for prompt in prompt_version.prompt:
                    if prompt["role"] == "placeholder":
                        chat_prompt.append(MessagesPlaceholder(prompt["content"]))
                    else:
                        chat_prompt.append(prompt)

                return ChatPromptTemplate(chat_prompt)

class AsyncPromptsResource(AsyncBaseResource):
    """Prompts resource for asynchronous operations."""

    def __init__(
        self,
        http_client: "AsyncHttpClient",
        config: "Config",
        cache: "Cache",
    ):
        """Initialize async prompts resource."""
        super().__init__(http_client, config, cache)
        self._resolved_project_id: str | None = None
        self._prompt_cache: dict[
            str, tuple[str, str]
        ] = {}  # {prompt_name: (prompt_id, prompt_type)}

    async def _get_project_id(self) -> str:
        """Get project ID, resolving from project_name if necessary."""
        # Return cached project_id if already resolved
        if self._resolved_project_id:
            return self._resolved_project_id

        # Use configured project_id if available
        if self._config.project_id:
            self._resolved_project_id = self._config.project_id
            return self._resolved_project_id

        # Resolve from project_name
        if self._config.project_name:
            # Query projects API to get project by name
            # API returns single project object when querying by name
            response = await self._http.get(
                "/projects", params={"name": self._config.project_name}
            )
            data = self._get_json(response)

            # API returns single project object directly
            if not data:
                from langprompt.exceptions import NotFoundError

                raise NotFoundError(f"Project not found: {self._config.project_name}")

            self._resolved_project_id = data["id"]
            return self._resolved_project_id

        # Neither project_id nor project_name is configured
        raise ValueError("Either project_id or project_name must be configured")

    async def _resolve_prompt_id(self, prompt_name: str) -> tuple[str, str]:
        """Resolve prompt name to prompt ID and type asynchronously.

        Args:
            prompt_name: Prompt name

        Returns:
            Tuple of (prompt_id, prompt_type)

        Raises:
            NotFoundError: If prompt not found
        """
        # Check cache first
        if prompt_name in self._prompt_cache:
            return self._prompt_cache[prompt_name]

        project_id = await self._get_project_id()
        response = await self._http.get(
            f"/projects/{project_id}/prompts", params={"name": prompt_name}
        )
        data = self._get_json(response)

        # Handle response format
        if isinstance(data, dict) and "id" in data:
            prompt_id = data["id"]
            prompt_type = data.get("type", "")
            self._prompt_cache[prompt_name] = (prompt_id, prompt_type)
            return prompt_id, prompt_type

        # If not a valid prompt object, it's not found
        from langprompt.exceptions import NotFoundError

        raise NotFoundError(f"Prompt not found: {prompt_name}")

    async def list(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> PagedResponse[Prompt]:
        """List all prompts in the project asynchronously.

        Args:
            limit: Maximum number of items to return
            offset: Number of items to skip

        Returns:
            PagedResponse of Prompts
        """
        params: dict[str, Any] = {
            "limit": limit,
            "offset": offset,
        }

        project_id = await self._get_project_id()
        response = await self._http.get(
            f"/projects/{project_id}/prompts", params=params
        )
        data = self._get_json(response)

        # Handle server response format
        prompts_list = data.get("prompts", data.get("items", []))
        total = data.get("total", 0)

        # Calculate pagination info
        has_next = offset + len(prompts_list) < total

        return PagedResponse[Prompt](
            items=[Prompt(**item) for item in prompts_list],
            total=total,
            limit=limit,
            offset=offset,
            has_next=has_next,
        )

    async def get(
        self,
        prompt_name: str,
        label: str | None = None,
        version: int | None = None,
    ) -> PromptVersion:
        """Get prompt version by label or version number asynchronously.

        Must provide either label OR version (not both).

        Args:
            prompt_name: Prompt name
            label: Version label (e.g., "production", "staging")
            version: Version number

        Returns:
            PromptVersion object

        Raises:
            ValueError: If neither or both label and version provided
            NotFoundError: If prompt/version not found
        """
        if (label is None and version is None) or (label and version):
            raise ValueError("Must provide exactly one of: label or version")

        # Build cache key
        identifier = label if label else str(version)
        cache_key = self._cache.make_key(
            self._config.project_id or "_",
            "version",
            prompt_name,
            identifier,
        )

        # Check cache
        cached = self._cache.get(cache_key)
        if cached:
            return PromptVersion(**cached)

        # Resolve prompt name to ID and get type
        project_id = await self._get_project_id()
        prompt_id, prompt_type = await self._resolve_prompt_id(prompt_name)

        # Build request with query parameters
        params = {}
        if label:
            params["label"] = label
        else:
            params["version"] = version

        response = await self._http.get(
            f"/projects/{project_id}/prompts/{prompt_id}/versions", params=params
        )
        data = self._get_json(response)

        # Add type if not present in response
        if "type" not in data:
            data["type"] = prompt_type

        # Cache result (version content is immutable, can cache longer)
        ttl = None if version else self._config.cache_ttl
        self._cache.set(cache_key, data, ttl=ttl)

        return PromptVersion(**data)

    async def get_prompt(
        self,
        prompt_name: str,
        label: str = "production",
        version: int | None = None,
    ) -> list[Any]:
        """Get prompt content asynchronously.

        Convenience method to get only the prompt field.

        Args:
            prompt_name: Prompt name
            label: Version label (default: "production")
            version: Version number (overrides label if provided)

        Returns:
            Prompt content list
        """
        prompt_version = await self.get(
            prompt_name=prompt_name,
            label=None if version else label,
            version=version,
        )
        return prompt_version.prompt
