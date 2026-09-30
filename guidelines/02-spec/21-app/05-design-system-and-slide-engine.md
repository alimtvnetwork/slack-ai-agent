# 05 — Design System, CSS3 Building Blocks & Slide Presentation Engine

> **/goal** Architect a unified, high-craft design system specification covering modern color grading, beginner-friendly building blocks explained via standalone SVGs, darkish professional hover effects with subtle shade elevation, CSS3 animations, native select customization with organic border shapes, and a slide presentation engine inspired by local multi-deck presentation repositories.
> **/learn** Master the extraction of visual design tokens, 4-plane dark materiality, subtle non-white-blended hover elevations, CSS3 transition curves, native `appearance: base-select` with `::picker(select)`, organic layouts with `border-shape`, and the 16:9 responsive slide presentation engine architecture.

**Version:** 1.0.0
**Updated:** 2026-09-24
**Status:** Active
**AI Confidence:** High
**Ambiguity:** None

---

## User Request (Verbatim)

```text
read first please
[REFERENCE_AI_ENGINEERING_PORTAL]
[REFERENCE_AI_CERTIFICATION_PORTAL]
[REFERENCE_SCREENSHOT_01]
[REFERENCE_SCREENSHOT_02]
[REFERENCE_SCREENSHOT_03]

[PRESENTATIONS_REPOS_ROOT]

I want you to understand this website, get the color grading, how the sections are created. Okay, so based on that, you would put some examples. You do not put this image, which I have given you, but you try to explain it, okay? Like SVG or some sort. So here, the idea is that you try to explain it in a way so that AI can understand these blocks, building blocks. Okay? The hover effect, animation, CSS3 animations. So those are the things, very important, like hover effect, a little bit of shade, things like that, that needs to be explained very detailed way to AI. Let's say I hover over a line that have a hover over effect that is not blended in with the white, because it needs to be darkish color, but also at the same time, it needs to feel like it is done by professional...
```

---

## Actionable Extracted Deliverables

- **Task-01: Multi-Theme Design Tokens & LESS Stylesheet Pipeline**
  - Author machine-readable design tokens in `02-spec/07-design-system/tokens/design-tokens.json` supporting Light High-Trust, Dark Obsidian Navy, Corporate Riseup, and Electric Indigo themes.
  - Author modular LESS mixins and variables in `02-spec/07-design-system/tokens/theme-palette.less` with explicit preference for LESS over CSS.
  - Enforce darkish professional hover states (`rgba(15, 23, 42, 0.06)` on light surfaces, `rgba(2, 6, 23, 0.45)` shadow bloom) that never wash out or blend into white.

- **Task-02: CSS3 Keyframe Animations & Hover Transition Specifications**
  - Author `02-spec/07-design-system/21-css3-animations-and-interactions.md`.
  - Detail physics-based cubic-bezier easing curves (`cubic-bezier(0.16, 1, 0.3, 1)`), line hover highlight effects, border glow animations, infinite marquee ribbons, zero-JS fluid accordions, rotating neon borders, and strict `prefers-reduced-motion` fallbacks.

- **Task-03: Modern CSS Capabilities — Native Select & Border Shapes**
  - Author `02-spec/07-design-system/22-native-css-select-and-border-shapes.md`.
  - Detail `appearance: base-select`, `::picker(select)`, `<selectedcontent>`, arrow rotation on `select:open`, and organic layouts via `border-shape` (solid blobs, cutouts, outlines).

- **Task-04: Building Blocks Component Architecture with Standalone SVGs**
  - Author `02-spec/07-design-system/23-building-block-components.md` explaining component anatomy like explaining to a five-year-old child.
  - Generate standalone SVG visual diagrams in `02-spec/07-design-system/svgs/` illustrating card structures (`card-anatomy.svg`), hover mechanics (`hover-elevation.svg`), curriculum modules (`curriculum-card.svg`), 3-tier pricing tables (`pricing-tiers.svg`), and slide layouts (`slide-layout.svg`) without external screenshots.
  - Detail high-trust editorial whiteness and floating containers inspired by clean digital agency portals.

- **Task-05: Slide Presentation Engine Architecture**
  - Author `02-spec/07-design-system/24-slide-presentation-system.md` synthesizing patterns from `presentations-repos` (16:9 responsive canvas, draggable webcam PIP overlay, incremental step reveals, dual-screen presenter mode).

- **Task-06: Antigravity Skills Hygiene & Expansion**
  - Fix frontmatter in `.agents/skills/fix-spec-from-audit/skill.md`.
  - Rename uppercase `SKILL.md` to `skill.md` in `gitmap` and `movie-cli-migration-and-optimization`.
  - Author `.agents/skills/prompts-and-skills-sync/skill.md` for synchronization across connected repositories.

- **Task-07: Master Index Enrichment & Multi-Theme Cataloging**
  - Update `02-spec/07-design-system/readme.md` with action-oriented AI reading checklists, 8 standardized short-form theme identifiers (`LIGHT-TRUST`, `DARK-NAVY`, `RISEUP-CORP`, `CYBER-INDIGO`, `VSCODE-DARK`, `TOKYO-NIGHT`, `ONEDARK-PRO`, `WARM-PAPER`), CSS3 animations roster, and direct HTML/LESS live code samples.

---

## Architectural Contracts

### 1. Color Grading & Surface Contrast Matrix

| Role | Token Name | Light Surface | Dark Obsidian Navy | Intent & Usage |
|:---|:---|:---|:---|:---|
| Primary Ground | `@bg-primary` | `#ffffff` | `#0b1329` | Base application viewport surface |
| Elevated Surface | `@bg-elevated` | `#f8fafc` | `#111c44` | Card bodies, dropdown containers, slide panels |
| Accent Brand | `@color-accent` | `#6366f1` | `#8b5cf6` | Focus indicators, active badges, highlights |
| Darkish Hover Tint | `@hover-darkish`| `rgba(15, 23, 42, 0.05)` | `rgba(255, 255, 255, 0.07)` | High-craft hover tone maintaining dark visibility |
| Deep Shadow Bloom | `@shadow-depth` | `0 20px 40px -15px rgba(15, 23, 42, 0.12)` | `0 25px 50px -12px rgba(2, 6, 23, 0.70)` | Professional elevation without muddy gray |

### 2. Styling Technology Preference Mandate

```less
// LESS is the preferred styling language across this specification.
// Every component provides modular LESS mixins alongside raw CSS equivalents.
.theme-card() {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: 1rem;
  transition: transform 300ms cubic-bezier(0.16, 1, 0.3, 1),
              box-shadow 300ms cubic-bezier(0.16, 1, 0.3, 1),
              background-color 200ms ease;

  &:hover {
    transform: translateY(-4px);
    background-color: var(--bg-surface-hover);
    box-shadow: 0 20px 40px -15px var(--shadow-color-hover);
  }
}
```

---

## Verification & Acceptance Gates

1. **Zero External URLs:** Specifications must contain zero live third-party URLs.
2. **Zero Forbidden Words:** Banned intensifiers and hyperbolic colloquialisms must not appear in any spec, file, or comment.
3. **Strict Lowercase File Naming:** All paths and files must use strictly lowercase naming.
4. **Standalone SVGs:** Component diagrams must be pure standalone SVGs located in `02-spec/07-design-system/svgs/`.
5. **No Breaking Linter Failures:** All documentation checks must pass cleanly.
