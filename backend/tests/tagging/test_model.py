import pytest

from voices.tagging.model import MissingModelKey, connect_model


def test_tagging_without_a_key_stops_with_a_message_saying_where_the_key_goes():
    with pytest.raises(MissingModelKey, match="OPENROUTER_API_KEY"):
        connect_model(api_key="", model_name="anthropic/claude-sonnet-5.5")


def test_the_model_is_reached_through_openrouter():
    model = connect_model(api_key="sk-or-test", model_name="anthropic/claude-sonnet-5.5")

    assert model.model_name == "anthropic/claude-sonnet-5.5"
    assert str(model.openai_api_base).startswith("https://openrouter.ai/api/v1")
