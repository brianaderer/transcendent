"""What each bake-off model costs: OpenRouter's listed prices, read from
https://openrouter.ai/api/v1/models on 2026-10-18, in dollars per million tokens."""

from dataclasses import dataclass

TOKENS_PER_MILLION = 1_000_000


@dataclass(frozen=True)
class Price:
    per_million_in: float
    per_million_out: float

    def of(self, tokens_in: int, tokens_out: int) -> float:
        spent = tokens_in * self.per_million_in + tokens_out * self.per_million_out
        return spent / TOKENS_PER_MILLION


PRICES = {
    "anthropic/claude-haiku-5.5": Price(0.10, 0.50),
    "anthropic/claude-sonnet-5.5": Price(2.00, 10.00),
}


class UnknownPrice(Exception):
    pass


def price_of(model_name: str) -> Price:
    if model_name not in PRICES:
        raise UnknownPrice(f"{model_name} has no price in voices/bakeoff/pricing.py; add it first")
    return PRICES[model_name]
