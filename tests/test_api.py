from unittest.mock import Mock, patch

from fpl_stato.api import ChatRequest, ChatResponse, chat, health


def test_health():
    assert health() == {"status": "ok"}


def test_chat_returns_assistant_answer():
    assistant = Mock()
    assistant.answer.return_value = "Captain Salah."

    with patch("fpl_stato.api._assistant", assistant):
        response = chat(ChatRequest(question="Who should I captain?"))

    assert response == ChatResponse(answer="Captain Salah.")
    assistant.answer.assert_called_once_with("Who should I captain?")
