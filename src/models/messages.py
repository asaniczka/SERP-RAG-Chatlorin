"""Contains models for generic messages"""

from pydantic import BaseModel


class BaseMessage(BaseModel):
    role: str
    text: str


class BaseMessageLog(BaseModel):
    messages: list[BaseMessage]
