"""The help assistant: answers questions about using Crate, from ragbot/help.py, for people who are signed in.

It knows only that guide. It is given no item, stock, message or account data, and no name or email: what leaves this
server for the model is the guide and the last few lines of the conversation the browser sends. Nothing is stored here;
the browser keeps the conversation and sends it again with each question.
"""
import json
import logging
import math
from functools import lru_cache
from typing import Literal

import anthropic
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, model_validator

from app.config import get_settings
from app.models import User
from app.ratelimit import limiter
from app.security import current_user

from .help import SYSTEM_PROMPT

router = APIRouter(prefix="/api/chat", dependencies=[Depends(current_user)])
log = logging.getLogger(__name__)

MAX_LENGTH = 2000  # characters in one message
SENT = 10  # how many of the latest messages go to the model
MAX_TOKENS = 1500  # the reply; the model's thinking counts toward it, so leave room


class Turn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=MAX_LENGTH)


class ChatIn(BaseModel):
    messages: list[Turn] = Field(min_length=1, max_length=40)

    @model_validator(mode="after")
    def ends_with_a_question(self):
        if self.messages[-1].role != "user":
            raise ValueError("The last message must be yours")
        return self


class ChatConfigOut(BaseModel):
    enabled: bool


@lru_cache
def get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=get_settings().ANTHROPIC_API_KEY, timeout=30.0, max_retries=2)


def event(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


@router.get("/config", response_model=ChatConfigOut)
def chat_config():
    """Whether there is an assistant at all: the browser shows no chat button when there is not."""
    return ChatConfigOut(enabled=bool(get_settings().ANTHROPIC_API_KEY))


@router.post("")
def chat(body: ChatIn, user: User = Depends(current_user)):
    settings = get_settings()
    if not settings.ANTHROPIC_API_KEY:
        raise HTTPException(503, "The assistant is not set up")
    try:
        limiter.take((f"chat {user.id}", settings.CHAT_MESSAGES_PER_DAY, 86400))
    except HTTPException as limit:  # the limiter counts in minutes, which is a lot of them for a day
        hours = math.ceil(int(limit.headers["Retry-After"]) / 3600)
        raise HTTPException(
            429,
            f"You have used today's {settings.CHAT_MESSAGES_PER_DAY} messages. Try again in about "
            f"{hours} hour{'' if hours == 1 else 's'}.",
            headers=limit.headers,
        ) from None

    turns = [turn.model_dump() for turn in body.messages[-SENT:]]
    if turns[0]["role"] == "assistant":  # the model's first line must be a question
        turns = turns[1:]

    def answer():
        try:
            with get_client().messages.stream(
                model=settings.CHAT_MODEL,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                messages=turns,
                output_config={"effort": "low"},  # a lookup in a short guide needs no long thinking
            ) as stream:
                for text in stream.text_stream:
                    yield event({"text": text})
                final = stream.get_final_message()
        except anthropic.APIError as error:
            # What was asked is never logged, and neither is the error's own text.
            log.error("The assistant request failed: %s %s", type(error).__name__, getattr(error, "status_code", ""))
            yield event({"error": "The assistant isn't available right now. Please try again in a moment."})
            return
        if final.stop_reason == "refusal":
            yield event({"error": "I can't help with that one."})
        else:
            yield event({"done": True})

    # no-store: not kept anywhere. no buffering: nginx would otherwise hold the reply back until it is complete.
    headers = {"Cache-Control": "no-store", "X-Accel-Buffering": "no"}
    return StreamingResponse(answer(), media_type="text/event-stream", headers=headers)
