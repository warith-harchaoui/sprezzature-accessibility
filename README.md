# sprezzature-accessibility

[![License](https://img.shields.io/badge/license-BSD--3--Clause-blue.svg)](https://github.com/warith-harchaoui/sprezzature-accessibility/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)

[🇫🇷 LISEZMOI.md](https://github.com/warith-harchaoui/sprezzature-accessibility/blob/main/LISEZMOI.md) · 🇬🇧 README.md

[![logo](https://raw.githubusercontent.com/warith-harchaoui/sprezzature-accessibility/main/assets/logo.png)](https://harchaoui.org/warith/sprezzature/)

A web page is accessible when someone using a screen reader, a keyboard alone (no
mouse), or a browser's reduced-motion setting can still use it. This tool checks HTML
source code for the mistakes that most often break that: an `<img>` with no `alt` text
is as invisible to a screen reader as if the image were simply missing from the page.

It is a static linter: fourteen rules from WCAG (Web Content Accessibility
Guidelines, the W3C standard that defines what "accessible" means for the web) and
WAI-ARIA (the attribute vocabulary, `role`, `aria-label` and the like, that lets custom
widgets describe themselves to assistive software), each one decidable by reading the
HTML text alone. No browser opens, no page renders, no JavaScript runs, so there is no
DOM (the tree of elements a browser builds while rendering a page) to inspect and
nothing to install beyond Python itself. That is what makes it fast enough for a
pre-commit hook or a CI step: a deterministic gate before any change lands in
production.

The violations it covers account for the bulk of real-world accessibility failures:
missing alt text, unlabelled inputs, empty buttons, clickable `<div>`s a keyboard
cannot reach, dialogs with no way to close them by keyboard, missing `lang` attributes
(which break screen-reader pronunciation), heading levels that jump around instead of
nesting in order, status shown by color alone (a red/green pair that a colorblind
reader cannot tell apart), and animations with no way to turn them down for someone
sensitive to motion. Five of those fourteen rules also ship a mechanical auto-fix
(`--fix`), so the gate can repair what it safely can instead of only reporting it.

This tool only ever reads source code, so it cannot catch what only shows up once a
page actually renders in a browser: keyboard focus order, screen-reader announcement
timing, color contrast against a real background. Pair it with axe-core, Pa11y, or
Lighthouse, which drive a real browser, for that layer. The two are complementary, not
interchangeable: this one is the fast, no-browser first gate; those are the slower,
browser-accurate second pass.

## Features

- 14 rules covering img, a, button, div/span, input, dialog, html, tabindex, aria,
  heading order, color-only state, and motion-reduce guards
- Auto-fix for 5 rules: lang detection + insertion, redundant aria removal, tabindex
  demotion, aria-hidden strip, motion-reduce guard append
- Text and JSON output formats, composable with jq or any CI parser
- Exit code 1 on any finding (exit 0 on clean), suitable as a pre-commit gate
- Stdlib only at runtime: Python 3.10+, no pip install required for the core
- Optional `langdetect` for the `html-missing-lang` auto-fixer (language detection)

## Quick start

```bash
# Lint a single page
python scripts/lint_a11y.py public/index.html

# Lint a directory recursively, exit 1 on any finding
python scripts/lint_a11y.py public/

# JSON output for CI pipeline consumption
python scripts/lint_a11y.py --format json public/index.html

# Suppress two rules
python scripts/lint_a11y.py --ignore heading-skip,motion-no-reduce-guard public/

# Auto-fix what can be fixed mechanically
python scripts/lint_a11y.py --fix public/

# Preview what --fix would change, without writing
python scripts/lint_a11y.py --fix --dry-run public/
```

## Install

```bash
pip install sprezzature-accessibility
# With language detection for the html-missing-lang fixer:
pip install "sprezzature-accessibility[lang]"
```

Or run directly without install:

```bash
python scripts/lint_a11y.py public/
```

## Rules

| Rule | Severity | Description |
|---|---|---|
| `img-missing-alt` | error | `<img>` without alt attribute |
| `img-redundant-aria` | warning | `alt=""` with redundant role/aria-hidden |
| `a-missing-href` | error | `<a>` without href (use `<button>`) |
| `a-empty` | error | `<a>` with no accessible name |
| `button-empty` | error | `<button>` with no accessible name |
| `div-onclick` | error | onclick div/span without role+tabindex |
| `input-missing-label` | error | `<input>` without associated label |
| `dialog-missing-close` | error | `<dialog>` without close affordance |
| `html-missing-lang` | error | `<html>` without lang attribute |
| `tabindex-positive` | error | tabindex >= 1 breaks DOM order |
| `aria-hidden-interactive` | error | aria-hidden on interactive element |
| `heading-skip` | error | headings skip levels downward |
| `color-only-state` | warning | red/green token with no icon or text |
| `motion-no-reduce-guard` | warning | animation without motion-reduce peer |

## License

BSD-3-Clause. Copyright 2026 Warith HARCHAOUI.
