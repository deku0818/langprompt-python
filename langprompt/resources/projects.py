"""Project resource module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from langprompt.models import Project, ProjectListResponse
from langprompt.resources.base import AsyncBaseResource, BaseResource

if TYPE_CHECKING:
    from langprompt.cache import Cache
    from langprompt.config import Config
    from langprompt.http import AsyncHttpClient, HttpClient


class ProjectsResource(BaseResource):
    """Projects resource for synchronous operations."""

    def __init__(
        self,
        http_client: "HttpClient",
        config: "Config",
        cache: "Cache",
    ):
        """Initialize projects resource."""
        super().__init__(http_client, config, cache)

    def get(
        self,
        project_id: str | None = None,
        project_name: str | None = None,
    ) -> Project:
        """Get project information.

        Args:
            project_id: Project ID (optional)
            project_name: Project name (optional)

        Priority: project_id > project_name > configured project_id > configured project_name

        Returns:
            Project object

        Raises:
            ValueError: If no project identifier provided
            NotFoundError: If project not found
            AuthenticationError: If authentication fails
            PermissionError: If permission denied
        """
        # Resolve which identifier to use
        pid = project_id or self._config.project_id
        pname = project_name or self._config.project_name

        # Must have either ID or name
        if not pid and not pname:
            raise ValueError("Either project_id or project_name must be provided")

        # Build query parameters (prefer ID over name)
        params = {}
        cache_key_parts = []

        if pid:
            params["project_id"] = pid
            cache_key_parts = [pid, "project"]
        else:
            params["name"] = pname
            cache_key_parts = ["_", "project_name", pname]

        # Check cache
        cache_key = self._cache.make_key(*cache_key_parts)
        cached = self._cache.get(cache_key)
        if cached:
            return Project(**cached)

        # Make API request with query parameters
        response = self._http.get("/projects", params=params)
        data = self._get_json(response)

        # API returns single project when querying by ID or name
        if not data:
            from langprompt.exceptions import NotFoundError
            identifier = pid if pid else pname
            raise NotFoundError(f"Project not found: {identifier}")

        # Cache result
        self._cache.set(cache_key, data)

        return Project(**data)

    def list(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> ProjectListResponse:
        """List all projects with pagination.

        Args:
            limit: Number of items per page (1-100, default: 20)
            offset: Number of items to skip (default: 0)

        Returns:
            ProjectListResponse with projects list and pagination info

        Raises:
            ValidationError: If parameters are invalid
            AuthenticationError: If authentication fails
        """
        # Validate parameters
        if limit < 1 or limit > 100:
            raise ValueError("limit must be between 1 and 100")
        if offset < 0:
            raise ValueError("offset must be non-negative")

        # Make API request
        params = {"limit": limit, "offset": offset}
        response = self._http.get("/projects", params=params)
        data = self._get_json(response)

        return ProjectListResponse(**data)


class AsyncProjectsResource(AsyncBaseResource):
    """Projects resource for asynchronous operations."""

    def __init__(
        self,
        http_client: "AsyncHttpClient",
        config: "Config",
        cache: "Cache",
    ):
        """Initialize async projects resource."""
        super().__init__(http_client, config, cache)

    async def get(
        self,
        project_id: str | None = None,
        project_name: str | None = None,
    ) -> Project:
        """Get project information asynchronously.

        Args:
            project_id: Project ID (optional)
            project_name: Project name (optional)

        Priority: project_id > project_name > configured project_id > configured project_name

        Returns:
            Project object

        Raises:
            ValueError: If no project identifier provided
            NotFoundError: If project not found
            AuthenticationError: If authentication fails
            PermissionError: If permission denied
        """
        # Resolve which identifier to use
        pid = project_id or self._config.project_id
        pname = project_name or self._config.project_name

        # Must have either ID or name
        if not pid and not pname:
            raise ValueError("Either project_id or project_name must be provided")

        # Build query parameters (prefer ID over name)
        params = {}
        cache_key_parts = []

        if pid:
            params["project_id"] = pid
            cache_key_parts = [pid, "project"]
        else:
            params["name"] = pname
            cache_key_parts = ["_", "project_name", pname]

        # Check cache
        cache_key = self._cache.make_key(*cache_key_parts)
        cached = self._cache.get(cache_key)
        if cached:
            return Project(**cached)

        # Make API request with query parameters
        response = await self._http.get("/projects", params=params)
        data = self._get_json(response)

        # API returns single project when querying by ID or name
        if not data:
            from langprompt.exceptions import NotFoundError
            identifier = pid if pid else pname
            raise NotFoundError(f"Project not found: {identifier}")

        # Cache result
        self._cache.set(cache_key, data)

        return Project(**data)

    async def list(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> ProjectListResponse:
        """List all projects with pagination asynchronously.

        Args:
            limit: Number of items per page (1-100, default: 20)
            offset: Number of items to skip (default: 0)

        Returns:
            ProjectListResponse with projects list and pagination info

        Raises:
            ValidationError: If parameters are invalid
            AuthenticationError: If authentication fails
        """
        # Validate parameters
        if limit < 1 or limit > 100:
            raise ValueError("limit must be between 1 and 100")
        if offset < 0:
            raise ValueError("offset must be non-negative")

        # Make API request
        params = {"limit": limit, "offset": offset}
        response = await self._http.get("/projects", params=params)
        data = self._get_json(response)

        return ProjectListResponse(**data)
