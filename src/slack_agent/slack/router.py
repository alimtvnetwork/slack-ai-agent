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
from slack_agent.slack.handlers.slash_commands import (
    MODAL_COMPLIANCE_CALLBACK_ID,
    MODAL_CV_CALLBACK_ID,
    ModalSubmissionContext,
    SlashCommandContext,
    handle_slash_command,
    validate_compliance_modal_submission,
    validate_cv_modal_submission,
)
from slack_agent.slack.handlers.slash_commands import (
    handle_modal_submission as handle_slash_modal_submission,
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


def _register_command_listeners(
    app: AsyncApp,
    settings: Settings,
    agent_graph: Any,
) -> None:
    """Register native slash command handlers on the Bolt AsyncApp."""
    supported_commands = (
        "/help",
        "/ai-help",
        "/commands",
        "/status",
        "/ai-status",
        "/info",
        "/reset",
        "/ai-reset",
        "/clear",
        "/summary",
        "/ai-summary",
        "/summarize",
        "/recap",
        "/compliance-check",
        "/cv-check",
    )

    def _create_command_handler(command_name: str) -> Any:
        async def on_command(
            ack: AsyncAck,
            body: dict[str, Any],
            client: AsyncWebClient,
        ) -> None:
            await ack()
            ctx = SlashCommandContext(
                command_name=command_name,
                body=body,
                client=client,
                settings=settings,
                agent_graph=agent_graph,
            )
            await handle_slash_command(ctx)

        return on_command

    for cmd in supported_commands:
        app.command(cmd)(_create_command_handler(cmd))


def _register_compliance_modal(
    app: AsyncApp,
    settings: Settings,
    agent_graph: Any,
) -> None:
    @app.view(MODAL_COMPLIANCE_CALLBACK_ID)
    async def on_compliance_submit(
        ack: AsyncAck,
        body: dict[str, Any],
        client: AsyncWebClient,
    ) -> None:
        view = body.get("view", {})
        errors = validate_compliance_modal_submission(view)
        if errors:
            await ack(response_action="errors", errors=errors)
            return

        await ack()
        ctx = ModalSubmissionContext(
            callback_id=MODAL_COMPLIANCE_CALLBACK_ID,
            body=body,
            client=client,
            settings=settings,
            agent_graph=agent_graph,
        )
        await handle_slash_modal_submission(ctx)


def _register_cv_modal(
    app: AsyncApp,
    settings: Settings,
    agent_graph: Any,
) -> None:
    @app.view(MODAL_CV_CALLBACK_ID)
    async def on_cv_submit(
        ack: AsyncAck,
        body: dict[str, Any],
        client: AsyncWebClient,
    ) -> None:
        view = body.get("view", {})
        errors = validate_cv_modal_submission(view)
        if errors:
            await ack(response_action="errors", errors=errors)
            return

        await ack()
        ctx = ModalSubmissionContext(
            callback_id=MODAL_CV_CALLBACK_ID,
            body=body,
            client=client,
            settings=settings,
            agent_graph=agent_graph,
        )
        await handle_slash_modal_submission(ctx)


def _register_modal_view_listeners(
    app: AsyncApp,
    settings: Settings,
    agent_graph: Any,
) -> None:
    """Register modal submission listeners for specialized tasks."""
    _register_compliance_modal(app, settings, agent_graph)
    _register_cv_modal(app, settings, agent_graph)


def _register_slash_command_routes(
    app: AsyncApp,
    settings: Settings,
    agent_graph: Any,
) -> None:
    """Register native Slack slash commands and modal submission handlers."""
    _register_command_listeners(app, settings, agent_graph)
    _register_modal_view_listeners(app, settings, agent_graph)


def register_slack_routes(
    app: AsyncApp,
    settings: Settings,
    agent_graph: Any,
    bot_user_id: str,
) -> None:
    """Register all Slack event and interactive action listeners on the Bolt AsyncApp."""
    _register_event_routes(app, settings, agent_graph, bot_user_id)
    _register_action_routes(app)
    _register_slash_command_routes(app, settings, agent_graph)
