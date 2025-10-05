"""Tests for convert_messages_with_placeholder function."""

import pytest
from langchain_core.prompts import MessagesPlaceholder

from langprompt.resources.prompts import convert_messages_with_placeholder


class TestConvertMessagesWithPlaceholder:
    """Test cases for convert_messages_with_placeholder."""

    def test_messagesplaceholder_object(self):
        """Test conversion of MessagesPlaceholder object."""
        messages = [MessagesPlaceholder("history")]
        result = convert_messages_with_placeholder(messages)

        assert result == [{"role": "placeholder", "content": "history"}]

    def test_placeholder_tuple_format(self):
        """Test conversion of ("placeholder", "variable_name") tuple."""
        messages = [("placeholder", "history")]
        result = convert_messages_with_placeholder(messages)

        assert result == [{"role": "placeholder", "content": "history"}]

    def test_placeholder_dict_format(self):
        """Test conversion of dict with role="placeholder"."""
        messages = [{"role": "placeholder", "content": "history"}]
        result = convert_messages_with_placeholder(messages)

        assert result == [{"role": "placeholder", "content": "history"}]

    def test_mixed_messages_with_placeholder(self):
        """Test conversion of mixed message types including placeholders."""
        messages = [
            ("system", "You are a helpful assistant"),
            MessagesPlaceholder("history"),
            ("user", "Hello"),
        ]
        result = convert_messages_with_placeholder(messages)

        assert len(result) == 3
        assert result[0] == {"role": "system", "content": "You are a helpful assistant"}
        assert result[1] == {"role": "placeholder", "content": "history"}
        assert result[2] == {"role": "user", "content": "Hello"}

    def test_single_placeholder_message(self):
        """Test conversion of a single placeholder message (not in a list)."""
        message = MessagesPlaceholder("history")
        result = convert_messages_with_placeholder(message)

        assert result == [{"role": "placeholder", "content": "history"}]

    def test_single_regular_message(self):
        """Test conversion of a single regular message."""
        message = ("user", "Hello")
        result = convert_messages_with_placeholder(message)

        assert result == [{"role": "user", "content": "Hello"}]

    def test_multiple_placeholders(self):
        """Test conversion with multiple placeholders."""
        messages = [
            MessagesPlaceholder("context"),
            ("user", "Question"),
            MessagesPlaceholder("history"),
        ]
        result = convert_messages_with_placeholder(messages)

        assert len(result) == 3
        assert result[0] == {"role": "placeholder", "content": "context"}
        assert result[1] == {"role": "user", "content": "Question"}
        assert result[2] == {"role": "placeholder", "content": "history"}

    def test_all_three_placeholder_formats(self):
        """Test all three placeholder formats in one call."""
        messages = [
            MessagesPlaceholder("placeholder1"),
            ("placeholder", "placeholder2"),
            {"role": "placeholder", "content": "placeholder3"},
            ("user", "Message"),
        ]
        result = convert_messages_with_placeholder(messages)

        assert len(result) == 4
        assert result[0] == {"role": "placeholder", "content": "placeholder1"}
        assert result[1] == {"role": "placeholder", "content": "placeholder2"}
        assert result[2] == {"role": "placeholder", "content": "placeholder3"}
        assert result[3] == {"role": "user", "content": "Message"}

    def test_dict_message(self):
        """Test conversion of dict-format messages."""
        messages = [
            {"role": "system", "content": "System message"},
            {"role": "user", "content": "User message"},
        ]
        result = convert_messages_with_placeholder(messages)

        assert len(result) == 2
        assert result[0] == {"role": "system", "content": "System message"}
        assert result[1] == {"role": "user", "content": "User message"}

    def test_string_message(self):
        """Test conversion of string messages."""
        # Single string becomes HumanMessage
        message = "Hello world"
        result = convert_messages_with_placeholder(message)

        assert len(result) == 1
        assert result[0]["role"] == "user"
        assert result[0]["content"] == "Hello world"

    def test_empty_list(self):
        """Test conversion of empty list."""
        messages = []
        result = convert_messages_with_placeholder(messages)

        assert result == []

    def test_tuple_not_placeholder(self):
        """Test that non-placeholder tuples are converted normally."""
        messages = [
            ("system", "System"),
            ("user", "User"),
            ("assistant", "Assistant"),
        ]
        result = convert_messages_with_placeholder(messages)

        assert len(result) == 3
        assert result[0]["role"] == "system"
        assert result[1]["role"] == "user"
        assert result[2]["role"] == "assistant"

    def test_complex_content_blocks(self):
        """Test messages with complex content blocks."""
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What's in this image?"},
                    {
                        "type": "image_url",
                        "image_url": {"url": "data:image/png;base64,iVBORw0KGgo="},
                    },
                ],
            },
            MessagesPlaceholder("history"),
        ]
        result = convert_messages_with_placeholder(messages)

        assert len(result) == 2
        assert result[0]["role"] == "user"
        assert isinstance(result[0]["content"], list)
        assert result[1] == {"role": "placeholder", "content": "history"}

    def test_placeholder_with_special_variable_names(self):
        """Test placeholders with various variable name formats."""
        messages = [
            MessagesPlaceholder("simple"),
            MessagesPlaceholder("with_underscore"),
            MessagesPlaceholder("with123numbers"),
        ]
        result = convert_messages_with_placeholder(messages)

        assert result[0]["content"] == "simple"
        assert result[1]["content"] == "with_underscore"
        assert result[2]["content"] == "with123numbers"


class TestGetLangchainPromptValidation:
    """Test validation in _get_langchain_prompt method."""

    def test_invalid_prompt_format_not_dict(self, client):
        """Test that non-dict prompt items raise ValueError."""
        from langprompt.models import PromptVersion
        from datetime import datetime
        from uuid import uuid4

        # Create a PromptVersion with invalid format (string instead of dict)
        version = PromptVersion(
            id=uuid4(),
            prompt_id=uuid4(),
            version=1,
            prompt=["invalid string"],  # Should be dict
            type="chat",
            labels=[],
            metadata={},
            commit_message="test",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        with pytest.raises(ValueError, match="Invalid prompt format: expected dict"):
            client.prompts._get_langchain_prompt(version)

    def test_missing_role_field(self, client):
        """Test that missing 'role' field raises ValueError."""
        from langprompt.models import PromptVersion
        from datetime import datetime
        from uuid import uuid4

        # Create a PromptVersion with missing 'role' field
        version = PromptVersion(
            id=uuid4(),
            prompt_id=uuid4(),
            version=1,
            prompt=[{"content": "Hello"}],  # Missing 'role'
            type="chat",
            labels=[],
            metadata={},
            commit_message="test",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        with pytest.raises(ValueError, match="Invalid prompt format: missing 'role' field"):
            client.prompts._get_langchain_prompt(version)

    def test_placeholder_missing_content_field(self, client):
        """Test that placeholder without 'content' field raises ValueError."""
        from langprompt.models import PromptVersion
        from datetime import datetime
        from uuid import uuid4

        # Create a PromptVersion with placeholder missing 'content' field
        version = PromptVersion(
            id=uuid4(),
            prompt_id=uuid4(),
            version=1,
            prompt=[{"role": "placeholder"}],  # Missing 'content'
            type="chat",
            labels=[],
            metadata={},
            commit_message="test",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        with pytest.raises(ValueError, match="Invalid placeholder format: missing 'content' field"):
            client.prompts._get_langchain_prompt(version)
