"""Request/response shapes for the three HTTP endpoints."""

from pydantic import BaseModel


class SessionRequest(BaseModel):
    name: str
    is_newcomer: bool


class SessionResponse(BaseModel):
    session_id: str
    welcome_message: str


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str
