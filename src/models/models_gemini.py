"""
Contains all pydantic models of Google Gemeni
"""

from enum import Enum
from pydantic import BaseModel, ConfigDict


class GeminiRoles(Enum):
    """
    Enum representing the roles in the Gemini system.
    """

    USER = "user"
    AI = "model"


class ChatMessagePart(BaseModel):
    """
    Represents a part of a chat message.

    Attributes:
        text (str): The text content of the message part.
    """

    text: str


class ChatMessage(BaseModel):
    """
    Represents a chat message.

    Attributes:
        role (GeminiRoles): The role of the message sender.
        parts (list[ChatMessagePart]): The parts of the message.
    """

    model_config = ConfigDict(use_enum_values=True)

    role: GeminiRoles
    parts: list[ChatMessagePart]


class ChatHistory(BaseModel):
    """
    Represents the chat history for Gemini
    """

    contents: list[ChatMessage]


class GeminiKeywords(BaseModel):
    """Model to store keywords Gemini Suggests"""

    keywords: list[str]
