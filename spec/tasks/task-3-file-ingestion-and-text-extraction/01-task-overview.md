# Task 3: File Ingestion & Multi-Format Text Extraction

> **Task ID:** `TASK-03`  
> **Target Capabilities:** Extract text from PDFs, DOCX, CSV, and code files uploaded to Slack channels and DMs.  
> **Libraries:** `httpx`, `pypdf`, `python-docx`  
> **Status:** Pending Implementation  

---

## 1. Objective

Implement an authenticated file downloader that fetches files from Slack's private CDN, parses them across multiple formats (PDF, Word DOCX, CSV, plain text, and code files), enforces size limits, and securely formats the extracted content for injection into the LangGraph agent prompt.

---

## 2. Subtask Breakdown

| Subtask ID | File | Summary |
|---|---|---|
| **SUBTASK-3.1** | [`subtask-3-1-slack-file-downloader.md`](subtask-3-1-slack-file-downloader.md) | Authenticated HTTP download of user-uploaded files using `httpx.AsyncClient` with bearer token auth and `max_file_size_bytes` guard. |
| **SUBTASK-3.2** | [`subtask-3-2-multiformat-parsers.md`](subtask-3-2-multiformat-parsers.md) | In-memory text extraction for PDF (`pypdf.PdfReader`), DOCX (`docx.Document`), CSV, and code/text files, returning `Result[str]`. |
| **SUBTASK-3.3** | [`subtask-3-3-content-injection-and-chunking.md`](subtask-3-3-content-injection-and-chunking.md) | File metadata structuring, size-aware truncation/chunking, and prompt synthesis prepending extracted content to the user's inquiry. |

---

## 3. Success Criteria

1. Authenticated downloads succeed from Slack `url_private_download` URLs using the bot token.
2. Text accurately extracted from multi-page PDFs, complex DOCX documents, CSV spreadsheets, and code files.
3. Corrupt or unparseable files return typed `AppError` without crashing the application.
