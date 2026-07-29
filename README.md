# sprezzature-accessibility

[![License](https://img.shields.io/badge/license-BSD--3--Clause-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)

[🇫🇷 LISEZMOI.md](LISEZMOI.md) · 🇬🇧 README.md

[![logo](assets/logo.png)](https://harchaoui.org/warith/sprezzature/)

A static accessibility linter for HTML: fourteen WCAG/WAI rules that are decidable from
source, without a browser, without a runtime DOM, without network access. Drop it into a
pre-commit hook or a CI step and get a fast, deterministic gate before any diff lands in
production.

The linter covers the violations that account for the bulk of real-world accessibility
failures: missing alt text, unlabelled inputs, empty buttons, clickable divs, missing
dialog close affordances, absent lang attributes, inverted heading order, color-only
state cues, and missing reduced-motion guards. Five of those rules also have a mechanical
auto-fix mode (`--fix`) so the gate can self-heal what it can.

This is not a substitute for runtime DOM testing. Pair it with axe-core, Pa11y, or
Lighthouse for browser-time checks. This tool catches what a browser never sees.

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
