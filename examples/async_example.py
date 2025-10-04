"""Example usage of AsyncLangPrompt client."""

import asyncio

from langprompt import AsyncLangPrompt


async def main():
    """Demonstrate async client usage."""
    # Initialize async client - no need for async with!
    client = AsyncLangPrompt(
        project_name="my-project",
        api_key="your-api-key",
    )

    # Example 1: Get project information
    print("Getting project information...")
    project = await client.projects.get()
    print(f"Project: {project.name}")

    # Example 2: List prompts
    print("\nListing prompts...")
    prompts = await client.prompts.list(limit=10)
    print(f"Found {prompts.total} prompts")
    for prompt in prompts.items:
        print(f"  - {prompt.name}")

    # Example 3: Get prompt by label
    print("\nGetting prompt by label...")
    version = await client.prompts.get(
        prompt_name="greeting",
        label="production"
    )
    print(f"Version: {version.version}")
    print(f"Content: {version.prompt}")

    # Example 4: Get prompt by version number
    print("\nGetting prompt by version number...")
    version = await client.prompts.get(
        prompt_name="greeting",
        version=1
    )
    print(f"Version: {version.version}")

    # Example 5: Get prompt content directly
    print("\nGetting prompt content...")
    content = await client.prompts.get_prompt(
        prompt_name="greeting",
        label="production"
    )
    print(f"Content: {content}")

    # Example 6: Create a new version
    print("\nCreating new version...")
    new_version = await client.prompts.create(
        name="greeting",
        prompt="Hello {name}!",
        type="text",
        labels=["staging"],
        commit_message="Updated greeting"
    )
    print(f"Created version: {new_version.version}")

    # Optional: Explicit cleanup
    # await client.close()
    # Note: Resources are automatically cleaned up when the program exits


async def parallel_requests():
    """Demonstrate parallel async requests."""
    client = AsyncLangPrompt(
        project_name="my-project",
        api_key="your-api-key",
    )

    # Execute multiple requests in parallel
    results = await asyncio.gather(
        client.prompts.get("greeting", label="production"),
        client.prompts.get("farewell", label="production"),
        client.prompts.get("welcome", label="production"),
    )

    for i, result in enumerate(results, 1):
        print(f"Result {i}: version {result.version}")


async def multiple_clients():
    """Demonstrate using multiple clients."""
    # Create multiple clients for different projects
    client1 = AsyncLangPrompt(
        project_name="project-1",
        api_key="api-key-1",
    )

    client2 = AsyncLangPrompt(
        project_name="project-2",
        api_key="api-key-2",
    )

    # Use them independently
    project1 = await client1.projects.get()
    project2 = await client2.projects.get()

    print(f"Project 1: {project1.name}")
    print(f"Project 2: {project2.name}")

    # Both clients will be automatically cleaned up


if __name__ == "__main__":
    # Run the main example
    print("=== Basic Usage ===")
    asyncio.run(main())

    print("\n=== Parallel Requests ===")
    asyncio.run(parallel_requests())

    print("\n=== Multiple Clients ===")
    asyncio.run(multiple_clients())
