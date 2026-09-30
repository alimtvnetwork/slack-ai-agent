"""Interactive preview script demonstrating raw markdown vs Slack beautified output."""

from __future__ import annotations

import json
import sys

# Ensure UTF-8 output on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from slack_agent.slack.blocks.response_card import (
    ResponseCardParams,
    build_response_attachment,
    format_slack_mrkdwn,
)

SAMPLE_RAW_LLM_OUTPUT = """## Financial & Market Performance

> 📌 *Executive Summary:* Net quarterly revenue increased by **24.8% ($1.42M)**.

### Core Metrics
- Total Revenue: **$1,420,000** (vs. **$1,138,000** in Q3 2025)
- Net Retention: **114.2%** across Enterprise accounts
- See full documentation at [SEC 10-Q Filing](https://sec.gov/filing/q3)

### Code & Automation Snippet
```python
# Verification script - code blocks are preserved intact
def verify_margin(revenue: float, cost: float) -> float:
    margin = (revenue - cost) / revenue
    return margin  # **not_bold** preserved
```

### Next Steps
1. Finalize regional allocations for Q4.
2. Review churn mitigation plan.
"""


def main() -> None:
    print("\n" + "=" * 70)
    print(" 1. RAW LLM OUTPUT (Standard Markdown)")
    print("=" * 70)
    print(SAMPLE_RAW_LLM_OUTPUT)

    print("=" * 70)
    print(" 2. BEAUTIFIED SLACK MRKDWN")
    print("=" * 70)
    beautified = format_slack_mrkdwn(SAMPLE_RAW_LLM_OUTPUT)
    print(beautified)

    print("\n" + "=" * 70)
    print(" 3. SLACK BLOCK KIT ATTACHMENT PAYLOAD (Ready for Block Kit Builder)")
    print("=" * 70)
    params = ResponseCardParams(
        text=beautified,
        agent_name="AIAssistant",
        accent_color="#1A85FF",
        has_footer=True,
    )
    attachment = build_response_attachment(params)
    print(json.dumps(attachment, indent=2))

    print("\n💡 TIP: Copy the JSON above and paste it into:")
    print("   👉 https://app.slack.com/block-kit-builder")
    print("   to see the exact visual rendering in Slack desktop & mobile!\n")


if __name__ == "__main__":
    main()
