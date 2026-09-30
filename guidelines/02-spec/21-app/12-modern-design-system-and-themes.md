# 12 — Modern Design System, Theme Architecture & AI Training Guide

> **/goal** Provide a comprehensive, portable, high-craft design system and multi-theme architecture inside `02-spec/07-design-system/`, equipped with machine-readable theme JSON, dark background principles, modern sliding/carousel interactions, and an exhaustive step-by-step train-and-learn checklist for AI assistants.
> **/learn** Master the 4-plane dark materiality, 60/30/10 visual balance, single-accent Von Restorff discipline, fluid typography hierarchy, and multi-theme palette models (Navy Blue & Purple, VS Code themes, heatmaps, and warm editorial).

**Version:** 4.0.0
**Updated:** 2026-09-24
**Status:** Active
**AI Confidence:** High
**Ambiguity:** None

---

## User Request (Verbatim)

```text
02-spec/07-design-system

Okay, now that you have understood the design concepts, UI, UX, and everything, I don't want you to modify anything in this site, but I want you to update the coding guideline. So first pull the coding guideline, and then whatever the design concepts that you learn, the sliding and things like that, you put this into the design system, okay? Along with the other aspects, and you improve the design system section inside the coding guideline with the modern approaches, just like from this, so that any AI can follow through and make nice UI interfaces. So you go through in many steps so that you can fine-tune it and any AI can be trained on navy blue and purple color themes. So it's not based on the Rise Up theme, but add different themes, like VS Code themes, color themes, heat map themes and colors as well. So you take most of these that we have, and you try to name these themes and put it inside the coding guideline spec folder, which is zero to spec folder, and then inside the design system, which is zero seven. You mention those design systems properly so that any AI can follow through these slides, specs. Okay? So try to have more information so that it's easier for a blind or low-quality AI to follow through. So write more, accurately write it, write it as a checklist, write it like a train and learn, put some goals into this, and AI should know which themes are available. Things like that. Do you understand? Also, for themes and colors, you can put a JSON there as well so that it's easier to understand what is what, and also a theme, why, what is used. With the dark background, why and how we should use it, typography information, how it needs to be used. So you get influence from this Rise Up Asia website. Do you understand? So I want you to go deep and improve the suspect inside the design system of the coding guideline. First things first, you should pull the code base for the coding guideline. Is it clear?
```

---

## Actionable Extracted Deliverables

- **Task-01: Pull & Inspect Coding Guidelines Codebase**
  - Verify git status in repository root, ensure clean working branch, pull latest upstream commits.
- **Task-02: Comprehensive Theme Catalogue & Palette Specification (`16-theme-catalogue-and-palettes.md`)**
  - Define complete theme families:
    1. Navy Blue & Purple Theme (Deep midnight navy ground, electric violet accent, cyan/ice highlights, subtle indigo depth).
    2. VS Code Theme Ecosystem (VS Code Dark+, Tokyo Night, One Dark Pro, GitHub Dark High Contrast, Monokai Pro).
    3. Heat Map & Density Themes (Sequential Plasma/Thermal, Diverging Red-Amber-Green, Activity/Contribution Green).
    4. Warm Editorial & Craft Theme (Warm paper light, warm-black `#0b0a09` base, single amber accent).
- **Task-03: Machine-Readable Theme Tokens JSON (`17-theme-tokens.json`)**
  - Export structured JSON containing all theme tokens (surface planes 0–3, text colors, accents, hairlines, glows, code block tokens, why/when to use metadata) for programmatic AI consumption.
- **Task-04: Dark Mode Architecture & Materiality Spec (`18-dark-mode-and-materiality.md`)**
  - Deep-dive guide explaining why pure black `#000000` fails, 4-plane neutral depth hierarchy (~4% lightness steps), hairline borders over drop shadows, progressive blur masking, grain/noise overlays, 60/30/10 weight balance, and single-accent Von Restorff rules.
- **Task-05: Modern Motion & Sliding Interaction Spec (`19-modern-motion-and-sliding-interactions.md`)**
  - Controlled sliding carousels, loop reset mechanics, directional entrance grammar (`maskUp`, `rise`, `drawRule`), section pacing, and strict `prefers-reduced-motion` compliance.
- **Task-06: AI Training & Anti-Slop Checklist Guide (`20-ai-training-and-checklist-guide.md`)**
  - Step-by-step train-and-learn rules for AI models, the 5-question above-the-fold contract, golden ratio composition, and the anti-AI-slop rubric.
- **Task-07: Core Design System Updates & Integration**
  - Synchronize `readme.md`, `02-design-principles.md`, `03-theme-variable-architecture.md`, `04-typography.md`, `08-motion-transitions.md`, and `13-section-patterns.md`.

---

## Architecture & System Context

```text
02-spec/07-design-system/
├── readme.md                                (Master Index updated with new specs)
├── 02-design-principles.md                    (Enhanced with 60/30/10, 4-plane depth)
├── 03-theme-variable-architecture.md          (Updated multi-theme variable registry)
├── 04-typography.md                           (Updated fluid clamp scale & tracking rules)
├── 08-motion-transitions.md                   (Updated with sliding & reveal tokens)
├── 13-section-patterns.md                     (Updated with asymmetric hero & carousels)
├── 16-theme-catalogue-and-palettes.md         (NEW: Comprehensive theme library)
├── 17-theme-tokens.json                       (NEW: Machine-readable theme JSON)
├── 18-dark-mode-and-materiality.md            (NEW: 4-plane depth, grain, progressive blur)
├── 19-modern-motion-and-sliding-interactions.md (NEW: Carousels, choreography, reduced motion)
└── 20-ai-training-and-checklist-guide.md      (NEW: Step-by-step AI checklist & training guide)
```

---

## Verification & Acceptance Gates

1. Zero modifications to `riseup-asia-website-project`.
2. All additions and modifications reside strictly in `02-spec/07-design-system/` and planning files.
3. Every theme family contains exact Hex, HSL, and semantic usage rules with explicit contrast verification.
4. `17-theme-tokens.json` parses as valid JSON with complete structural coverage.
5. All markdown files adhere to coding guideline standards (headings, checklists, zero banned operations, clean table formatting).
6. Changes are staged and committed in a single clean atomic commit and pushed to origin.
