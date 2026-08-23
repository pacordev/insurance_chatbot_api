"""FastAPI wrapper around the ins_chatbot core — see /health, /session, /chat."""

import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from bot.data import TermStore
from bot.dispatcher import Dispatcher
from bot.responses import render_welcome

from app.auth import require_api_key
from app.models import ChatRequest, ChatResponse, SessionRequest, SessionResponse
from app.sessions import SESSIONS, create_session

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    store = TermStore.load()
    app.state.dispatcher = Dispatcher(store)
    yield


app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

_origins = os.environ.get("ALLOWED_ORIGINS", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins.split(",")],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/session", response_model=SessionResponse, dependencies=[Depends(require_api_key)])
@limiter.limit("20/minute")
def start_session(payload: SessionRequest, request: Request):
    session_id, _ = create_session(payload.name, payload.is_newcomer)
    return SessionResponse(session_id=session_id, welcome_message=render_welcome(payload.name))


@app.post("/chat", response_model=ChatResponse, dependencies=[Depends(require_api_key)])
@limiter.limit("30/minute")
def chat(payload: ChatRequest, request: Request):
    state = SESSIONS.get(payload.session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Unknown session_id")
    reply, state = request.app.state.dispatcher.process_turn(payload.message, state)
    SESSIONS[payload.session_id] = state
    return ChatResponse(reply=reply)
