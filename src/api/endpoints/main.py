"""This module holds all FastAPI endpoints"""

from fastapi import FastAPI

from src.api.api_helpers.rag_cordinator import handle_reply_generation
from src.models.messages import BaseMessageLog

app = FastAPI()


@app.get("/")
def you_okay():
    """Check if the server is running"""
    return {"message": "ok"}


@app.post("/llm_reply")
def generate_reply(messages: BaseMessageLog):

    reply = handle_reply_generation(messages)
    return {"message": reply}
