from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from slack_sdk.web.async_client import AsyncWebClient

from slack_agent.core.errors import ERR_SLACK_UPLOAD_FAILED, AppError, ErrorCategoryType
from slack_agent.core.logger import get_logger
from slack_agent.core.result import Result

logger = get_logger(__name__)


@dataclass(frozen=True)
class UploadDocumentParams:
    """Parameters required to upload a document to a Slack conversation thread."""

    client: AsyncWebClient
    channel_id: str
    thread_ts: str
    file_bytes: bytes
    file_name: str
    title: str
    initial_comment: str = ""


async def upload_generated_document(params: UploadDocumentParams) -> Result[dict[str, Any]]:
    """Upload generated document directly to the Slack conversation thread using files.upload_v2."""
    comment = params.initial_comment or f"📄 Here is your generated document: `{params.file_name}`"
    try:
        response = await params.client.files_upload_v2(
            channel=params.channel_id,
            thread_ts=params.thread_ts,
            file=params.file_bytes,
            filename=params.file_name,
            title=params.title,
            initial_comment=comment,
        )
        data = getattr(response, "data", {})
        logger.info(
            "Uploaded file to Slack thread",
            extra={
                "ChannelId": params.channel_id,
                "ThreadTs": params.thread_ts,
                "FileName": params.file_name,
            },
        )
        return Result.ok(dict(data))
    except Exception as exc:
        err = AppError.wrap(
            exc,
            code=ERR_SLACK_UPLOAD_FAILED,
            message="Failed to upload generated file to Slack via files_upload_v2",
            category=ErrorCategoryType.SlackApi,
            context={"ChannelId": params.channel_id, "FileName": params.file_name},
        )
        logger.error(str(err))
        return Result.fail(err)
