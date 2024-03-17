"""
Module contains all functions related to interacting with Google Gemini
"""

# pylint: disable = wrong-import-position
# pylint: disable = wrong-import-order

import os
import sys
import dotenv

sys.path.append(os.getcwd())
dotenv.load_dotenv()

import json
from enum import Enum

import httpx
from fastapi.exceptions import HTTPException

from src.models.models_gemini import (
    ChatMessage,
    ChatMessagePart,
    GeminiRoles,
    ChatHistory,
)
from src.models.messages import BaseMessageLog, BaseMessage


class AgentEnum(Enum):
    """Enum Class for local last message role tracking"""

    AI = 1
    USER = 2


def get_response_from_gemini(messages: ChatHistory) -> str | None:
    """
    Sends the chat history to Gemini and returns the response.

    Args:
        messages (ChatHistory): The chat history containing the conversation messages.

    Returns:
        str | None: The response generated by Gemini, or None if an error occurred.

    """

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.0-pro:generateContent?key={os.getenv('GOOGLE_GEMINI_KEY')}"
    payload = {
        "generationConfig": {
            "temperature": 0.9,
            "topK": 1,
            "topP": 1,
            "maxOutputTokens": 2048,
            "stopSequences": [],
        },
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_ONLY_HIGH",
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_ONLY_HIGH",
            },
        ],
    }

    payload.update(messages.model_dump())

    response = httpx.post(url, data=json.dumps(payload, default=str), timeout=120)

    try:
        reply = (
            response.json()
            .get("candidates")[0]
            .get("content")
            .get("parts")[0]
            .get("text")
        )
        return reply

    except Exception:
        print(f"Unable to extract message from AI: {response.text}")
        return None


def insert_proper_turn(agent: AgentEnum, chat_history: list):
    """
    Since Gemini requires messages to take turns, if the original message log doesn't have a proper turn, we insert a dummy one.

    Parameters:
    - agent (AgentEnum): The agent type (AI or USER).
    - chat_history (list): The chat history containing previous messages.

    Returns:
    None
    """

    if agent == AgentEnum.AI:
        chat_message = ChatMessage(
            role=GeminiRoles.AI,
            parts=[ChatMessagePart(text="How can I help you?")],
        )
        chat_history.append(chat_message)
    else:
        chat_message = ChatMessage(
            role=GeminiRoles.USER,
            parts=[ChatMessagePart(text="Cool, I'll tell you the task in a bit")],
        )
        chat_history.append(chat_message)


def construct_chat_history(messages: BaseMessageLog) -> ChatHistory:
    """
    Constructs a chat history in Gemini format.

    Args:
        messages (list[dict]): A list of messages containing information about each message.

    Returns:
        ChatHistory: The constructed chat history in Gemini format.
    """

    chat_history = []
    last_role: AgentEnum = None

    for message in messages.messages:
        if message.role.upper() == "AI":

            if last_role and last_role != AgentEnum.USER:
                insert_proper_turn(AgentEnum.USER, chat_history)

            message_text = ChatMessagePart(text=message.text)
            chat_message = ChatMessage(role=GeminiRoles.AI, parts=[message_text])
            chat_history.append(chat_message)
            last_role = AgentEnum.AI
        else:

            if last_role and last_role != AgentEnum.AI:
                insert_proper_turn(AgentEnum.AI, chat_history)

            message_text = ChatMessagePart(text=message.text)
            chat_message = ChatMessage(role=GeminiRoles.USER, parts=[message_text])
            chat_history.append(chat_message)
            last_role = AgentEnum.USER

    validated_chat_history = ChatHistory(contents=chat_history)

    return validated_chat_history


def handle_generating_response(messages: BaseMessageLog) -> str:
    """
    Main entrypoint for generating a response with gemini
    """
    history = construct_chat_history(messages)
    reply = get_response_from_gemini(history)

    if not reply:
        raise HTTPException(500, "Unable to get a proper response from Gemini")

    return reply


if __name__ == "__main__":

    msg_log = BaseMessageLog(
        messages=[
            BaseMessage(**{"role": "user", "text": "You're a helpful assistant"}),
            BaseMessage(**{"role": "user", "text": "Hello"}),
            BaseMessage(**{"role": "AI", "text": "Hello! How can I assist you today?"}),
            BaseMessage(**{"role": "user", "text": "What is 1+1?"}),
        ]
    )
    constructed_msg_history = construct_chat_history(msg_log)
    print(constructed_msg_history.model_dump())

    reply = get_response_from_gemini(constructed_msg_history)
    print(reply)