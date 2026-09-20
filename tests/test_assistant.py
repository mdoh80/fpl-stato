from unittest.mock import Mock

from fpl_stato import FPLAssistant, FPLSnapshot


def test_assistant_fetches_data_and_returns_openai_text():
    snapshot = FPLSnapshot(
        manifest={"current_gameweek": 5},
        bootstrap={"elements": [{"id": 1}], "teams": []},
        fixtures=[],
        live={"elements": []},
    )
    data_client = Mock()
    data_client.fetch.return_value = snapshot
    openai_client = Mock()
    openai_client.responses.create.return_value.output_text = "Captain Salah."

    assistant = FPLAssistant(data_client=data_client, openai_client=openai_client, model="test-model")
    answer = assistant.answer("Who should I captain?")

    assert answer == "Captain Salah."
    data_client.fetch.assert_called_once_with()
    call = openai_client.responses.create.call_args.kwargs
    assert call["model"] == "test-model"
    assert "Who should I captain?" in call["input"][1]["content"]
    assert '"current_gameweek":5' in call["input"][1]["content"]


def test_assistant_rejects_empty_questions():
    assistant = FPLAssistant(data_client=Mock(), openai_client=Mock())

    try:
        assistant.answer("  ")
    except ValueError as exc:
        assert str(exc) == "question must not be empty"
    else:
        raise AssertionError("expected ValueError")
