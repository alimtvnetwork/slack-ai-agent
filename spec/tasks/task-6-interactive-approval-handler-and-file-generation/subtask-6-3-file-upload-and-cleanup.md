# Subtask 6.3: Slack File Upload & Proposal Cleanup

> **Task Reference:** `TASK-06` > `SUBTASK-6.3`  
> **Source Rule:** `agent_rules/01-python-guidelines.md` §3, `agent_rules/03-error-handling-architecture.md` §5  

---

## 1. Description

Implement `src/slack/uploader.py` to upload generated file bytes into the target Slack conversation thread using `client.files_upload_v2`, post an accompanying confirmation message, and evict the proposal from the state store.

---

## 2. Requirements & Implementation Details

### 2.1 File: `src/slack/uploader.py`
```python
async def upload_generated_document(
    client: AsyncWebClient,
    channel_id: str,
    thread_ts: str,
    file_bytes: bytes,
    file_name: str,
    title: str,
) -> Result[dict[str, Any]]:
    """Upload generated document directly to the Slack conversation thread."""
    try:
        # files_upload_v2 is Slack's official modern replacement for files_upload
        response = await client.files_upload_v2(
            channel=channel_id,
            thread_ts=thread_ts,
            file=file_bytes,
            filename=file_name,
            title=title,
            initial_comment=f"📄 Here is your generated document: `{file_name}`",
        )
        return Result.ok(dict(response.data))
    except Exception as exc:
        return Result.fail(
            AppError.wrap(
                exc,
                code="E7004",
                message="Failed to upload generated document via Slack files.upload_v2",
                context={"ChannelId": channel_id, "FileName": file_name},
            )
        )
```

### 2.2 Complete Approval Workflow
1. Retrieve proposal from store: `get_proposal(proposal_id)`.
2. Generate file bytes: `generate_pdf_bytes()` or `generate_docx_bytes()`.
3. Upload to thread: `upload_generated_document()`.
4. Delete proposal from store: `delete_proposal(proposal_id)`.
5. Post completion thread message confirming delivery.

---

## 3. Verification

Create unit test `tests/unit/test_uploader.py`:
1. Mock `files_upload_v2` call: successfully uploads and returns Slack response payload.
2. Verify proposal is deleted from store upon successful upload.
3. Test failure in upload: leaves structured `AppError` log and notifies user of failure in thread.
