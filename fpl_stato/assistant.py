"""OpenAI-powered question answering over an FPL data snapshot."""

from __future__ import annotations

import json
from typing import Any


from .data import FPLDataClient, FPLSnapshot


SYSTEM_INSTRUCTIONS = """You are FPL Stato, an accurate Fantasy Premier League assistant.
Answer using the supplied FPL data. Be clear about the relevant gameweek and
distinguish data-backed facts from recommendations or uncertainty. Never claim
that a player, fixture, or statistic exists if it is not present in the data.
Keep answers concise unless the user asks for detail."""


def build_data_context(snapshot: FPLSnapshot) -> str:
    """Serialize a snapshot as stable, machine-readable assistant context."""
    return json.dumps(
        {
            "manifest": snapshot.manifest,
            "bootstrap": snapshot.bootstrap,
            "fixtures": snapshot.fixtures,
            "live": snapshot.live,
        },
        separators=(",", ":"),
    )


class FPLAssistant:
    """Fetch current FPL data and answer one question with OpenAI."""

    def __init__(
        self,
        data_client: FPLDataClient | None = None,
        openai_client: Any | None = None,
        model: str = "gpt-5.6",
    ) -> None:
        self.data_client = data_client or FPLDataClient()
        self.openai_client = openai_client if openai_client is not None else __import__("openai").OpenAI()
        self.model = model

    def answer(self, question: str) -> str:
        if not question.strip():
            raise ValueError("question must not be empty")

        snapshot = self.data_client.fetch()
        prompt = (
            f"FPL data context (JSON):\n{build_data_context(snapshot)}\n\n"
            f"User question:\n{question.strip()}"
        )
        response = self.openai_client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": SYSTEM_INSTRUCTIONS},
                {"role": "user", "content": prompt},
            ],
        )
        return response.output_text
