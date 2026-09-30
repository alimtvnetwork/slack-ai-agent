from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from langchain_core.callbacks import AsyncCallbackHandler
from slack_sdk.web.async_client import AsyncWebClient

from slack_agent.core.logger import get_logger

logger = get_logger(__name__)

MAX_STATUS_TEXT_LENGTH = 2800


class SlackStatusNotifier(AsyncCallbackHandler):
    """
    Manages a live temporary status message in a Slack thread.

    Provides real-time feedback during file processing, reasoning,
    and tool execution, and cleans up when the pipeline finishes.
    """

    def __init__(
        self,
        client: AsyncWebClient,
        channel_id: str,
        thread_ts: str,
    ) -> None:
        super().__init__()
        self.client = client
        self.channel_id = channel_id
        self.thread_ts = thread_ts
        self.status_ts: str | None = None
        self.has_finalized: bool = False

    async def start(self, initial_text: str = "⏳ _Thinking..._") -> None:
        """Post the initial status message in the Slack thread."""
        try:
            res = await self.client.chat_postMessage(
                channel=self.channel_id,
                thread_ts=self.thread_ts,
                text=initial_text,
            )
            self.status_ts = res.get("ts")
        except Exception as exc:
            logger.debug(f"Failed to post initial status message: {exc}")

    async def update(self, text: str) -> None:
        """Update the existing temporary status message."""
        if not self.status_ts:
            return
        try:
            await self.client.chat_update(
                channel=self.channel_id,
                ts=self.status_ts,
                text=text,
            )
        except Exception as exc:
            logger.debug(f"Failed to update status message: {exc}")

    async def finalize(
        self,
        text: str,
        blocks: list[dict[str, Any]] | None = None,
        attachments: list[dict[str, Any]] | None = None,
    ) -> bool:
        """
        Update the status message in-place with the final response, card, or attachments.

        Returns True if updated in-place, or False if no status message exists.
        """
        if not self.status_ts:
            return False
        try:
            safe_text = (
                f"{text[: MAX_STATUS_TEXT_LENGTH - 3].rstrip()}..."
                if len(text) > MAX_STATUS_TEXT_LENGTH
                else text
            )
            update_kwargs: dict[str, Any] = {
                "channel": self.channel_id,
                "ts": self.status_ts,
                "text": safe_text,
            }
            if blocks is not None:
                update_kwargs["blocks"] = blocks
            if attachments is not None:
                update_kwargs["attachments"] = attachments
            await self.client.chat_update(**update_kwargs)
            self.has_finalized = True
            return True
        except Exception as exc:
            logger.warning(f"Failed to finalize status message: {exc}")
            return False

    async def cleanup(self) -> None:
        """Delete the temporary status message only if unfinalized (e.g. on error)."""
        if not self.status_ts or self.has_finalized:
            self.status_ts = None
            return
        try:
            await self.client.chat_delete(
                channel=self.channel_id,
                ts=self.status_ts,
            )
        except Exception as exc:
            logger.debug(f"Failed to delete unfinalized status message: {exc}")
        finally:
            self.status_ts = None

    async def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        **kwargs: Any,
    ) -> None:
        """Callback triggered when LangGraph executes a tool node."""
        tool_name = str(serialized.get("name", ""))
        inputs = kwargs.get("inputs")
        inputs_dict = inputs if isinstance(inputs, dict) else {}
        status_text = self._format_tool_status(tool_name, inputs_dict)
        await self.update(status_text)

    def _format_tool_status(self, tool_name: str, inputs: dict[str, Any]) -> str:
        """Format a user-friendly status message based on tool name and parameters."""
        if tool_name == "web_search":
            query = str(inputs.get("query", "")).strip()
            return (
                f'🔍 _Searching the web for "{query[:60]}"..._'
                if query
                else "🔍 _Searching the web..._"
            )

        if tool_name == "fetch_web_page":
            domain = self._extract_domain(str(inputs.get("url", "")).strip())
            return (
                f"📄 _Reading article from {domain}..._" if domain else "📄 _Reading web page..._"
            )

        if tool_name == "generate_chart":
            chart_type = str(inputs.get("chart_type", "data")).strip()
            return f"📊 _Generating {chart_type} chart..._"

        if tool_name == "propose_file_write":
            file_name = str(inputs.get("file_name", "")).strip()
            return (
                f"✍️ _Drafting report proposal for '{file_name}'..._"
                if file_name
                else "✍️ _Drafting report proposal..._"
            )

        return f"⚙️ _Running {tool_name}..._"

    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extract a readable domain name from a URL."""
        try:
            parsed = urlparse(url)
            netloc = parsed.netloc or parsed.path.split("/")[0]
            if netloc.startswith("www."):
                netloc = netloc[4:]
            return netloc
        except Exception:
            return ""
