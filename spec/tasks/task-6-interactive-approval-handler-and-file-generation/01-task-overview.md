# Task 6: Interactive Approval Handlers & File Generation Engine

> **Task ID:** `TASK-06`  
> **Core Technologies:** `reportlab`, `python-docx`, Slack `files.upload_v2`, `slack_bolt` action handlers  
> **Status:** Pending Implementation  

---

## 1. Objective

Implement the interactive button callback listeners in Slack Socket Mode for `[Approve & Write]` and `[Reject]`, construct the document generation engine (using ReportLab for PDF, python-docx for Word, and raw text/csv encoders), upload approved files via `files.upload_v2`, and clean up proposal state.

---

## 2. Subtask Breakdown

| Subtask ID | File | Summary |
|---|---|---|
| **SUBTASK-6.1** | [`subtask-6-1-block-kit-action-listener.md`](subtask-6-1-block-kit-action-listener.md) | Register `@app.action("approve_file_write")` and `@app.action("reject_file_write")`, update Slack message card to reflect decision, and dispatch generation. |
| **SUBTASK-6.2** | [`subtask-6-2-reportlab-pdf-and-docx-engine.md`](subtask-6-2-reportlab-pdf-and-docx-engine.md) | Build PDF rendering engine with ReportLab (styles, headers, margins, typography) and DOCX builder with `python-docx`. |
| **SUBTASK-6.3** | [`subtask-6-3-file-upload-and-cleanup.md`](subtask-6-3-file-upload-and-cleanup.md) | Dispatch file bytes to Slack thread using `client.files_upload_v2`, post confirmation message, and evict proposal from memory cache. |

---

## 3. Success Criteria

1. Clicking `[Approve & Write]` renders a clean, styled PDF/DOCX and uploads it into the exact Slack thread where requested.
2. Clicking `[Reject]` updates the card to "Rejected by @user" and cleans up proposal cache without generating files.
3. Card updates in place so buttons cannot be clicked a second time.
