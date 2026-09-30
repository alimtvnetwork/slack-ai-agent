from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChecklistItem:
    """Individual compliance standard checklist item from KITA guidelines."""

    item_id: str
    category: str
    title: str
    standard_code: str
    description: str


_KITA_COMPLIANCE_CHECKLIST: list[ChecklistItem] = [
    # Category 1: Marketing and Communications
    ChecklistItem(
        item_id="1.1",
        category="Marketing & Communications",
        title="Regulator and NRT Logo Compliance",
        standard_code="(CS13) & (CSS2)",
        description=(
            "Regulator and Nationally Recognised Training (NRT) logo use is "
            "compliant with current Standards for RTOs."
        ),
    ),
    ChecklistItem(
        item_id="1.2",
        category="Marketing & Communications",
        title="NRT Logo Direct Advertising",
        standard_code="(CSS23,2)",
        description=(
            "Used on advertising and marketing only in direct relationship "
            "to nationally recognised training."
        ),
    ),
    ChecklistItem(
        item_id="1.3",
        category="Marketing & Communications",
        title="NRT Logo Student Information",
        standard_code="(CSS2,6)",
        description=(
            "Used on student brochures and course information only in respect "
            "to nationally recognised training."
        ),
    ),
    ChecklistItem(
        item_id="1.4",
        category="Marketing & Communications",
        title="No NRT Logo on Stationery",
        standard_code="(CSS2,7)",
        description=(
            "NRT logo is NOT used on corporate stationery, business cards, "
            "general signage, or learning resources."
        ),
    ),
    ChecklistItem(
        item_id="1.5",
        category="Marketing & Communications",
        title="RTO Code Displayed",
        standard_code="(CS71a)",
        description="Clearly displays KI Training and Assessing RTO code (52593).",
    ),
    ChecklistItem(
        item_id="1.6",
        category="Marketing & Communications",
        title="Accredited vs Non-Accredited Distinction",
        standard_code="(CS71b)",
        description=(
            "Clear distinction between nationally recognised training leading to AQF "
            "certification and non-accredited training."
        ),
    ),
    ChecklistItem(
        item_id="1.7",
        category="Marketing & Communications",
        title="Estimated Course Duration",
        standard_code="(OS2.1c(i))",
        description=(
            "Includes estimated duration from commencement to completion for "
            "training and/or assessment."
        ),
    ),
    ChecklistItem(
        item_id="1.8",
        category="Marketing & Communications",
        title="Within KITA Scope of Registration",
        standard_code="(CS72b)",
        description=(
            "All training products advertised are strictly within KI Training "
            "and Assessing scope of registration."
        ),
    ),
    ChecklistItem(
        item_id="1.9",
        category="Marketing & Communications",
        title="Code and Full Title on National Register",
        standard_code="(CS72a) & (OS2.1c(i))",
        description=(
            "Includes official unit/qualification code and full title as listed on training.gov.au."
        ),
    ),
    ChecklistItem(
        item_id="1.10",
        category="Marketing & Communications",
        title="Clear Responsible RTO Identity",
        standard_code="(CS72)",
        description=(
            "The RTO responsible for delivery and assessment is absolutely "
            "clear to anyone viewing the content."
        ),
    ),
    ChecklistItem(
        item_id="1.11",
        category="Marketing & Communications",
        title="Scope Currency and Transition",
        standard_code="(CS72c(i))",
        description=(
            "Products are current and on scope, OR superseded within 12 months "
            "of new qualification release."
        ),
    ),
    # Category 2: Images / Reference to Others
    ChecklistItem(
        item_id="2.1",
        category="Images & Attribution",
        title="Third-Party Reference Consent",
        standard_code="(CS71d)",
        description=(
            "Only refers to another person, client, or organisation if written "
            "consent has been obtained."
        ),
    ),
    ChecklistItem(
        item_id="2.2",
        category="Images & Attribution",
        title="Image Quality and Person Consent",
        standard_code="(CS71d)",
        description=(
            "Images are appropriate quality and only depict individuals who "
            "have granted explicit consent."
        ),
    ),
    ChecklistItem(
        item_id="2.3",
        category="Images & Attribution",
        title="Copyright Ownership / Acknowledgment",
        standard_code="(CS71d)",
        description=(
            "Copyright is held by KITA or third-party intellectual property is "
            "formally acknowledged."
        ),
    ),
    # Category 3: General Claims, Guarantees & Regulatory Requirements
    ChecklistItem(
        item_id="3.1",
        category="General & Guarantees",
        title="Accurate, Clear, and Factual Information",
        standard_code="(OS2.1a)",
        description="Write-up is accurate, clear, current, and contains only factual information.",
    ),
    ChecklistItem(
        item_id="3.2",
        category="General & Guarantees",
        title="Consistent with TAS",
        standard_code="(CS2.1)",
        description="Content is consistent with KITA Training and Assessment Strategies.",
    ),
    ChecklistItem(
        item_id="3.3",
        category="General & Guarantees",
        title="NO Employment Guarantees",
        standard_code="(CS8c)",
        description=(
            "Strict prohibition: Does NOT guarantee any employment outcome following the training."
        ),
    ),
    ChecklistItem(
        item_id="3.4",
        category="General & Guarantees",
        title="NO Completion Guarantees",
        standard_code="(CS8a)",
        description=(
            "Strict prohibition: Does NOT guarantee that the learner will "
            "successfully complete the training product."
        ),
    ),
    ChecklistItem(
        item_id="3.5",
        category="General & Guarantees",
        title="NO Inconsistent Fast-Tracking",
        standard_code="(CS8b)",
        description=(
            "Does not promise completion in a manner inconsistent with "
            "training package requirements under Section 185."
        ),
    ),
    ChecklistItem(
        item_id="3.6",
        category="General & Guarantees",
        title="Delivery Location Disclosed",
        standard_code="(OS2.1c(i))",
        description=(
            "Includes delivery location(s) for the training products "
            "(e.g. Welshpool, Naval Base, or On-site)."
        ),
    ),
    ChecklistItem(
        item_id="3.7",
        category="General & Guarantees",
        title="Factual Licence Eligibility Claims",
        standard_code="(CS7(2)(d))",
        description=(
            "Any statement that a learner will be eligible for a licence "
            "or accreditation is strictly factual."
        ),
    ),
    ChecklistItem(
        item_id="3.8",
        category="General & Guarantees",
        title="Accurate URLs",
        standard_code="General",
        description=(
            "All hyperlinks, contact addresses, and website URLs are active, "
            "accurate, and functional."
        ),
    ),
    ChecklistItem(
        item_id="3.9",
        category="General & Guarantees",
        title="Regulatory Arrangements Met",
        standard_code="General",
        description=(
            "Material meets Australian states and territories (WA WorkSafe / ASQA) "
            "regulatory arrangements."
        ),
    ),
    ChecklistItem(
        item_id="3.10",
        category="General & Guarantees",
        title="Regulator Confirmation for Licensing",
        standard_code="(CR72d) & (OS2.1c(i))",
        description=(
            "Only markets that successful completion results in a licensed "
            "outcome if confirmed by industry regulator."
        ),
    ),
    ChecklistItem(
        item_id="3.11",
        category="General & Guarantees",
        title="Separation of Non-Recognised Courses",
        standard_code="(CS71b)",
        description=(
            "Any non-nationally recognised training is separated from other "
            "marketing and clearly identified as such."
        ),
    ),
]


def get_compliance_checklist() -> list[ChecklistItem]:
    """Return all active KITA compliance checklist items."""
    return list(_KITA_COMPLIANCE_CHECKLIST)


def format_checklist_for_prompt() -> str:
    """Format checklist items into a structured prompt guide for LLM compliance auditing."""
    sections: list[str] = ["### KITA ASQA / STANDARDS FOR RTOS MARKETING COMPLIANCE RULES:"]
    current_category = ""

    for item in _KITA_COMPLIANCE_CHECKLIST:
        if item.category != current_category:
            current_category = item.category
            sections.append(f"\n**{current_category.upper()}:**")

        sections.append(
            f"• [{item.item_id}] {item.title} (Standard: {item.standard_code}): {item.description}"
        )

    return "\n".join(sections)
