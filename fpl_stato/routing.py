"""Route football questions to the FPL or general-trivia assistant.

Routing is deliberately deterministic: explicit FPL terms, FPL chips, or a
first-person squad decision go to the data-backed assistant. General football
facts—including club captains and ordinary fixture questions—go to trivia.
"""

from __future__ import annotations

import re
from typing import Any

from .assistant import FPLAssistant


TRIVIA_SYSTEM_INSTRUCTIONS = """You are FPL Stato, a helpful general football trivia assistant.
Answer stable football facts clearly and concisely. Do not invent facts. For
current, time-sensitive, or obscure questions that you cannot verify, say so
plainly rather than presenting an uncertain answer as fact."""


_FPL_PATTERNS = (
    r"\bfpl\b",
    r"fantasy premier league",
    r"\b(?:my|our)\s+(?:fpl\s+)?(?:team|squad)\b",
    r"\bgameweek\b",
    r"\bwildcard\b",
    r"\bfree hit\b",
    r"\bbench boost\b",
    r"\btriple captain\b",
    r"\bteam value\b",
    r"\btransfer budget\b",
    r"\b(?:player price|total points|fixture difficulty|differential|ownership)\b",
    r"\b(?:squad|bench)\b.*\b(?:player|team|week)\b",
    r"\b(?:who|which player)\s+should\s+i\s+(?:captain|vice[- ]captain|transfer in)\b",
    r"\bshould\s+i\s+(?:captain|vice[- ]captain|buy|sell|transfer in|transfer out)\b",
    r"\bwhich players?\b.*\b(?:best|easiest|favorable|favourable)\b.*\bupcoming fixtures?\b",
)


def is_fpl_question(question: str) -> bool:
    """Return whether a question explicitly concerns Fantasy Premier League."""
    normalized = question.casefold()
    return any(re.search(pattern, normalized) for pattern in _FPL_PATTERNS)


class FootballTriviaAssistant:
    """Answer general football trivia without fetching FPL data."""

    def __init__(self, openai_client: Any | None = None, model: str = "gpt-6-luna") -> None:
        self.openai_client = openai_client if openai_client is not None else __import__("openai").OpenAI()
        self.model = model

    def answer(self, question: str) -> str:
        if not question.strip():
            raise ValueError("question must not be empty")

        response = self.openai_client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": TRIVIA_SYSTEM_INSTRUCTIONS},
                {"role": "user", "content": question.strip()},
            ],
        )
        try:
            answer = response.output_text
        except AttributeError as exc:
            raise ValueError("trivia response did not contain answer text") from exc
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("trivia response did not contain answer text")
        return answer


class QuestionRouter:
    """Route one question while keeping FPL data access out of trivia."""

    def __init__(
        self,
        fpl_assistant: FPLAssistant | None = None,
        trivia_assistant: FootballTriviaAssistant | None = None,
        openai_client: Any | None = None,
        model: str = "gpt-6-luna",
    ) -> None:
        if fpl_assistant is None or trivia_assistant is None:
            client = openai_client if openai_client is not None else __import__("openai").OpenAI()
            fpl_assistant = fpl_assistant or FPLAssistant(openai_client=client, model=model)
            trivia_assistant = trivia_assistant or FootballTriviaAssistant(openai_client=client, model=model)
        self.fpl_assistant = fpl_assistant
        self.trivia_assistant = trivia_assistant

    def answer(self, question: str) -> str:
        if not question.strip():
            raise ValueError("question must not be empty")
        assistant = self.fpl_assistant if is_fpl_question(question) else self.trivia_assistant
        return assistant.answer(question)
