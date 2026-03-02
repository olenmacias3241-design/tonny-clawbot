"""Message models for the bot."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class Message(BaseModel):
    """Message model."""

    role: str = Field(..., description="Message role: user, assistant, or system")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = Field(default=None)


class Conversation(BaseModel):
    """Conversation model."""

    id: str = Field(..., description="Conversation ID")
    messages: List[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = Field(default=None)

    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add a message to the conversation."""
        message = Message(role=role, content=content, metadata=metadata)
        self.messages.append(message)
        self.updated_at = datetime.now()

    def get_recent_messages(self, count: int = 10) -> List[Message]:
        """Get recent messages from the conversation."""
        return self.messages[-count:]


class BotRequest(BaseModel):
    """Bot request model."""

    message: str = Field(..., description="User message")
    conversation_id: Optional[str] = Field(default=None)
    user_id: Optional[str] = Field(default=None)
    model: Optional[str] = Field(default=None, description="Override model, e.g. gpt-4o-mini, gpt-3.5-turbo")
    metadata: Optional[Dict[str, Any]] = Field(default=None)


class BotResponse(BaseModel):
    """Bot response model."""

    message: str = Field(..., description="Bot response message")
    conversation_id: str = Field(..., description="Conversation ID")
    metadata: Optional[Dict[str, Any]] = Field(default=None)
    error: Optional[str] = Field(default=None)
