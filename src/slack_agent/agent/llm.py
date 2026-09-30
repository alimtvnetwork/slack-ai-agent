from __future__ import annotations

from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from slack_agent.core.config import Settings


def create_llm_client(settings: Settings, max_tokens: int | None = None) -> ChatOpenAI:
    """Initialize OpenRouter-backed ChatOpenAI client with headers and max_tokens limit."""
    api_key_str = settings.openrouter_api_key.get_secret_value()
    # Provide placeholder string if not yet provided to allow graph initialization
    effective_api_key = api_key_str if api_key_str.strip() else "sk-placeholder-key"
    effective_max_tokens = max_tokens if max_tokens is not None else settings.openrouter_max_tokens
    extra_body = (
        {"reasoning": {"effort": settings.openrouter_reasoning_effort}}
        if settings.openrouter_reasoning_effort
        else None
    )

    return ChatOpenAI(
        model=settings.openrouter_model,
        api_key=SecretStr(effective_api_key),
        base_url=settings.openrouter_base_url,
        temperature=0.2,
        max_tokens=effective_max_tokens,  # type: ignore[call-arg]
        extra_body=extra_body,
        default_headers={
            "HTTP-Referer": "https://github.com/slack-agent",
            "X-Title": settings.agent_name,
        },
    )
