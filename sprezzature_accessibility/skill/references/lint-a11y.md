# A11y linter: `sprezzature-accessibility-lint`

Static lint with no DOM (Document Object Model, the tree of elements a browser builds from a page), for CI (continuous integration, the checks a server runs on every change pushed to a repository) and pre-commit hooks. No browser, no JavaScript execution; it runs over HTML source. Catches **20 source-decidable failures** of WCAG (Web Content Accessibility Guidelines, the W3C's (World Wide Web Consortium, the body that writes the web's standards) rules for an accessible page) and WAI-ARIA (the Web Accessibility Initiative's Accessible Rich Internet Applications, the `role` and `aria-*` attributes that tell a screen reader what a custom widget is). Each WCAG rule is a numbered SC (success criterion, one testable requirement such as 1.1.1).

**Not a replacement for axe-core, Pa11y, or Lighthouse.** Those run a real browser and catch the dynamic / runtime failures that no static parser can see: colour-only state after JavaScript runs, focus order after a route change, name/role/value after a WAI-ARIA attribute changes, contrast after a runtime theme switch, live-region announcement order. Use `sprezzature-accessibility-lint` in pre-commit; use axe-core (or Pa11y, or Lighthouse) in your end-to-end suite. Run both.

## Install

```bash
pip install sprezzature-accessibility
```

The lint imports only the standard library and click (plus `langdetect`, a
base dependency, for `--fix`'s language guess); Python 3.10 to 3.13. The one
`pip install` puts `sprezzature-accessibility-lint` on `$PATH`, with the rest of
the package.

## Run

```bash
# A single page
sprezzature-accessibility-lint public/index.html

# A whole tree
sprezzature-accessibility-lint public/

# JSON output for CI
sprezzature-accessibility-lint --format json public/index.html

# Skip a couple of rules
sprezzature-accessibility-lint --ignore heading-skip,motion-no-reduce-guard public/

# Auto-fix the mechanically-fixable rules (6 of the 20)
sprezzature-accessibility-lint --fix --dry-run public/
```

Exit code is `0` when no findings, `1` when any finding is present, `2` on a usage error such as a path that does not exist. Pipe-friendly for CI.

## Rules

Each rule has a stable identifier so the `--ignore` flag and JSON (JavaScript Object Notation, named fields a script can read) output reference them.

| Rule | What it catches | Standard |
|---|---|---|
| `html-missing-lang` | `<html>` without a `lang` attribute. | WCAG SC 3.1.1 |
| `img-missing-alt` | `<img>` with no `alt` attribute at all (different from `alt=""`). | WCAG SC 1.1.1, W3C image decision tree. |
| `img-redundant-aria` | `alt=""` *plus* `role="presentation"` or `aria-hidden="true"`. `alt=""` alone is enough. | W3C Web Accessibility Initiative tutorial on decorative images. |
| `a-missing-href` | `<a>` without `href` (should be `<button>`). | WAI-ARIA Authoring Practices. |
| `a-empty` | `<a>` with no text, no `aria-label`, no `aria-labelledby`, no `title`, no inline image. | WCAG SC 2.4.4. |
| `button-empty` | `<button>` with no text, no `aria-label`, no `aria-labelledby`, no `title`, no inline icon. | WCAG SC 4.1.2. |
| `div-onclick` | `<div>` / `<span>` with `onclick` but no `role="button"` and no `tabindex`. | WCAG SC 2.1.1. |
| `input-missing-label` | `<input>` not wrapped in a `<label>`, not referenced by a `<label for=>`, and with neither `aria-label` nor `aria-labelledby`. Hidden, submit, button, reset and image inputs are exempt. | WCAG SC 3.3.2. |
| `dialog-missing-close` | `<dialog>` without an obvious close affordance (a button with `value="cancel"` or `value="close"`, `autofocus`, or accessible name "Close" / "Cancel" / "Fermer" / "Annuler" / "Schließen"). | WAI-ARIA modal pattern. |
| `tabindex-positive` | `tabindex` ≥ 1, which breaks DOM tab order. | WAI-ARIA Authoring Practices. |
| `aria-hidden-interactive` | `aria-hidden="true"` on a `<button>` / `<a>` / `<input>` / `<select>` / `<textarea>`, which removes the control from assistive technology but leaves it focusable. Not flagged when the element is out of the tab order: `tabindex="-1"`, `disabled`, `inert`, or an `<a>` without `href` (the correct way to hide the second copy of a duplicated link). | WAI-ARIA spec. |
| `heading-skip` | Heading levels jump downward (e.g. `<h2>` followed by `<h4>`). | WCAG SC 1.3.1. |
| `color-only-state` | Tailwind `text-` / `bg-` / `border-` / `ring-` token in red, green, emerald, rose or crimson on an element with no text and no inline icon. State must not rely on color alone. | WCAG SC 1.4.1. |
| `motion-no-reduce-guard` | `animate-{spin,ping,pulse,bounce}`, `transition-transform`, or `transition-all` without a `motion-reduce:` peer. | WCAG SC 2.3.3 / `prefers-reduced-motion`. |
| `body-text-tracking-tight` | Tailwind `tracking-tight`/`tracking-tighter` (negative letter-spacing) on running body text (`p`, `li`, `dd`, `blockquote`, `td`, `figcaption`); headings, buttons, and nav labels are excluded, and so is display type (`text-3xl` or larger, or an arbitrary size of 30px / 1.875rem and up). A static proxy for the intent of the SC, not a conformance test: it cannot verify a rendered page survives a user *widening* spacing without clipping. The make-side counterpart, `sprezzature-accessibility-text-spacing`, emits an opt-in CSS (Cascading Style Sheets, the rules that set a page's colours, fonts and spacing) block at the WCAG 1.4.12 minimums for the same tag set. | WCAG SC 1.4.12 (proxy). |
| `video-missing-captions` | `<video>` with no `<track kind="captions">` or `kind="subtitles"` (a `<track>` with no `kind` counts as subtitles). A decorative video, `muted` with no `controls`, is exempt. | WCAG SC 1.2.2. |
| `audio-missing-transcript` | `<audio>` with neither a caption track nor an accessible name pointing at a transcript. | WCAG SC 1.2.1. |
| `track-missing-srclang` | `<track>` with no `srclang`, so assistive technology cannot tell the captions' language. | Authoring practice (WCAG 1.2.4). |
| `media-missing-controls` | `<video>` / `<audio>` with no `controls`: nothing to operate from the keyboard. Decorative video exempt. | WCAG SC 2.1.1. |
| `media-autoplay-sound` | `autoplay` without `muted`: sound that starts by itself masks the screen reader. | WCAG SC 1.4.2. |

The media rules see that a caption track is **declared**, never that its text
is right or in sync; `sprezzature-audio` drafts the WebVTT the declaration
points at.

## When a finding is wrong

Three escape valves:

1. **`--ignore rule-id[,rule-id…]`** for a single run.
2. **Fix the markup.** Most findings have a one-line fix (add `alt=""`, wrap in `<label>`, add `motion-reduce:transition-none`).
3. **File-level suppression** is not supported. It would invite the linter to be silenced for a whole page. Per-element exemption belongs in the markup itself (the `role="button"` + `tabindex` escape for `div-onclick`, for example).

## CI integration

```yaml
# .github/workflows/a11y.yml
- name: A11y lint
  run: |
    sprezzature-accessibility-lint --format json public/ > a11y-report.json
    python3 -c "import json,sys; d=json.load(open('a11y-report.json')); sys.exit(1 if d['findings_total'] else 0)"
```

The linter's exit code is also CI-friendly on its own; the JSON dump above is just for an artifact.

## What this linter does *not* check

- Live WAI-ARIA state (`aria-expanded`, `aria-selected` consistency): depends on JavaScript behaviour.
- Color contrast: see the companion `sprezzature-colors` skill's `sprezzature-colors-contrast`.
- Focus order within a JavaScript-built widget: needs runtime.
- Whether a declared caption track is correct or synchronised: only its presence is checked.
- Form error association (`aria-describedby` between input and a sibling message): pattern is too varied for a static rule.

For those, pair with axe-core in dev tools and manual testing with a screen reader.

## Colour-blindness & grayscale: the image-layer check

Static markup can't tell whether colour is *load-bearing*: whether two series
collapse to one hue for a red-green–blind reader, or a diverging +/− sign
vanishes in grayscale. That needs the rendered pixels, so it lives one layer
out from the linter, in the companion `sprezzature-colors` package's
`sprezzature-colors-cvd`.

It reinforces the two existing sprezzature-figures steps rather than replacing them:

- **make** (the Ralph Eyeball Loop): after the render step, run
  `sprezzature-colors-cvd render.png` to get a contact
  sheet (grayscale + protanopia + deuteranopia + tritanopia) and *look*. The
  loop becomes **render → simulate → look**.
- **audit** (the figure auditor, static): the auditor flags rainbow ramps and
  filters in the markup; the simulator catches what only shows in pixels. Same
  goal (colour is never the sole channel), two layers.

The transform is done in **linear light** (sRGB → linear → Machado-2009 matrix
or luminance → sRGB), the physically correct pipeline; applying the matrices to
gamma-encoded sRGB is a common shortcut that shifts every colour. When a series
or a sign becomes unreadable in the sheet, add a second channel: a sign, a value
label, a marker shape, or a stroke style.

## Checklist (when adding a new rule)

- [ ] Stable identifier (kebab-case, suggestive of the violation).
- [ ] Citation of the WCAG SC or WAI-ARIA section in this doc.
- [ ] Implementation in the brick's `scripts/lint_a11y.py`, registered in `ALL_RULES`.
- [ ] Smoke test on at least one positive fixture and one negative.
- [ ] The brick's test suite green (`python3 -m pytest -q` in `sprezzature-accessibility`).
