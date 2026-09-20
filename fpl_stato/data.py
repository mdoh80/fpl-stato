"""Download and validate a snapshot from the fplcache repository."""

from __future__ import annotations

import json
import lzma
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


class FPLDataError(RuntimeError):
    """Raised when the FPL cache cannot be downloaded or validated."""


@dataclass(frozen=True)
class FPLSnapshot:
    """The three FPL datasets and the manifest that describes them."""

    manifest: dict[str, Any]
    bootstrap: dict[str, Any]
    fixtures: list[Any]
    live: dict[str, Any]


class FPLDataClient:
    """Fetch one consistent FPL data snapshot from a cache branch."""

    DATASETS = ("bootstrap", "fixtures", "live")

    def __init__(
        self,
        base_url: str = "https://raw.githubusercontent.com/mdoh80/fplcache/latest/",
        timeout: float = 30,
    ) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout = timeout

    def fetch(self) -> FPLSnapshot:
        manifest = self._get_json("manifest.json")
        if not isinstance(manifest, dict):
            raise FPLDataError("manifest.json must contain a JSON object")

        datasets = {
            name: self._get_compressed_json(self._dataset_path(manifest, name))
            for name in self.DATASETS
        }
        self._validate_datasets(datasets)
        return FPLSnapshot(manifest=manifest, **datasets)

    def _dataset_path(self, manifest: dict[str, Any], name: str) -> str:
        """Use a manifest-provided path, falling back to the published filename."""
        files = manifest.get("files")
        value: Any = files.get(name) if isinstance(files, dict) else None
        if value is None:
            value = manifest.get(name)
        if value is None:
            value = f"{name}.json.xz"
        if isinstance(value, dict):
            value = value.get("path") or value.get("url") or value.get("name")
        if not isinstance(value, str) or not value:
            raise FPLDataError(f"manifest does not provide a valid {name} dataset path")
        return value

    def _read(self, path: str) -> bytes:
        url = urljoin(self.base_url, path)
        request = Request(url, headers={"User-Agent": "fpl-stato/0.1"})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return response.read()
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise FPLDataError(f"could not fetch {url}: {exc}") from exc

    def _get_json(self, path: str) -> Any:
        try:
            return json.loads(self._read(path).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise FPLDataError(f"{path} is not valid UTF-8 JSON") from exc

    def _get_compressed_json(self, path: str) -> Any:
        try:
            payload = lzma.decompress(self._read(path))
            return json.loads(payload.decode("utf-8"))
        except (lzma.LZMAError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise FPLDataError(f"{path} is not valid compressed JSON") from exc

    @staticmethod
    def _validate_datasets(datasets: dict[str, Any]) -> None:
        if not isinstance(datasets["bootstrap"], dict):
            raise FPLDataError("bootstrap dataset must contain a JSON object")
        if not isinstance(datasets["fixtures"], list):
            raise FPLDataError("fixtures dataset must contain a JSON array")
        if not isinstance(datasets["live"], dict):
            raise FPLDataError("live dataset must contain a JSON object")
