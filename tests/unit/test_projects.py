"""Unit tests for projects resource."""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from langprompt.cache import Cache
from langprompt.config import Config
from langprompt.exceptions import NotFoundError
from langprompt.models import Project, ProjectListResponse
from langprompt.resources.projects import AsyncProjectsResource, ProjectsResource


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client."""
    return Mock()


@pytest.fixture
def mock_async_http_client():
    """Create a mock async HTTP client."""
    client = Mock()
    # Make the get method async
    client.get = AsyncMock()
    return client


@pytest.fixture
def config():
    """Create a test config."""
    return Config(
        project_id="test-project-id",
        project_name="test-project",
        api_key="test-api-key",
    )


@pytest.fixture
def cache():
    """Create a test cache."""
    return Cache(enabled=False)


@pytest.fixture
def projects_resource(mock_http_client, config, cache):
    """Create a projects resource instance."""
    return ProjectsResource(mock_http_client, config, cache)


@pytest.fixture
def async_projects_resource(mock_async_http_client, config, cache):
    """Create an async projects resource instance."""
    return AsyncProjectsResource(mock_async_http_client, config, cache)


@pytest.fixture
def sample_project_data():
    """Sample project data."""
    return {
        "id": str(uuid4()),
        "name": "test-project",
        "description": "Test project description",
        "tags": ["tag1", "tag2"],
        "metadata": {"key": "value"},
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }


class TestProjectsResourceGet:
    """Tests for ProjectsResource.get() method."""

    def test_get_by_project_id_param(
        self, projects_resource, mock_http_client, sample_project_data
    ):
        """Test get project by project_id parameter."""
        # Setup mock
        mock_response = Mock()
        mock_response.json.return_value = {
            "success": True,
            "data": sample_project_data,
        }
        mock_http_client.get.return_value = mock_response

        # Call method
        project = projects_resource.get(project_id="custom-id")

        # Verify
        mock_http_client.get.assert_called_once_with(
            "/projects", params={"project_id": "custom-id"}
        )
        assert isinstance(project, Project)
        assert project.name == "test-project"

    def test_get_by_project_name_param(
        self, mock_http_client, cache, sample_project_data
    ):
        """Test get project by project_name parameter."""
        # Create config without project_id to avoid override
        config = Config(api_key="test-api-key")
        projects_resource = ProjectsResource(mock_http_client, config, cache)

        # Setup mock
        mock_response = Mock()
        mock_response.json.return_value = {
            "success": True,
            "data": sample_project_data,
        }
        mock_http_client.get.return_value = mock_response

        # Call method
        project = projects_resource.get(project_name="custom-project")

        # Verify
        mock_http_client.get.assert_called_once_with(
            "/projects", params={"name": "custom-project"}
        )
        assert isinstance(project, Project)
        assert project.name == "test-project"

    def test_get_uses_config_project_id(
        self, projects_resource, mock_http_client, sample_project_data
    ):
        """Test get project uses configured project_id."""
        # Setup mock
        mock_response = Mock()
        mock_response.json.return_value = {
            "success": True,
            "data": sample_project_data,
        }
        mock_http_client.get.return_value = mock_response

        # Call method without parameters
        project = projects_resource.get()

        # Verify - should use configured project_id
        mock_http_client.get.assert_called_once_with(
            "/projects", params={"project_id": "test-project-id"}
        )
        assert isinstance(project, Project)

    def test_get_uses_config_project_name(
        self, mock_http_client, cache, sample_project_data
    ):
        """Test get project uses configured project_name when no project_id."""
        # Create config with only project_name
        config = Config(project_name="test-project", api_key="test-api-key")
        projects_resource = ProjectsResource(mock_http_client, config, cache)

        # Setup mock
        mock_response = Mock()
        mock_response.json.return_value = {
            "success": True,
            "data": sample_project_data,
        }
        mock_http_client.get.return_value = mock_response

        # Call method
        project = projects_resource.get()

        # Verify - should use configured project_name
        mock_http_client.get.assert_called_once_with(
            "/projects", params={"name": "test-project"}
        )
        assert isinstance(project, Project)

    def test_get_prefers_id_over_name(
        self, projects_resource, mock_http_client, sample_project_data
    ):
        """Test that project_id is preferred over project_name."""
        # Setup mock
        mock_response = Mock()
        mock_response.json.return_value = {
            "success": True,
            "data": sample_project_data,
        }
        mock_http_client.get.return_value = mock_response

        # Call with both parameters
        project = projects_resource.get(
            project_id="id-param", project_name="name-param"
        )

        # Verify - should use project_id
        mock_http_client.get.assert_called_once_with(
            "/projects", params={"project_id": "id-param"}
        )
        assert isinstance(project, Project)

    def test_get_raises_error_when_no_identifier(
        self, mock_http_client, cache
    ):
        """Test get raises ValueError when no identifier provided."""
        # Create config without project_id or project_name
        config = Config(api_key="test-api-key")
        projects_resource = ProjectsResource(mock_http_client, config, cache)

        # Should raise ValueError
        with pytest.raises(ValueError, match="Either project_id or project_name"):
            projects_resource.get()

    def test_get_not_found(self, projects_resource, mock_http_client):
        """Test get raises NotFoundError when project not found."""
        # Setup mock to return None
        mock_response = Mock()
        mock_response.json.return_value = {
            "success": True,
            "data": None,
        }
        mock_http_client.get.return_value = mock_response

        # Should raise NotFoundError
        with pytest.raises(NotFoundError, match="Project not found"):
            projects_resource.get(project_id="nonexistent")

    def test_get_uses_cache(
        self, mock_http_client, config, sample_project_data
    ):
        """Test get uses cache when available."""
        # Create cache with enabled=True
        cache = Cache(enabled=True)
        projects_resource = ProjectsResource(mock_http_client, config, cache)

        # Setup mock
        mock_response = Mock()
        mock_response.json.return_value = {
            "success": True,
            "data": sample_project_data,
        }
        mock_http_client.get.return_value = mock_response

        # First call - should hit API
        project1 = projects_resource.get(project_id="test-id")
        assert mock_http_client.get.call_count == 1

        # Second call - should use cache
        project2 = projects_resource.get(project_id="test-id")
        assert mock_http_client.get.call_count == 1  # No additional call

        # Verify both return same data
        assert project1.name == project2.name


class TestProjectsResourceList:
    """Tests for ProjectsResource.list() method."""

    def test_list_default_params(self, projects_resource, mock_http_client):
        """Test list projects with default parameters."""
        # Setup mock
        mock_response = Mock()
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "projects": [],
                "total": 0,
                "limit": 20,
                "offset": 0,
            },
        }
        mock_http_client.get.return_value = mock_response

        # Call method
        result = projects_resource.list()

        # Verify
        mock_http_client.get.assert_called_once_with(
            "/projects", params={"limit": 20, "offset": 0}
        )
        assert isinstance(result, ProjectListResponse)
        assert result.total == 0
        assert result.limit == 20
        assert result.offset == 0

    def test_list_custom_params(self, projects_resource, mock_http_client):
        """Test list projects with custom parameters."""
        # Setup mock
        mock_response = Mock()
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "projects": [],
                "total": 100,
                "limit": 50,
                "offset": 10,
            },
        }
        mock_http_client.get.return_value = mock_response

        # Call method
        result = projects_resource.list(limit=50, offset=10)

        # Verify
        mock_http_client.get.assert_called_once_with(
            "/projects", params={"limit": 50, "offset": 10}
        )
        assert result.limit == 50
        assert result.offset == 10

    def test_list_validates_limit(self, projects_resource):
        """Test list validates limit parameter."""
        # Test limit too small
        with pytest.raises(ValueError, match="limit must be between 1 and 100"):
            projects_resource.list(limit=0)

        # Test limit too large
        with pytest.raises(ValueError, match="limit must be between 1 and 100"):
            projects_resource.list(limit=101)

    def test_list_validates_offset(self, projects_resource):
        """Test list validates offset parameter."""
        with pytest.raises(ValueError, match="offset must be non-negative"):
            projects_resource.list(offset=-1)

    def test_list_with_projects(
        self, projects_resource, mock_http_client, sample_project_data
    ):
        """Test list returns projects correctly."""
        # Setup mock
        mock_response = Mock()
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "projects": [sample_project_data, sample_project_data],
                "total": 2,
                "limit": 20,
                "offset": 0,
            },
        }
        mock_http_client.get.return_value = mock_response

        # Call method
        result = projects_resource.list()

        # Verify
        assert len(result.projects) == 2
        assert all(isinstance(p, Project) for p in result.projects)
        assert result.total == 2


class TestAsyncProjectsResourceGet:
    """Tests for AsyncProjectsResource.get() method."""

    @pytest.mark.asyncio
    async def test_get_by_project_id_param(
        self, async_projects_resource, mock_async_http_client, sample_project_data
    ):
        """Test async get project by project_id parameter."""
        # Setup mock
        mock_response = Mock()
        mock_response.json.return_value = {
            "success": True,
            "data": sample_project_data,
        }
        mock_async_http_client.get.return_value = mock_response

        # Call method
        project = await async_projects_resource.get(project_id="custom-id")

        # Verify
        mock_async_http_client.get.assert_called_once_with(
            "/projects", params={"project_id": "custom-id"}
        )
        assert isinstance(project, Project)
        assert project.name == "test-project"

    @pytest.mark.asyncio
    async def test_get_by_project_name_param(
        self, mock_async_http_client, cache, sample_project_data
    ):
        """Test async get project by project_name parameter."""
        # Create config without project_id to avoid override
        config = Config(api_key="test-api-key")
        async_projects_resource = AsyncProjectsResource(
            mock_async_http_client, config, cache
        )

        # Setup mock
        mock_response = Mock()
        mock_response.json.return_value = {
            "success": True,
            "data": sample_project_data,
        }
        mock_async_http_client.get.return_value = mock_response

        # Call method
        project = await async_projects_resource.get(project_name="custom-project")

        # Verify
        mock_async_http_client.get.assert_called_once_with(
            "/projects", params={"name": "custom-project"}
        )
        assert isinstance(project, Project)

    @pytest.mark.asyncio
    async def test_get_raises_error_when_no_identifier(
        self, mock_async_http_client, cache
    ):
        """Test async get raises ValueError when no identifier provided."""
        # Create config without project_id or project_name
        config = Config(api_key="test-api-key")
        async_projects_resource = AsyncProjectsResource(
            mock_async_http_client, config, cache
        )

        # Should raise ValueError
        with pytest.raises(ValueError, match="Either project_id or project_name"):
            await async_projects_resource.get()


class TestAsyncProjectsResourceList:
    """Tests for AsyncProjectsResource.list() method."""

    @pytest.mark.asyncio
    async def test_list_default_params(
        self, async_projects_resource, mock_async_http_client
    ):
        """Test async list projects with default parameters."""
        # Setup mock
        mock_response = Mock()
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "projects": [],
                "total": 0,
                "limit": 20,
                "offset": 0,
            },
        }
        mock_async_http_client.get.return_value = mock_response

        # Call method
        result = await async_projects_resource.list()

        # Verify
        mock_async_http_client.get.assert_called_once_with(
            "/projects", params={"limit": 20, "offset": 0}
        )
        assert isinstance(result, ProjectListResponse)
        assert result.total == 0

    @pytest.mark.asyncio
    async def test_list_validates_limit(self, async_projects_resource):
        """Test async list validates limit parameter."""
        with pytest.raises(ValueError, match="limit must be between 1 and 100"):
            await async_projects_resource.list(limit=0)
