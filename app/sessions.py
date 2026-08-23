"""In-memory session storage.

Deliberately simple: a plain dict, lost on restart/redeploy, doesn't survive
multiple instances. Good enough for a coworker-testing deployment, not a
permanent design — see ins_chatbot's handoff.md §2.56.
"""

import uuid

from bot.state import ConversationState

SESSIONS: dict[str, ConversationState] = {}


def create_session(name: str, is_newcomer: bool) -> tuple[str, ConversationState]:
    session_id = str(uuid.uuid4())
    state = ConversationState(user_name=name, is_newcomer=is_newcomer)
    SESSIONS[session_id] = state
    return session_id, state
