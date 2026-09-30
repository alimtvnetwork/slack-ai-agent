from __future__ import annotations

import pytest
from pydantic import SecretStr, ValidationError

from slack_agent.core.config import Settings


def test_settings_default_values() -> None:
    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.agent_name == "AIAssistant"
    assert settings.proposal_ttl_seconds == 1800
    assert settings.max_file_size_bytes == 10 * 1024 * 1024
    assert settings.has_slack_credentials is False
    assert settings.has_openrouter_credentials is False


def test_settings_credentials_validation() -> None:
    settings = Settings(
        slack_bot_token=SecretStr("xoxb-valid-bot-token"),
        slack_app_token=SecretStr("xapp-valid-app-token"),
        openrouter_api_key=SecretStr("sk-or-valid-key"),
    )

    assert settings.has_slack_credentials is True
    assert settings.has_openrouter_credentials is True
    # Secrets should not expose raw values in string repr
    assert "xoxb-valid-bot-token" not in str(settings.slack_bot_token)
    assert settings.slack_bot_token.get_secret_value() == "xoxb-valid-bot-token"


def test_settings_invalid_token_prefixes() -> None:
    settings = Settings(
        slack_bot_token=SecretStr("invalid-bot-token"),
        slack_app_token=SecretStr("invalid-app-token"),
    )

    assert settings.has_slack_credentials is False


def test_settings_negative_file_size_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(max_file_size_bytes=-5)
