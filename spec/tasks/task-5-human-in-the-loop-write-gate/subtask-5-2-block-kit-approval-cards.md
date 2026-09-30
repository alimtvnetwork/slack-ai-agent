# Subtask 5.2: Block Kit Approval Card Builder

> **Task Reference:** `TASK-05` > `SUBTASK-5.2`  
> **Source Rule:** `agent_rules/02-general-coding-guidelines.md` §2.2  

---

## 1. Description

Construct the Slack Block Kit UI template in `src/slack/blocks/approval_card.py` that formats the interactive file write approval request.

---

## 2. Requirements & Block Kit Payload

### 2.1 File: `src/slack/blocks/approval_card.py`
The card contains 4 distinct UI sections:
1. **Header Block:** Plain text notification (`"📝 Document Generation Request"`).
2. **Context Section:** Target file name, format badge, and file size estimation.
3. **Summary Section:** Executive summary and preview snippet (max 300 chars).
4. **Actions Block:** Interactive buttons:
   - Button 1: **Approve & Write** (Primary green style, `action_id="approve_file_write"`, `value=proposal_id`).
   - Button 2: **Reject** (Danger red style, `action_id="reject_file_write"`, `value=proposal_id`).

```python
def build_approval_card(
    proposal_id: str,
    file_name: str,
    file_format: str,
    content_summary: str,
    preview_snippet: str,
) -> list[dict[str, Any]]:
    return [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "📝 Document Generation Request", "emoji": True},
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*File Name:*\n`{file_name}`"},
                {"type": "mrkdwn", "text": f"*Format:*\n`{file_format.upper()}`"},
            ],
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Summary:*\n{content_summary}\n\n*Preview:*\n> {preview_snippet[:300]}...",
            },
        },
        {
            "type": "actions",
            "block_id": f"write_approval_block_{proposal_id}",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Approve & Write", "emoji": True},
                    "style": "primary",
                    "action_id": "approve_file_write",
                    "value": proposal_id,
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Reject", "emoji": True},
                    "style": "danger",
                    "action_id": "reject_file_write",
                    "value": proposal_id,
                },
            ],
        },
    ]
```

---

## 3. Verification

Create unit test `tests/unit/test_approval_card_builder.py`:
1. Verify Block Kit JSON adheres to Slack Block Kit schema.
2. Verify both buttons contain the correct `action_id` and encode `proposal_id` in `value`.
