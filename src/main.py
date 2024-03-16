"""This module holds all FastAPI endpoints"""

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def test_okay():
    """Check if the server is running"""
    return {"message": "ok"}
