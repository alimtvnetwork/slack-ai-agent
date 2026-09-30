from __future__ import annotations

from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration and credentials loaded from environment or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    slack_bot_token: SecretStr = Field(default=SecretStr(""))
    slack_app_token: SecretStr = Field(default=SecretStr(""))
    slack_signing_secret: SecretStr = Field(default=SecretStr(""))

    openrouter_api_key: SecretStr = Field(default=SecretStr(""))
    openrouter_model: str = Field(default="anthropic/claude-3.5-sonnet")
    openrouter_base_url: str = Field(default="https://openrouter.ai/api/v1")
    openrouter_max_tokens: int = Field(default=8192)
    openrouter_reasoning_effort: str = Field(default="low")

    agent_name: str = Field(default="AIAssistant")
    accent_color: str = Field(default="#1A85FF")
    proposal_ttl_seconds: int = Field(default=1800)
    max_file_size_bytes: int = Field(default=10 * 1024 * 1024)
    log_level: str = Field(default="INFO")

    # Analyst Bot Settings (Bot 2)
    analyst_slack_bot_token: SecretStr = Field(default=SecretStr(""))
    analyst_slack_app_token: SecretStr = Field(default=SecretStr(""))
    analyst_agent_name: str = Field(default="KITA-Analyst")
    analyst_accent_color: str = Field(default="#007A5A")

    @field_validator("max_file_size_bytes")
    @classmethod
    def validate_max_file_size(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("max_file_size_bytes must be greater than zero")

        return value

    @property
    def has_slack_credentials(self) -> bool:
        """Check if all required Slack tokens are configured for primary bot."""
        bot_token = self.slack_bot_token.get_secret_value().strip()
        app_token = self.slack_app_token.get_secret_value().strip()

        return bot_token.startswith("xoxb-") and app_token.startswith("xapp-")

    @property
    def has_analyst_slack_credentials(self) -> bool:
        """Check if all required Slack tokens are configured for analyst bot."""
        bot_token = self.analyst_slack_bot_token.get_secret_value().strip()
        app_token = self.analyst_slack_app_token.get_secret_value().strip()

        return bot_token.startswith("xoxb-") and app_token.startswith("xapp-")

    @property
    def has_openrouter_credentials(self) -> bool:
        """Check if OpenRouter API key is configured."""
        key = self.openrouter_api_key.get_secret_value().strip()

        return len(key) > 0

    def for_analyst(self) -> Settings:
        """Create a Settings instance configured with analyst bot parameters."""
        return self.model_copy(
            update={
                "agent_name": self.analyst_agent_name,
                "accent_color": self.analyst_accent_color,
                "slack_bot_token": self.analyst_slack_bot_token,
                "slack_app_token": self.analyst_slack_app_token,
            }
        )


def load_settings(env_file_path: str | Path | None = None) -> Settings:
    """Load settings from environment with optional explicit .env path."""
    if env_file_path is not None:
        return Settings(_env_file=str(env_file_path))  # type: ignore[call-arg]

    return Settings()
