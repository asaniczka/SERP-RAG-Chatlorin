"""Contains models for generic messages"""

from pydantic import BaseModel, ConfigDict, Field


class BaseMessage(BaseModel):
    role: str = Field(
        description="Role of the message. Allows any arbitary string. For Gemini, anything except AI will be assigned to the role user",
        examples=["user", "ai", "model", "system"],
    )
    content: str


class BaseMessageLog(BaseModel):
    model_config = ConfigDict(extra="allow")

    messages: list[BaseMessage]
