"""API key check, applied as a FastAPI dependency on /session and /chat.

Not real access control — just enough to keep out bots/crawlers/casual
traffic and to have a clean revocation lever (change the env var, redeploy).
See ins_chatbot's handoff.md §2.56 for the full reasoning.
"""

import os

from fastapi import Header, HTTPException


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    expected = os.environ.get("API_KEY")
    if not expected or x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
