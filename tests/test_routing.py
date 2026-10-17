from unittest.mock import Mock

import pytest

from fpl_stato.routing import FootballTriviaAssistant, QuestionRouter, is_fpl_question


@pytest.mark.parametrize(
    ("question", "expected_fpl"),
    [
        ("Who should I captain?", True),
        ("Who should I transfer in?", True),
        ("Who should I captain this gameweek?", True),
        ("Should I wildcard this week?", True),
        ("Which players have the best upcoming fixtures?", True),
        ("What is Salah's player price?", True),
        ("Who is Liverpool's current captain?", False),
        ("What are Arsenal's upcoming fixtures?", False),
        ("What are the rules for the captain's armband?", False),
        ("Who won the 1966 World Cup?", False),
    ],
)
def test_routes_questions_using_explicit_intent(question, expected_fpl):
    assert is_fpl_question(question) is expected_fpl


def test_router_does_not_fetch_fpl_data_for_trivia():
    fpl = Mock()
    trivia = Mock()
    trivia.answer.return_value = "Brazil."
    router = QuestionRouter(fpl_assistant=fpl, trivia_assistant=trivia)

    assert router.answer("Who won the 1970 World Cup?") == "Brazil."
    trivia.answer.assert_called_once_with("Who won the 1970 World Cup?")
    fpl.answer.assert_not_called()


@pytest.mark.parametrize(
    ("question", "assistant_name"),
    [
        ("Who should I captain?", "fpl"),
        ("Who should I transfer in?", "fpl"),
        ("Who is Liverpool's current captain?", "trivia"),
        ("What are Arsenal's upcoming fixtures?", "trivia"),
    ],
)
def test_router_dispatches_ambiguous_questions(question, assistant_name):
    fpl = Mock()
    trivia = Mock()
    QuestionRouter(fpl_assistant=fpl, trivia_assistant=trivia).answer(question)

    expected = fpl if assistant_name == "fpl" else trivia
    expected.answer.assert_called_once_with(question)


def test_trivia_assistant_returns_openai_text():
    client = Mock()
    client.responses.create.return_value.output_text = "Brazil."
    assistant = FootballTriviaAssistant(openai_client=client, model="test-model")

    assert assistant.answer("Who won the 1970 World Cup?") == "Brazil."
    call = client.responses.create.call_args.kwargs
    assert call["model"] == "test-model"
    assert call["input"][1]["content"] == "Who won the 1970 World Cup?"


@pytest.mark.parametrize("response", [Mock(output_text=""), Mock(output_text=None), Mock()])
def test_trivia_assistant_rejects_malformed_response_text(response):
    client = Mock()
    client.responses.create.return_value = response
    assistant = FootballTriviaAssistant(openai_client=client)

    with pytest.raises(ValueError, match="trivia response did not contain answer text"):
        assistant.answer("Who won the 1970 World Cup?")


def test_trivia_assistant_propagates_openai_failures():
    client = Mock()
    failure = RuntimeError("OpenAI unavailable")
    client.responses.create.side_effect = failure
    assistant = FootballTriviaAssistant(openai_client=client)

    with pytest.raises(RuntimeError, match="OpenAI unavailable"):
        assistant.answer("Who won the 1970 World Cup?")


def test_router_rejects_empty_questions_without_calling_an_assistant():
    fpl = Mock()
    trivia = Mock()
    with pytest.raises(ValueError, match="question must not be empty"):
        QuestionRouter(fpl_assistant=fpl, trivia_assistant=trivia).answer(" ")
    fpl.answer.assert_not_called()
    trivia.answer.assert_not_called()
