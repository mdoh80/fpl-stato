import json
import lzma
from io import BytesIO
from unittest.mock import patch

import pytest

from fpl_stato.data import FPLDataClient, FPLDataError


class FakeResponse(BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


def test_fetches_manifest_and_all_datasets():
    manifest = {
        "gameweek": 5,
        "files": {
            "bootstrap": "bootstrap.json.xz",
            "fixtures": "fixtures.json.xz",
            "live": "live.json.xz",
        },
    }
    documents = {
        "manifest.json": manifest,
        "bootstrap.json.xz": {"elements": [], "teams": [], "gameweeks": []},
        "fixtures.json.xz": [{"id": 1}],
        "live.json.xz": {"elements": []},
    }

    def fake_urlopen(request, timeout):
        name = request.full_url.rsplit("/", 1)[-1]
        document = documents[name]
        payload = json.dumps(document).encode()
        if name != "manifest.json":
            payload = lzma.compress(payload)
        return FakeResponse(payload)

    with patch("fpl_stato.data.urlopen", side_effect=fake_urlopen):
        snapshot = FPLDataClient("https://example.test/cache").fetch()

    assert snapshot.manifest["gameweek"] == 5
    assert snapshot.bootstrap["teams"] == []
    assert snapshot.fixtures == [{"id": 1}]
    assert snapshot.live == {"elements": []}


def test_rejects_invalid_dataset_shape():
    def fake_urlopen(request, timeout):
        name = request.full_url.rsplit("/", 1)[-1]
        payload = json.dumps({}).encode() if name == "manifest.json" else lzma.compress(b"[]")
        return FakeResponse(payload)

    with patch("fpl_stato.data.urlopen", side_effect=fake_urlopen):
        with pytest.raises(FPLDataError, match="bootstrap dataset"):
            FPLDataClient().fetch()


def test_rejects_invalid_compressed_json():
    def fake_urlopen(request, timeout):
        name = request.full_url.rsplit("/", 1)[-1]
        if name == "manifest.json":
            return FakeResponse(b"{}")
        return FakeResponse(lzma.compress(b"not json"))

    with patch("fpl_stato.data.urlopen", side_effect=fake_urlopen):
        with pytest.raises(FPLDataError, match="not valid compressed JSON"):
            FPLDataClient().fetch()
