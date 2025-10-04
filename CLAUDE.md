# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LangPrompt Python SDK is the official Python client library for LangPrompt - a prompt management system combining GitHub-like version control with Apollo-like configuration management. This SDK focuses on **prompt retrieval and usage**, not management (which is handled by the Web UI).

### Key Concepts

**Data Hierarchy**:
```
Project -> Prompt -> Version
```

**Version Management**:
- **Immutable fields**: `content`, `version`, `commit_message`, `created_at` (Git-like immutability)
- **Mutable fields**: `labels`, `metadata` (can be updated after creation)
- **Label uniqueness**: Each label can only point to one version per prompt
- **Common labels**: `production`, `staging`, `development`, `deprecated`, `hotfix`

**Prompt Naming**: Supports categorization like `category/prompt_name` (similar to object storage paths)

## Development Commands

### Setup
```bash
# Install dependencies (recommended)
uv sync

# Alternative with pip
pip install -e ".[dev]"
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_projects.py

# Run with coverage report
pytest --cov=langprompt --cov-report=html
```

## Architecture

### Module Structure

The SDK uses a **resource namespace pattern** for API organization:

```
langprompt/
├── client.py           # Main LangPrompt client
├── resources/          # Resource modules (projects, prompts, versions)
├── models/             # Pydantic data models
├── http/               # HTTP client with retry logic
├── exceptions.py       # Exception hierarchy
├── cache.py            # Optional caching (default: disabled)
└── config.py           # Configuration management
```

### API Access Pattern

```python
client.projects.get()                          # Get current project
client.prompts.list()                          # List all prompts
client.prompts.list(name="greeting")           # Filter by name
client.prompts.get(name="greeting", label="production")  # Get prompt version
client.prompts.get_prompt(name="greeting", label="production")  # Get prompt content
client.prompts.get(prompt_name="greeting", version=3)    # Get specific version
client.prompts.list(prompt_name="greeting")    # List versions for prompt
```

**Important**: When using `client.prompts.get()`, must provide either `label` OR `version` to ensure uniqueness.

### Authentication

**API Key Only** (no JWT support):
- SDK uses API Key authentication via `X-API-Key` header
- Priority: constructor param -> `LANGPROMPT_API_KEY` env var -> config file

### Name vs ID Resolution

- SDK supports both `name` and `id` parameters for resources
- When `name` is provided, SDK automatically converts to `id` for API queries
- Direct `id` usage is more performant (skips name resolution step)
- Parameter naming: `project_id`/`project_name`, `prompt_id`/`prompt_name`, `version` (integer)

### Synchronous and Asynchronous APIs

The SDK provides both sync and async APIs:
- `LangPrompt` - synchronous client
- `AsyncLangPrompt` - asynchronous client

### Error Handling

Exception hierarchy:
```
LangPromptError (base)
├── AuthenticationError (401)
├── PermissionError (403)
├── NotFoundError (404)
├── ValidationError (422)
├── RateLimitError (429)
├── ServerError (5xx)
├── NetworkError
└── TimeoutError
```

### Retry Mechanism

- **Default retries**: 5xx errors, timeouts, 429 rate limits
- **No retries**: 4xx client errors (except 429), auth/permission errors
- **Strategy**: Exponential backoff with jitter: `min(retry_delay * 2^n + random(0,1), max_delay)`

## Design Documents

- **SDK Design**: `docs/langprompt sdk设计文档.md` - Complete SDK architecture and design decisions
- **Server Design**: `docs/langprompt设计文档.md` - Overall system design including server, frontend, and SDK

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LANGPROMPT_PROJECT_NAME` | Default project name | - |
| `LANGPROMPT_PROJECT_ID` | Default project ID (higher priority) | - |
| `LANGPROMPT_API_KEY` | API Key for authentication | - |
| `LANGPROMPT_API_URL` | API base URL | `https://api.langprompt.com/api/v1` |

## Configuration Priority

From highest to lowest:
1. Constructor parameters
2. Environment variables
3. Project-level config (`./.langprompt`)
4. User-level config (`~/.langprompt/config`)
5. Default values

## Python Version Requirements

- **Minimum**: Python 3.11+
- **Recommended**: Python 3.12+
- **Tested**: 3.11, 3.12, 3.13

## Core Dependencies

- `httpx` - Modern HTTP client (sync/async support)
- `pydantic` - Data validation and models

## SDK Scope

**In Scope**:
- Get project information
- Query prompts and versions
- Retrieve prompt content by label or version number
- Local caching (optional)

**Out of Scope** (handled by Web UI):
- Project creation/configuration
- Prompt content editing
- Version management and publishing
- Member and permission management

## Important Notes

- Default behavior: caching is **disabled** to ensure data freshness
- All requests use HTTPS; HTTP is rejected unless explicitly allowed
- API Keys inherit the user's highest permission level in the project
- Version content is immutable once created (Git-like behavior)
- Labels can be moved between versions, but only one version per label per prompt

- uv 管理python的所有依赖，python路径为/langprompt-python//.venv/bin/python
- 当更新依赖时尽可能避免直接修改pyproject.toml，而是通过终端使用uv来进行安装升级删除等操作
- 遵循驱动测试开发原则（TDD），所有的开发都需要对应的测试