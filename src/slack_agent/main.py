from __future__ import annotations

import asyncio
import sys

from slack_agent.agent.checkpointer import get_async_checkpointer
from slack_agent.agent.graph import create_agent_graph
from slack_agent.agent.llm import create_llm_client
from slack_agent.core.config import Settings, load_settings
from slack_agent.core.logger import get_logger, setup_logging
from slack_agent.slack.client import SlackBotClient
from slack_agent.slack.router import register_slack_routes

logger = get_logger("slack_agent")


def _is_environment_configured(settings: Settings) -> bool:
    """Verify that both Slack tokens and OpenRouter key are set."""
    if not settings.has_slack_credentials:
        logger.warning(
            "Slack credentials are missing or incomplete in .env. "
            "Please configure SLACK_BOT_TOKEN (xoxb-...) and SLACK_APP_TOKEN (xapp-...) "
            "per spec/slack-configuration.md."
        )
        return False

    if not settings.has_openrouter_credentials:
        logger.warning(
            "OPENROUTER_API_KEY is not configured in .env. "
            "Please configure OPENROUTER_API_KEY per spec/slack-configuration.md."
        )
        return False

    return True


async def run_application(settings: Settings) -> None:
    """Run the Slack AI Agent application."""
    logger.info("Initializing Slack AI Agent system components...")
    if not _is_environment_configured(settings):
        return

    async with get_async_checkpointer() as checkpointer:
        llm_client = create_llm_client(settings)
        agent_graph = create_agent_graph(llm_client=llm_client, checkpointer=checkpointer)

        slack_client = SlackBotClient(settings)
        auth_result = await slack_client.initialize()
        if auth_result.has_error:
            logger.error(f"Cannot start bot: {auth_result.error()}")
            return

        bot_user_id = auth_result.value()
        register_slack_routes(
            app=slack_client.app,
            settings=settings,
            agent_graph=agent_graph,
            bot_user_id=bot_user_id,
        )

        logger.info(f"Bot connected as <@{bot_user_id}>. Listening for events...")
        await slack_client.start()


def main() -> None:
    """Entrypoint function for CLI and module execution."""
    settings = load_settings()
    setup_logging(log_level=settings.log_level)

    try:
        asyncio.run(run_application(settings))
    except KeyboardInterrupt:
        logger.info("Application shut down by user.")
    except Exception as exc:
        logger.error(f"Fatal error running application: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
