"""HTTP API for the FPL Stato assistant."""

from __future__ import annotations

from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .routing import QuestionRouter
from .data import FPLDataError


app = FastAPI(title="FPL Stato", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://football-bot.com", "https://www.football-bot.com"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)
_assistant: QuestionRouter | None = None


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)


class ChatResponse(BaseModel):
    answer: str
    skill: Literal["fpl", "trivia"]


def get_assistant() -> QuestionRouter:
    global _assistant
    if _assistant is None:
        _assistant = QuestionRouter()
    return _assistant


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        result = get_assistant().answer_with_skill(request.question)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FPLDataError as exc:
        raise HTTPException(status_code=502, detail="FPL data is temporarily unavailable") from exc
    return ChatResponse(**result)
