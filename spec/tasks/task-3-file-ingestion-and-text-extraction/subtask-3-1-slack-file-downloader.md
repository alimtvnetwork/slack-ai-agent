# Subtask 3.1: Authenticated Slack File Downloader

> **Task Reference:** `TASK-03` > `SUBTASK-3.1`  
> **Source Rule:** `agent_rules/01-python-guidelines.md` §6.1, `agent_rules/03-error-handling-architecture.md`  

---

## 1. Description

Implement `src/files/downloader.py` to stream and download file bytes from Slack's authenticated private URLs (`url_private_download`), validating file size against security boundaries.

---

## 2. Requirements & Implementation Details

### 2.1 File: `src/files/downloader.py`
- Function Signature:
  ```python
  async def download_slack_file(
      download_url: str,
      bot_token: str,
      max_bytes: int = 10 * 1024 * 1024,
  ) -> Result[bytes]:
  ```
- **Authentication:** Must include `Authorization: Bearer <bot_token>` header in request.
- **Streaming Guard:** Stream response in chunks. If total bytes exceed `max_bytes` (10 MB), abort download immediately and return:
  ```python
  return Result.fail(
      AppError(
          code=ERR_FILE_DOWNLOAD_FAILED,
          message=f"File exceeds maximum allowed size of {max_bytes} bytes",
          category=ErrorCategoryType.Validation,
          context={"DownloadUrl": download_url, "MaxBytes": max_bytes},
      )
  )
  ```
- **Error Wrapping:** Catch `httpx.HTTPError`, `httpx.TimeoutException` and wrap in `AppError.wrap()`.

---

## 3. Verification

Create unit test `tests/unit/test_file_downloader.py`:
1. Mock HTTP 200 response: correctly returns `Result.ok(bytes)`.
2. Mock HTTP 403 response: returns `Result.fail(AppError)` with code `E5001`.
3. Mock stream exceeding 10 MB: aborts and returns validation failure.
