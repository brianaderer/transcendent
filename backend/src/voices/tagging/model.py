"""The language model, reached through OpenRouter with the reviewer's one key (atlas OPEN-5)."""

from langchain_openai import ChatOpenAI

OPENROUTER_URL = "https://openrouter.ai/api/v1"
MODEL_TIMEOUT_SECONDS = 120
MODEL_RETRIES = 3


class MissingModelKey(Exception):
    pass


def connect_model(api_key: str, model_name: str) -> ChatOpenAI:
    if not api_key:
        raise MissingModelKey(
            "OPENROUTER_API_KEY is not set in .env (README step 3); tagging needs it"
        )
    return ChatOpenAI(
        model=model_name,
        base_url=OPENROUTER_URL,
        api_key=api_key,
        temperature=0,
        timeout=MODEL_TIMEOUT_SECONDS,
        max_retries=MODEL_RETRIES,
    )
