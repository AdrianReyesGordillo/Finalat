"""Chat router — Fina autonomous LLM-driven financial advisor.

Provides endpoints compatible with the frontend's chat interface:
  GET  /api/chat/greeting  — get initial greeting message
  POST /api/chat/message   — send a message and get Fina's response

The conversation state (messages) is managed client-side in sessionStorage.
Each request sends the full conversation context so the LLM can reason
over the entire history.
"""

import logging
import time
import threading
from collections import deque

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.database import get_db
from backend.services.fina_agent import GREETING, fina_chat

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Per-user chat rate limiter: 20 messages per 60 seconds
_CHAT_MAX = 20
_CHAT_WINDOW = 60
_chat_requests: dict[str, deque] = {}
_chat_lock = threading.Lock()


def _chat_rate_limited(user_id: str) -> bool:
    """Check if user has exceeded chat rate limit (20 msg/min)."""
    now = time.time()
    with _chat_lock:
        if user_id not in _chat_requests:
            _chat_requests[user_id] = deque()
        timestamps = _chat_requests[user_id]
        cutoff = now - _CHAT_WINDOW
        while timestamps and timestamps[0] <= cutoff:
            timestamps.popleft()
        if len(timestamps) >= _CHAT_MAX:
            return True
        timestamps.append(now)
        return False


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ChatMessageRequest(BaseModel):
    """Request body for POST /api/chat/message."""

    user_message: str = Field(..., min_length=1, max_length=3000)
    state: dict = Field(default_factory=dict)
    current_step_index: int = 0


class ChatMessageResponse(BaseModel):
    """Response body matching the frontend's ChatResponse interface."""

    assistant_message: str
    investment_result: dict | None = None
    state: dict = Field(default_factory=dict)
    current_step_index: int = 0
    completed: bool = False
    redirect_to: str | None = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/greeting")
async def get_greeting():
    """Return Fina's initial greeting message."""
    return {"message": GREETING}


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    body: ChatMessageRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Process a user message through the Fina agent.

    The frontend sends the user's message plus the conversation state.
    The state dict contains the message history in a simplified format.
    We reconstruct the Bedrock Converse message format and run the agent.
    """
    # Per-user chat rate limit (stricter than global: 20 msg/min)
    user_id = getattr(request.state, "user_id", None)
    if user_id and _chat_rate_limited(user_id):
        return JSONResponse(
            status_code=429,
            content={"error": "Has enviado muchos mensajes. Espera un momento antes de continuar."}
        )
    state = body.state.copy()
    step_index = body.current_step_index

    # Reconstruct conversation history from state
    # The frontend stores messages as [{role, content}, ...] in state.messages
    history = state.get("messages", [])

    # Build Bedrock Converse format messages from history
    converse_messages = []
    for msg in history:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "assistant":
            converse_messages.append({
                "role": "assistant",
                "content": [{"text": content}],
            })
        else:
            converse_messages.append({
                "role": "user",
                "content": [{"text": content}],
            })

    # Sanitize user message (strip HTML tags)
    import re
    clean_message = re.sub(r'<[^>]+>', '', body.user_message).strip()
    if not clean_message:
        clean_message = body.user_message.strip()

    # Add the current user message
    converse_messages.append({
        "role": "user",
        "content": [{"text": clean_message}],
    })

    # Run the Fina agent
    user_name = state.pop("user_name", "")
    assistant_text, investment_result = await fina_chat(converse_messages, db, user_name=user_name)

    # Update state with the new messages for the frontend to persist
    history.append({"role": "user", "content": clean_message})
    history.append({"role": "assistant", "content": assistant_text})

    # Keep only last 20 messages to avoid token overflow
    if len(history) > 20:
        history = history[-20:]

    state["messages"] = history

    # Determine if the conversation produced a final result
    # NOTE: We intentionally do NOT set completed=True or redirect_to
    # because the agent presents results as part of the conversation text.
    # This keeps the user in the chat flow for follow-up questions.
    completed = False
    redirect_to = None

    logger.info(
        "Chat response: has_optimizer_result=%s, msg_len=%d",
        investment_result is not None, len(assistant_text),
    )

    return ChatMessageResponse(
        assistant_message=assistant_text,
        investment_result=investment_result,
        state=state,
        current_step_index=step_index + 1,
        completed=completed,
        redirect_to=redirect_to,
    )
