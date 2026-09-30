from __future__ import annotations

from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slack_bolt.async_app import AsyncApp

from slack_agent.core.config import Settings
from slack_agent.core.errors import ERR_SLACK_AUTH_FAILED, AppError, ErrorCategoryType
from slack_agent.core.logger import get_logger
from slack_agent.core.result import Result

logger = get_logger(__name__)


class SlackBotClient:
    """Manages the lifecycle and connection of the Slack Bolt AsyncApp in Socket Mode."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.app = AsyncApp(
            token=settings.slack_bot_token.get_secret_value(),
            signing_secret=settings.slack_signing_secret.get_secret_value(),
        )
        self.handler: AsyncSocketModeHandler | None = None
        self.bot_user_id: str = ""
        self.is_connected: bool = False

    async def initialize(self) -> Result[str]:
        """Test authentication and cache bot user ID."""
        try:
            auth_response = await self.app.client.auth_test()
            self.bot_user_id = str(auth_response.get("user_id", ""))
            logger.info(
                "Slack authentication successful",
                extra={"BotUserId": self.bot_user_id},
            )
            return Result.ok(self.bot_user_id)
        except Exception as exc:
            err = AppError.wrap(
                exc,
                code=ERR_SLACK_AUTH_FAILED,
                message="Failed to authenticate Slack Bot credentials via auth_test",
                category=ErrorCategoryType.Authentication,
            )
            logger.error(str(err))
            return Result.fail(err)

    async def start(self) -> Result[None]:
        """Connect to Slack in Socket Mode over WebSockets."""
        auth_result = await self.initialize()
        if auth_result.has_error:
            return Result.fail(auth_result.error())

        try:
            self.handler = AsyncSocketModeHandler(
                app=self.app,
                app_token=self.settings.slack_app_token.get_secret_value(),
            )
            self.is_connected = True
            logger.info("Starting Slack Socket Mode client...")
            await self.handler.start_async()  # type: ignore[no-untyped-call]
            return Result.ok(None)
        except Exception as exc:
            err = AppError.wrap(
                exc,
                code="E7001",
                message="Socket Mode connection failed",
                category=ErrorCategoryType.Network,
            )
            logger.error(str(err))
            return Result.fail(err)

    async def stop(self) -> None:
        """Close active Socket Mode handler and terminate connection."""
        if self.handler is not None and self.is_connected:
            logger.info("Closing Slack Socket Mode handler...")
            await self.handler.close_async()  # type: ignore[no-untyped-call]
            self.is_connected = False
