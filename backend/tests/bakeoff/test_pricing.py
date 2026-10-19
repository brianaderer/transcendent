import pytest

from voices.bakeoff.pricing import Price, UnknownPrice, price_of


def test_cost_is_tokens_times_the_price_per_million():
    assert Price(2.0, 10.0).of(tokens_in=500_000, tokens_out=100_000) == pytest.approx(2.0)


def test_both_bake_off_models_have_prices():
    assert (
        price_of("anthropic/claude-haiku-5.5").per_million_in
        < price_of("anthropic/claude-sonnet-5.5").per_million_in
    )


def test_a_model_without_a_listed_price_raises():
    with pytest.raises(UnknownPrice):
        price_of("someone/else")
