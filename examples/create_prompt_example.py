"""Example usage of create_prompt functionality."""

from langprompt import LangPrompt
from langprompt.exceptions import NotFoundError

# Initialize client
client = LangPrompt(
    project_name="my-project",
    api_key="your-api-key",
)

# Example 1: Create a new version for an existing prompt (text type)
print("Creating new version for existing prompt...")
text_version = client.prompts.create(
    name="event-planner",  # Assumes this prompt already exists
    prompt="你好{name}",
    type="text",
    metadata={"author": "example"},
    labels=["production"],
    commit_message="New version",
)
print(f"Created version {text_version.version}")
print(f"Content: {text_version.prompt}")

# Example 2: Create a new version for existing prompt (chat type)
print("\nCreating chat version for existing prompt...")
chat_version = client.prompts.create(
    name="assistant-chat",  # Assumes this prompt already exists
    prompt=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello {name}!"},
    ],
    type="chat",
    metadata={},
    labels=["production"],
    commit_message="New chat version",
)
print(f"Created version {chat_version.version}")
print(f"Messages: {len(chat_version.prompt)} messages")

# Example 3: Try to create version for non-existent prompt (will fail without force)
print("\nTrying to create version for non-existent prompt...")
try:
    client.prompts.create(
        name="nonexistent-prompt",
        prompt="Some content",
        type="text",
    )
except NotFoundError as e:
    print(f"Expected error: {e}")

# Example 4: Create prompt automatically with force=True
print("\nCreating prompt automatically with force=True...")
new_prompt = client.prompts.create(
    name="new-prompt",
    prompt="New prompt content",
    type="text",  # type is required when force=True and prompt doesn't exist
    labels=["development"],
    commit_message="Initial version",
    force=True,  # Will create the prompt if it doesn't exist
)
print(f"Created prompt with version {new_prompt.version}")

# Example 5: Create another version for existing prompt (no type needed)
print("\nCreating another version...")
another_version = client.prompts.create(
    name="new-prompt",
    prompt="Updated content",
    # type is optional when prompt already exists
    labels=["staging"],
    commit_message="Second version",
)
print(f"Created version {another_version.version}")

# Example 6: force=True without type raises error when prompt doesn't exist
print("\nTrying force=True without type for non-existent prompt...")
try:
    client.prompts.create(
        name="another-new-prompt",
        prompt="Content",
        force=True,
        # type is missing - will raise ValueError
    )
except ValueError as e:
    print(f"Expected error: {e}")

print("\nDone!")
