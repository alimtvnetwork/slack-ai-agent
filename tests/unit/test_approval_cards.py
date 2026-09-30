from __future__ import annotations

from slack_agent.slack.blocks.approval_card import (
    ApprovalCardParams,
    EditProposalModalParams,
    build_approval_card,
    build_approved_status_card,
    build_edit_proposal_modal,
    build_rejected_status_card,
)


def test_build_approval_card_structure() -> None:
    params = ApprovalCardParams(
        proposal_id="prop-test-1",
        file_name="quarterly_report.pdf",
        file_format="pdf",
        content_summary="Summary of quarterly metrics",
        preview_snippet="Revenue reached $1.2M with 25% margin.",
    )

    blocks = build_approval_card(params)

    # 4 blocks: header, fields section, summary/preview section, actions block
    assert len(blocks) == 4
    assert blocks[0]["type"] == "header"
    assert "quarterly_report.pdf" in blocks[1]["fields"][0]["text"]
    assert "PDF" in blocks[1]["fields"][1]["text"]
    assert "Summary of quarterly metrics" in blocks[2]["text"]["text"]

    actions_block = blocks[3]
    assert actions_block["type"] == "actions"
    elements = actions_block["elements"]
    assert len(elements) == 3

    approve_btn = elements[0]
    assert approve_btn["action_id"] == "approve_file_write"
    assert approve_btn["value"] == "prop-test-1"
    assert approve_btn["style"] == "primary"

    edit_btn = elements[1]
    assert edit_btn["action_id"] == "edit_file_write_proposal"
    assert edit_btn["value"] == "prop-test-1"

    reject_btn = elements[2]
    assert reject_btn["action_id"] == "reject_file_write"
    assert reject_btn["value"] == "prop-test-1"
    assert reject_btn["style"] == "danger"


def test_build_edit_proposal_modal() -> None:
    modal_params = EditProposalModalParams(
        proposal_id="prop-test-edit",
        file_name="report.docx",
        file_format="docx",
        content="Existing document body.",
    )
    modal = build_edit_proposal_modal(modal_params)
    assert modal["type"] == "modal"
    assert modal["callback_id"] == "submit_edit_file_proposal"
    assert modal["private_metadata"] == "prop-test-edit"
    assert len(modal["blocks"]) == 3
    assert modal["blocks"][0]["element"]["initial_value"] == "report.docx"
    assert modal["blocks"][1]["element"]["initial_value"] == "docx"
    assert modal["blocks"][2]["element"]["initial_value"] == "Existing document body."


def test_build_approval_card_preview_truncation() -> None:
    long_snippet = "x" * 400
    params = ApprovalCardParams(
        proposal_id="prop-test-2",
        file_name="long_doc.docx",
        file_format="docx",
        content_summary="Long preview",
        preview_snippet=long_snippet,
    )

    blocks = build_approval_card(params)
    preview_text = blocks[2]["text"]["text"]
    assert "..." in preview_text
    assert len(long_snippet) > 280


def test_build_approved_and_rejected_cards() -> None:
    approved_blocks = build_approved_status_card("prop-test-3", "U12345")
    assert len(approved_blocks) == 1
    assert "approved by <@U12345>" in approved_blocks[0]["text"]["text"]

    rejected_blocks = build_rejected_status_card("prop-test-3", "U67890")
    assert len(rejected_blocks) == 1
    assert "rejected by <@U67890>" in rejected_blocks[0]["text"]["text"]
