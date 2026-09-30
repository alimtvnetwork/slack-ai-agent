from __future__ import annotations

import httpx

from slack_agent.core.errors import (
    ERR_FILE_DOWNLOAD_FAILED,
    AppError,
    ErrorCategoryType,
)
from slack_agent.core.result import Result

HTTP_STATUS_OK = 200


async def download_slack_file(
    download_url: str,
    bot_token: str,
    max_bytes: int = 10 * 1024 * 1024,
) -> Result[bytes]:
    """Download user-uploaded file bytes from Slack private download URL."""
    headers = {"Authorization": f"Bearer {bot_token}"}
    try:
        async with (
            httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client,
            client.stream("GET", download_url, headers=headers) as response,
        ):
            if response.status_code != HTTP_STATUS_OK:
                return Result.fail(
                    AppError(
                        code=ERR_FILE_DOWNLOAD_FAILED,
                        message=f"Slack file download returned HTTP {response.status_code}",
                        category=ErrorCategoryType.SlackApi,
                        context={"StatusCode": response.status_code, "Url": download_url},
                    )
                )

            content_chunks: list[bytes] = []
            total_bytes = 0
            async for chunk in response.aiter_bytes():
                total_bytes += len(chunk)
                if total_bytes > max_bytes:
                    return Result.fail(
                        AppError(
                            code=ERR_FILE_DOWNLOAD_FAILED,
                            message=f"File exceeds maximum allowed size of {max_bytes} bytes",
                            category=ErrorCategoryType.Validation,
                            context={"MaxBytes": max_bytes, "DownloadedBytes": total_bytes},
                        )
                    )
                content_chunks.append(chunk)

            return Result.ok(b"".join(content_chunks))
    except Exception as exc:
        return Result.fail(
            AppError.wrap(
                exc,
                code=ERR_FILE_DOWNLOAD_FAILED,
                message="Network error during Slack file download",
                category=ErrorCategoryType.Network,
                context={"DownloadUrl": download_url},
            )
        )
