"""Tests for Claw Bot."""

import pytest
from src.models.message import BotRequest, Message, Conversation


def test_message_creation():
    """Test message creation."""
    message = Message(role="user", content="Hello")
    assert message.role == "user"
    assert message.content == "Hello"
    assert message.timestamp is not None


def test_conversation_creation():
    """Test conversation creation."""
    conversation = Conversation(id="test-123")
    assert conversation.id == "test-123"
    assert len(conversation.messages) == 0


def test_conversation_add_message():
    """Test adding messages to conversation."""
    conversation = Conversation(id="test-123")
    conversation.add_message(role="user", content="Hello")

    assert len(conversation.messages) == 1
    assert conversation.messages[0].role == "user"
    assert conversation.messages[0].content == "Hello"


def test_conversation_get_recent_messages():
    """Test getting recent messages."""
    conversation = Conversation(id="test-123")

    # Add multiple messages
    for i in range(15):
        conversation.add_message(role="user", content=f"Message {i}")

    # Get last 10 messages
    recent = conversation.get_recent_messages(count=10)
    assert len(recent) == 10
    assert recent[-1].content == "Message 14"


def test_bot_request_validation():
    """Test bot request validation."""
    request = BotRequest(message="Hello")
    assert request.message == "Hello"
    assert request.conversation_id is None
    assert request.user_id is None
