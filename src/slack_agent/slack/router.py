from __future__ import annotations

from typing import Any

from slack_bolt.async_app import AsyncAck, AsyncApp
from slack_sdk.web.async_client import AsyncWebClient

from slack_agent.core.config import Settings
from slack_agent.slack.handlers.actions import (
    handle_approval_action,
    handle_edit_action,
    handle_modal_submission,
    handle_rejection_action,
)
from slack_agent.slack.handlers.messages import (
    MessageEventContext,
    handle_incoming_message_event,
)


def _register_event_routes(
    app: AsyncApp,
    settings: Settings,
    agent_graph: Any,
    bot_user_id: str,
) -> None:
    """Register Slack event listeners (app mentions and direct messages)."""

    @app.event("app_mention")
    async def on_app_mention(
        event: dict[str, Any],
        ack: AsyncAck,
        client: AsyncWebClient,
    ) -> None:
        ctx = MessageEventContext(
            event=event,
            ack=ack,
            client=client,
            settings=settings,
            agent_graph=agent_graph,
            bot_user_id=bot_user_id,
        )
        await handle_incoming_message_event(ctx)

    @app.event("message")
    async def on_direct_message(
        event: dict[str, Any],
        ack: AsyncAck,
        client: AsyncWebClient,
    ) -> None:
        if event.get("channel_type") == "im":
            ctx = MessageEventContext(
                event=event,
                ack=ack,
                client=client,
                settings=settings,
                agent_graph=agent_graph,
                bot_user_id=bot_user_id,
            )
            await handle_incoming_message_event(ctx)
        else:
            await ack()


def _register_action_routes(app: AsyncApp) -> None:
    """Register interactive Block Kit button and modal listeners."""

    @app.action("approve_file_write")
    async def on_approve_action(
        ack: AsyncAck,
        body: dict[str, Any],
        client: AsyncWebClient,
    ) -> None:
        await handle_approval_action(ack=ack, body=body, client=client)

    @app.action("reject_file_write")
    async def on_reject_action(
        ack: AsyncAck,
        body: dict[str, Any],
        client: AsyncWebClient,
    ) -> None:
        await handle_rejection_action(ack=ack, body=body, client=client)

    @app.action("edit_file_write_proposal")
    async def on_edit_action(
        ack: AsyncAck,
        body: dict[str, Any],
        client: AsyncWebClient,
    ) -> None:
        await handle_edit_action(ack=ack, body=body, client=client)

    @app.view("submit_edit_file_proposal")
    async def on_modal_submit(
        ack: AsyncAck,
        body: dict[str, Any],
        client: AsyncWebClient,
    ) -> None:
        await handle_modal_submission(ack=ack, body=body, client=client)


def register_slack_routes(
    app: AsyncApp,
    settings: Settings,
    agent_graph: Any,
    bot_user_id: str,
) -> None:
    """Register all Slack event and interactive action listeners on the Bolt AsyncApp."""
    _register_event_routes(app, settings, agent_graph, bot_user_id)
    _register_action_routes(app)
