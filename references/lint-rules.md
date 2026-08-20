# The fourteen rules — WCAG/WAI-ARIA mapping and known limits

Each rule below maps to a specific Web Content Accessibility Guidelines
(WCAG, the W3C standard that defines what "accessible" means for the
web) success criterion or a WAI-ARIA (Web Accessibility Initiative,
Accessible Rich Internet Applications) authoring requirement, and is
decidable from the HTML source text alone, no browser, no rendered
DOM (the tree of elements a browser assembles while displaying a
page). This is the "why this rule, and where does it fall short"
document; for run commands and output shapes, see `EXAMPLES.md`.

## Rules with a WCAG success criterion

| Rule | WCAG SC | What it catches |
|---|---|---|
| `img-missing-alt` | 1.1.1 Non-text Content | `<img>` with no `alt` attribute at all. An empty `alt=""` is the correct way to mark a decorative image; *omitting* the attribute is the violation. |
| `html-missing-lang` | 3.1.1 Language of Page | `<html>` with no `lang`. A screen reader without a language hint may mispronounce every word on the page, not just foreign phrases. |
| `heading-skip` | 2.4.6 Headings and Labels (best practice reading) | Heading levels that jump downward (`<h2>` straight to `<h4>`). Screen-reader users navigate by heading level as a table of contents; a skipped level reads as a missing section. |
| `color-only-state` | 1.4.1 Use of Color | A Tailwind `text-red-*` / `bg-green-*` token with no accompanying icon or text. Roughly 1 in 12 men have some form of color vision deficiency; a status shown by hue alone disappears for them. |
| `motion-no-reduce-guard` | 2.3.3 Animation from Interactions (AAA, applied here as a house baseline) | An `animate-*` or `transition-transform` class with no `motion-reduce:` peer, so `prefers-reduced-motion` is silently ignored. |

## Rules grounded in WAI-ARIA authoring practice

| Rule | Requirement | What it catches |
|---|---|---|
| `a-missing-href` | An `<a>` without `href` has no link semantics or keyboard handling | `<a>` used as a click target instead of a real `<button>`. |
| `a-empty` | Every link needs an accessible name | `<a>` whose only content resolves to empty text (checked via `accessible_name()`, which aggregates `aria-label`, `title`, and all descendant text — not just direct text, so `<a><span>Label</span></a>` is read correctly). |
| `button-empty` | Every button needs an accessible name | Same check as `a-empty`, applied to `<button>`, with an icon-only exception when an `<svg>` or `<img>` descendant exists. |
| `div-onclick` | A non-interactive element with a click handler needs `role="button"` and `tabindex` to be keyboard-reachable | `<div>` / `<span>` with `onclick` but neither attribute. |
| `input-missing-label` | Every form control needs a programmatically associated label | `<input>` not wrapped in a `<label>`, not referenced by `<label for=...>`, and with no `aria-label`. Hidden, submit, button, reset, and image inputs are exempt. |
| `dialog-missing-close` | A modal needs a way to dismiss it without a mouse | `<dialog>` with no `<button>` whose `value` is `cancel`/`close`, no `autofocus` element, and no button text matching a small hardcoded set: "close", "cancel" (English), "fermer", "annuler" (French), "schließen" (German). **Known limit:** any other language's close/cancel wording is not recognized and will false-positive; add to the set in `check_dialog_close` (`lint_a11y.py`) as new cases come up. |
| `tabindex-positive` | A positive `tabindex` overrides natural DOM order, which usually surprises keyboard and screen-reader users | Any `tabindex` ≥ 1. `tabindex="0"` and `tabindex="-1"` are fine and not flagged. |
| `aria-hidden-interactive` | `aria-hidden="true"` removes an element from the accessibility tree entirely | A `button` / `a` / `input` / `select` / `textarea` with `aria-hidden="true"`, which makes it invisible to assistive technology while remaining visible and clickable on screen. |
| `img-redundant-aria` | Not a violation, a redundancy | `alt=""` (already the correct decorative marker) combined with `role="presentation"` or `aria-hidden="true"`. Harmless but redundant; flagged as a style warning, not an error. |

## What these fourteen rules do not cover

The linter is static by design (see `README.md` / `LISEZMOI.md` for why), so it cannot see:

- Keyboard focus order as the browser actually computes it (only the source-level `tabindex` anti-patterns above).
- Screen-reader announcement timing (live regions, focus management on route change).
- Real color contrast ratios against a rendered background — that is `sprezzature-colors/scripts/audit_contrast.py`'s job, not this linter's.
- Anything that only exists after JavaScript runs (content injected client-side, dynamically toggled `aria-*` states).

Pair this linter with `axe-core`, `Pa11y`, or `Lighthouse` for that layer; see `LANDSCAPE.md` / `PAYSAGE.md` for how the tools divide the work.
