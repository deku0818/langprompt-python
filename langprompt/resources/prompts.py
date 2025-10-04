"""Prompts resource module."""

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Union, Literal

from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    PromptTemplate,
)

from langprompt.models import PagedResponse, Prompt, PromptVersion
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

    def _transform_prompt_content(
        self,
        prompt: str | list[dict],
        type: Literal['chat', 'text'] | None = None,
    ) -> list[dict]:
        """Transform prompt content to standardized format.

        Args:
            prompt: Prompt content (string for text type, list of dicts for chat type)
            type: Prompt type ("text" or "chat")

        Returns:
            Standardized prompt content as list of dicts

        Raises:
            ValidationError: If prompt type is invalid or prompt format is wrong
        """
        from langprompt.exceptions import ValidationError

        # Validate type if provided
        if type is not None and type not in ("text", "chat"):
            raise ValidationError(f"Invalid prompt type: {type}. Must be 'text' or 'chat'")

        # Transform prompt content based on type
        match type:
            case "text":
                if not isinstance(prompt, str):
                    raise ValidationError("Prompt must be a string when type='text'")
                return [{"role": "user", "content": prompt}]
            case "chat":
                if not isinstance(prompt, list):
                    raise ValidationError("Prompt must be a list when type='chat'")
                return prompt
            case _:
                # Type not specified, auto-detect based on prompt format
                if isinstance(prompt, str):
                    return [{"role": "user", "content": prompt}]
                else:
                    return prompt

    def _create_version(
        self,
        project_id: str,
        prompt_id: str,
        prompt_name: str,
        prompt_content: list[dict],
        metadata: dict[str, Any] | None = None,
        labels: list[str] | None = None,
        commit_message: str | None = None,
    ) -> PromptVersion:
        """Create a new version for an existing prompt.

        Args:
            project_id: Project ID
            prompt_id: Prompt ID
            prompt_name: Prompt name (for cache clearing)
            prompt_content: Standardized prompt content
            metadata: Optional metadata dict
            labels: Optional list of labels for the version
            commit_message: Optional commit message

        Returns:
            PromptVersion object
        """
        version_data = {
            "prompt": prompt_content,
            "labels": labels or [],
            "metadata": metadata or {},
            "commit_message": commit_message or "New version",
        }
        response = self._http.post(
            f"/projects/{project_id}/prompts/{prompt_id}/versions",
            json=version_data,
        )
        data = self._get_json(response)

        # Clear cache for this prompt
        if prompt_name in self._prompt_cache:
            del self._prompt_cache[prompt_name]

        return PromptVersion(**data)

    def _create_prompt_with_version(
        self,
        project_id: str,
        name: str,
        type: Literal['chat', 'text'],
        prompt_content: list[dict],
        metadata: dict[str, Any] | None = None,
        labels: list[str] | None = None,
        commit_message: str | None = None,
    ) -> PromptVersion:
        """Create a new prompt and its initial version.

        Args:
            project_id: Project ID
            name: Prompt name
            type: Prompt type ("text" or "chat")
            prompt_content: Standardized prompt content
            metadata: Optional metadata dict
            labels: Optional list of labels for the version
            commit_message: Optional commit message

        Returns:
            PromptVersion object
        """
        # Step 1: Create prompt
        prompt_data = {
            "name": name,
            "type": type,
            "description": "",
            "tags": [],
        }
        prompt_response = self._http.post(
            f"/projects/{project_id}/prompts",
            json=prompt_data,
        )
        prompt_result = self._get_json(prompt_response)
        created_prompt_id = prompt_result["id"]

        # Step 2: Create initial version
        version_data = {
            "prompt": prompt_content,
            "labels": labels or [],
            "metadata": metadata or {},
            "commit_message": commit_message or "Initial version",
        }
        version_response = self._http.post(
            f"/projects/{project_id}/prompts/{created_prompt_id}/versions",
            json=version_data,
        )
        version_data = self._get_json(version_response)

        # Clear cache
        if name in self._prompt_cache:
            del self._prompt_cache[name]

        return PromptVersion(**version_data)

    def create(
        self,
        name: str,
        prompt: str | list[dict],
        type: Literal['chat', 'text'] | None = None,
        metadata: dict[str, Any] | None = None,
        labels: list[str] | None = None,
        commit_message: str | None = None,
        force: bool = False,
    ) -> PromptVersion:
        """Create a new prompt version (and prompt if needed with force=True).

        This method creates a new version for an existing prompt. If the prompt
        doesn't exist and force=True, it will create the prompt first.

        Args:
            name: Prompt name
            prompt: Prompt content (string for text type, list of dicts for chat type)
            type: Prompt type ("text" or "chat"), required when force=True and prompt doesn't exist
            metadata: Optional metadata dict
            labels: Optional list of labels for the version
            commit_message: Optional commit message
            force: If True, create prompt if it doesn't exist (requires type parameter)

        Returns:
            PromptVersion object

        Raises:
            ValidationError: If prompt type is invalid or prompt format is wrong
            NotFoundError: If prompt doesn't exist and force=False
            ValueError: If force=True but type is not provided when prompt doesn't exist
        """
        from langprompt.exceptions import NotFoundError

        # Transform prompt content to standardized format
        prompt_content = self._transform_prompt_content(prompt, type)

        project_id = self._get_project_id()

        # Check if prompt exists
        try:
            prompt_id, _ = self._resolve_prompt_id(name)
        except NotFoundError:
            prompt_id = None

        if prompt_id:
            # Create new version for existing prompt
            return self._create_version(
                project_id=project_id,
                prompt_id=prompt_id,
                prompt_name=name,
                prompt_content=prompt_content,
                metadata=metadata,
                labels=labels,
                commit_message=commit_message,
            )
        else:
            # Prompt doesn't exist
            if not force:
                raise NotFoundError(
                    f"Prompt '{name}' not found. Use force=True to create it automatically."
                )

            # force=True, create prompt first, then create version
            if type is None:
                raise ValueError(
                    "Parameter 'type' is required when force=True and prompt doesn't exist"
                )

            return self._create_prompt_with_version(
                project_id=project_id,
                name=name,
                type=type,
                prompt_content=prompt_content,
                metadata=metadata,
                labels=labels,
                commit_message=commit_message,
            )

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

        Raises:
            ValidationError: If parameters invalid
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
        prompt_version = await self.get(
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

    def _transform_prompt_content(
        self,
        prompt: str | list[dict],
        type: Literal['chat', 'text'] | None = None,
    ) -> list[dict]:
        """Transform prompt content to standardized format.

        Args:
            prompt: Prompt content (string for text type, list of dicts for chat type)
            type: Prompt type ("text" or "chat")

        Returns:
            Standardized prompt content as list of dicts

        Raises:
            ValidationError: If prompt type is invalid or prompt format is wrong
        """
        from langprompt.exceptions import ValidationError

        # Validate type if provided
        if type is not None and type not in ("text", "chat"):
            raise ValidationError(f"Invalid prompt type: {type}. Must be 'text' or 'chat'")

        # Transform prompt content based on type
        match type:
            case "text":
                if not isinstance(prompt, str):
                    raise ValidationError("Prompt must be a string when type='text'")
                return [{"role": "user", "content": prompt}]
            case "chat":
                if not isinstance(prompt, list):
                    raise ValidationError("Prompt must be a list when type='chat'")
                return prompt
            case _:
                # Type not specified, auto-detect based on prompt format
                if isinstance(prompt, str):
                    return [{"role": "user", "content": prompt}]
                else:
                    return prompt

    async def _create_version(
        self,
        project_id: str,
        prompt_id: str,
        prompt_name: str,
        prompt_content: list[dict],
        metadata: dict[str, Any] | None = None,
        labels: list[str] | None = None,
        commit_message: str | None = None,
    ) -> PromptVersion:
        """Create a new version for an existing prompt asynchronously.

        Args:
            project_id: Project ID
            prompt_id: Prompt ID
            prompt_name: Prompt name (for cache clearing)
            prompt_content: Standardized prompt content
            metadata: Optional metadata dict
            labels: Optional list of labels for the version
            commit_message: Optional commit message

        Returns:
            PromptVersion object
        """
        version_data = {
            "prompt": prompt_content,
            "labels": labels or [],
            "metadata": metadata or {},
            "commit_message": commit_message or "New version",
        }
        response = await self._http.post(
            f"/projects/{project_id}/prompts/{prompt_id}/versions",
            json=version_data,
        )
        data = self._get_json(response)

        # Clear cache for this prompt
        if prompt_name in self._prompt_cache:
            del self._prompt_cache[prompt_name]

        return PromptVersion(**data)

    async def _create_prompt_with_version(
        self,
        project_id: str,
        name: str,
        type: Literal['chat', 'text'],
        prompt_content: list[dict],
        metadata: dict[str, Any] | None = None,
        labels: list[str] | None = None,
        commit_message: str | None = None,
    ) -> PromptVersion:
        """Create a new prompt and its initial version asynchronously.

        Args:
            project_id: Project ID
            name: Prompt name
            type: Prompt type ("text" or "chat")
            prompt_content: Standardized prompt content
            metadata: Optional metadata dict
            labels: Optional list of labels for the version
            commit_message: Optional commit message

        Returns:
            PromptVersion object
        """
        # Step 1: Create prompt
        prompt_data = {
            "name": name,
            "type": type,
            "description": "",
            "tags": [],
        }
        prompt_response = await self._http.post(
            f"/projects/{project_id}/prompts",
            json=prompt_data,
        )
        prompt_result = self._get_json(prompt_response)
        created_prompt_id = prompt_result["id"]

        # Step 2: Create initial version
        version_data = {
            "prompt": prompt_content,
            "labels": labels or [],
            "metadata": metadata or {},
            "commit_message": commit_message or "Initial version",
        }
        version_response = await self._http.post(
            f"/projects/{project_id}/prompts/{created_prompt_id}/versions",
            json=version_data,
        )
        version_data = self._get_json(version_response)

        # Clear cache
        if name in self._prompt_cache:
            del self._prompt_cache[name]

        return PromptVersion(**version_data)

    async def create(
        self,
        name: str,
        prompt: str | list[dict],
        type: Literal['chat', 'text'] | None = None,
        metadata: dict[str, Any] | None = None,
        labels: list[str] | None = None,
        commit_message: str | None = None,
        force: bool = False,
    ) -> PromptVersion:
        """Create a new prompt version (and prompt if needed with force=True) asynchronously.

        This method creates a new version for an existing prompt. If the prompt
        doesn't exist and force=True, it will create the prompt first.

        Args:
            name: Prompt name
            prompt: Prompt content (string for text type, list of dicts for chat type)
            type: Prompt type ("text" or "chat"), required when force=True and prompt doesn't exist
            metadata: Optional metadata dict
            labels: Optional list of labels for the version
            commit_message: Optional commit message
            force: If True, create prompt if it doesn't exist (requires type parameter)

        Returns:
            PromptVersion object

        Raises:
            ValidationError: If prompt type is invalid or prompt format is wrong
            NotFoundError: If prompt doesn't exist and force=False
            ValueError: If force=True but type is not provided when prompt doesn't exist
        """
        from langprompt.exceptions import NotFoundError

        # Transform prompt content to standardized format
        prompt_content = self._transform_prompt_content(prompt, type)

        project_id = await self._get_project_id()

        # Check if prompt exists
        try:
            prompt_id, _ = await self._resolve_prompt_id(name)
        except NotFoundError:
            prompt_id = None

        if prompt_id:
            # Create new version for existing prompt
            return await self._create_version(
                project_id=project_id,
                prompt_id=prompt_id,
                prompt_name=name,
                prompt_content=prompt_content,
                metadata=metadata,
                labels=labels,
                commit_message=commit_message,
            )
        else:
            # Prompt doesn't exist
            if not force:
                raise NotFoundError(
                    f"Prompt '{name}' not found. Use force=True to create it automatically."
                )

            # force=True, create prompt first, then create version
            if type is None:
                raise ValueError(
                    "Parameter 'type' is required when force=True and prompt doesn't exist"
                )

            return await self._create_prompt_with_version(
                project_id=project_id,
                name=name,
                type=type,
                prompt_content=prompt_content,
                metadata=metadata,
                labels=labels,
                commit_message=commit_message,
            )
