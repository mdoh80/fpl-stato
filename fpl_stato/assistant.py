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


def _project_records(records: Any, fields: tuple[str, ...]) -> list[dict[str, Any]]:
    """Keep only useful fields from a list of cache records."""
    if not isinstance(records, list):
        return []
    return [
        {field: record[field] for field in fields if field in record}
        for record in records
        if isinstance(record, dict)
    ]


def build_data_context(snapshot: FPLSnapshot) -> str:
    """Serialize a compact, machine-readable view of a snapshot.

    The raw FPL cache includes historical and per-gameweek detail that can make
    a prompt exceed the model context window. Keep the fields needed for
    player, fixture, team, and current-live-stat questions instead.
    """
    bootstrap = snapshot.bootstrap
    live = snapshot.live
    player_fields = (
        "id", "first_name", "second_name", "web_name", "team", "element_type",
        "now_cost", "total_points", "event_points", "form", "selected_by_percent",
        "minutes", "goals_scored", "assists", "clean_sheets", "bonus", "influence",
        "creativity", "threat", "ict_index", "starts", "transfers_in_event",
        "transfers_out_event", "value_form", "value_season", "status",
        "chance_of_playing_next_round", "chance_of_playing_this_round", "news",
    )
    team_fields = ("id", "name", "short_name", "code", "strength", "position")
    fixture_fields = (
        "id", "event", "team_h", "team_a", "team_h_score", "team_a_score",
        "finished", "kickoff_time", "team_h_difficulty", "team_a_difficulty",
        "minutes", "provisional_start_time", "started", "pulse_id",
    )
    live_fields = ("id", "stats")
    return json.dumps(
        {
            "manifest": {
                key: value
                for key, value in snapshot.manifest.items()
                if key not in {"files", "checksums", "sizes"}
            },
            "bootstrap": {
                "events": _project_records(bootstrap.get("events"), (
                    "id", "name", "deadline_time", "finished", "is_current",
                    "is_next", "is_previous", "average_entry_score", "highest_score",
                    "most_selected", "most_transferred_in", "top_element",
                    "top_element_info", "transfers_made", "most_captained",
                    "most_vice_captained",
                )),
                "teams": _project_records(bootstrap.get("teams"), team_fields),
                "elements": _project_records(bootstrap.get("elements"), player_fields),
            },
            "fixtures": _project_records(snapshot.fixtures, fixture_fields),
            "live": {
                "elements": _project_records(live.get("elements"), live_fields),
            },
            "omitted_fields": [
                "bootstrap.gameweeks",
                "bootstrap.element_stats",
                "bootstrap.element_types",
                "live.historical_detail",
            ],
        },
        separators=(",", ":"),
    )


class FPLAssistant:
    """Fetch current FPL data and answer one question with OpenAI."""

    def __init__(
        self,
        data_client: FPLDataClient | None = None,
        openai_client: Any | None = None,
        model: str = "gpt-6-luna",
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
