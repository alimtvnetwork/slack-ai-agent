from __future__ import annotations

import asyncio
import sys
from typing import Any

from slack_agent.agent.analyst_prompts import ANALYST_SYSTEM_PROMPT
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


async def _start_single_bot(
    settings: Settings,
    agent_graph: Any,
    label: str,
) -> None:
    """Initialize authentication, wire event routes, and connect Socket Mode."""
    slack_client = SlackBotClient(settings)
    auth_result = await slack_client.initialize()
    if auth_result.has_error:
        logger.error(f"Cannot start {label}: {auth_result.error()}")
        return

    bot_user_id = auth_result.value()
    register_slack_routes(
        app=slack_client.app,
        settings=settings,
        agent_graph=agent_graph,
        bot_user_id=bot_user_id,
    )
    logger.info(f"{label} connected as <@{bot_user_id}>. Listening for events...")
    await slack_client.start()


async def run_application(settings: Settings) -> None:
    """Run the primary bot and optional analyst bot concurrently."""
    logger.info("Initializing Slack AI Agent system components...")
    if not _is_environment_configured(settings):
        return

    async with get_async_checkpointer() as checkpointer:
        llm_client = create_llm_client(settings)
        ops_graph = create_agent_graph(llm_client=llm_client, checkpointer=checkpointer)
        tasks = [_start_single_bot(settings, ops_graph, label=f"Bot ({settings.agent_name})")]

        if settings.has_analyst_slack_credentials:
            analyst_settings = settings.for_analyst()
            analyst_graph = create_agent_graph(
                llm_client=llm_client,
                checkpointer=checkpointer,
                system_prompt=ANALYST_SYSTEM_PROMPT,
            )
            tasks.append(
                _start_single_bot(
                    analyst_settings,
                    analyst_graph,
                    label=f"Analyst Bot ({analyst_settings.agent_name})",
                )
            )
        else:
            logger.info("Analyst credentials not configured; running primary bot only.")

        await asyncio.gather(*tasks)


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
