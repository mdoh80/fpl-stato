from unittest.mock import Mock, patch

import pytest

from fastapi import HTTPException

from fpl_stato.api import ChatRequest, ChatResponse, chat, health
from fpl_stato.data import FPLDataError


def test_health():
    assert health() == {"status": "ok"}


def test_chat_returns_assistant_answer():
    assistant = Mock()
    assistant.answer.return_value = "Captain Salah."

    with patch("fpl_stato.api._assistant", assistant):
        response = chat(ChatRequest(question="Who should I captain?"))

    assert response == ChatResponse(answer="Captain Salah.")
    assistant.answer.assert_called_once_with("Who should I captain?")


@pytest.mark.parametrize(
    ("error", "status_code", "detail"),
    [
        (ValueError("question must not be empty"), 400, "question must not be empty"),
        (FPLDataError("cache unavailable"), 502, "FPL data is temporarily unavailable"),
    ],
)
def test_chat_preserves_error_mapping(error, status_code, detail):
    assistant = Mock()
    assistant.answer.side_effect = error

    with patch("fpl_stato.api._assistant", assistant):
        with pytest.raises(HTTPException) as raised:
            chat(ChatRequest(question="question"))

    assert raised.value.status_code == status_code
    assert raised.value.detail == detail
