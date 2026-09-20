"""Command-line entry point for checking the current FPL data snapshot."""

from __future__ import annotations

import argparse
import json

from .data import FPLDataClient, FPLDataError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Load and summarize the current FPL data")
    parser.add_argument(
        "--base-url",
        help="fplcache base URL (defaults to the latest branch)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    client = FPLDataClient(**({"base_url": args.base_url} if args.base_url else {}))

    try:
        snapshot = client.fetch()
    except FPLDataError as exc:
        print(f"FPL data error: {exc}")
        return 1

    bootstrap = snapshot.bootstrap
    live_elements = snapshot.live.get("elements", [])
    summary = {
        "gameweek": snapshot.manifest.get("current_gameweek", snapshot.manifest.get("gameweek")),
        "players": len(bootstrap.get("elements", [])),
        "teams": len(bootstrap.get("teams", [])),
        "fixtures": len(snapshot.fixtures),
        "live_players": len(live_elements) if isinstance(live_elements, list) else 0,
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
