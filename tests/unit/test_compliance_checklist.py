from __future__ import annotations

from slack_agent.compliance.checklist import (
    format_checklist_for_prompt,
    get_compliance_checklist,
)


def test_compliance_checklist_contains_25_items() -> None:
    checklist = get_compliance_checklist()
    assert len(checklist) == 25


def test_compliance_checklist_categories() -> None:
    checklist = get_compliance_checklist()
    categories = {item.category for item in checklist}
    assert "Marketing & Communications" in categories
    assert "Images & Attribution" in categories
    assert "General & Guarantees" in categories


def test_compliance_critical_standards_present() -> None:
    checklist = get_compliance_checklist()
    items_by_id = {item.item_id: item for item in checklist}

    # 1.5 RTO Code 52593
    rto_code_item = items_by_id.get("1.5")
    assert rto_code_item is not None
    assert "52593" in rto_code_item.description

    # 3.3 No employment guarantees
    no_emp_item = items_by_id.get("3.3")
    assert no_emp_item is not None
    assert "guarantee any employment outcome" in no_emp_item.description.lower()

    # 3.4 No completion guarantees
    no_comp_item = items_by_id.get("3.4")
    assert no_comp_item is not None
    assert "successfully complete the training" in no_comp_item.description.lower()


def test_format_checklist_for_prompt() -> None:
    formatted = format_checklist_for_prompt()
    assert "KITA ASQA / STANDARDS FOR RTOS MARKETING COMPLIANCE RULES" in formatted
    assert "MARKETING & COMMUNICATIONS:" in formatted
    assert "IMAGES & ATTRIBUTION:" in formatted
    assert "GENERAL & GUARANTEES:" in formatted
    assert "(CS71a)" in formatted
    assert "(CS8c)" in formatted
