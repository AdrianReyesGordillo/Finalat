"""Chat router — Fina autonomous LLM-driven financial advisor.

Provides endpoints compatible with the frontend's chat interface:
  GET  /api/chat/greeting  — get initial greeting message
  POST /api/chat/message   — send a message and get Fina's response

The conversation state (messages) is managed client-side in sessionStorage.
Each request sends the full conversation context so the LLM can reason
over the entire history.
"""

import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.database import get_db
from backend.services.fina_agent import GREETING, fina_chat

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


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
    db: AsyncSession = Depends(get_db),
):
    """Process a user message through the Fina agent.

    The frontend sends the user's message plus the conversation state.
    The state dict contains the message history in a simplified format.
    We reconstruct the Bedrock Converse message format and run the agent.
    """
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

    # Add the current user message
    converse_messages.append({
        "role": "user",
        "content": [{"text": body.user_message}],
    })

    # Run the Fina agent
    assistant_text, investment_result = await fina_chat(converse_messages, db)

    # Update state with the new messages for the frontend to persist
    history.append({"role": "user", "content": body.user_message})
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
