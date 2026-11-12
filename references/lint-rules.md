# The twenty rules — standards mapping and known limits

Each rule below maps to a specific Web Content Accessibility Guidelines
(WCAG, the W3C standard that defines what "accessible" means for the
web) success criterion or a WAI-ARIA (Web Accessibility Initiative,
Accessible Rich Internet Applications) authoring requirement, and is
decidable from the HTML source text alone, no browser, no rendered
DOM (the tree of elements a browser assembles while displaying a
page). This is the "why this rule, and where does it fall short"
document; for run commands and output shapes, see `EXAMPLES.md`. Six of the rules have a mechanical fixer (`--fix`): `html-missing-lang`, `img-redundant-aria`, `tabindex-positive`, `aria-hidden-interactive`, `motion-no-reduce-guard`, `body-text-tracking-tight`. `img-missing-alt` is repaired by `--fix-alt`, which drafts the text with a local model (see `references/alt-text-ai.md`).

## Rules with a WCAG success criterion

| Rule | WCAG SC | What it catches |
|---|---|---|
| `img-missing-alt` | 1.1.1 Non-text Content | `<img>` with no `alt` attribute at all. An empty `alt=""` is the correct way to mark a decorative image; *omitting* the attribute is the violation. |
| `html-missing-lang` | 3.1.1 Language of Page | `<html>` with no `lang`. A screen reader without a language hint may mispronounce every word on the page, not just foreign phrases. |
| `heading-skip` | 2.4.6 Headings and Labels (best practice reading) | Heading levels that jump downward (`<h2>` straight to `<h4>`). Screen-reader users navigate by heading level as a table of contents; a skipped level reads as a missing section. |
| `color-only-state` | 1.4.1 Use of Color | A Tailwind `text-red-*` / `bg-green-*` token with no accompanying icon or text. Roughly 1 in 12 men have some form of color vision deficiency; a status shown by hue alone disappears for them. |
| `motion-no-reduce-guard` | 2.3.3 Animation from Interactions (AAA, applied here as a house baseline) | An `animate-spin`, `animate-ping`, `animate-pulse`, `animate-bounce`, `transition-transform` or `transition-all` class with no `motion-reduce:` peer, so `prefers-reduced-motion` is silently ignored. Any other `animate-*` utility (a custom keyframe) is not recognised. |
| `body-text-tracking-tight` | 1.4.12 Text Spacing (AA), applied here as a static proxy, not a conformance test | Tailwind `tracking-tight`/`tracking-tighter` (negative `letter-spacing`) on a body-text element (`p`, `li`, `dd`, `blockquote`, `td`, `figcaption`). Grounded in [Zorzi et al. 2012](https://www.planetesante.ch/Magazine/Bebes-enfants-et-adolescents/Dyslexie/Dyslexie-espacer-les-lettres-permet-d-ameliorer-la-lecture): doubling letter-spacing on running text raised reading speed 20% for dyslexic children (8-14yo, no prior training), the opposite direction of what `tracking-tight` does. Body text set at display size (`text-3xl` or larger, or an arbitrary size of 30px / 1.875rem and up) is a figure in a tile rather than running text, and is not flagged. Headings, buttons, and nav labels are deliberately excluded — one glance at a short label has no comparable evidence of harm, and tight tracking there is an established display-type convention. **Known limit**: this cannot verify actual WCAG 1.4.12 conformance (does the layout survive a *user* widening spacing without clipping/overlap?) — that needs a rendered DOM, out of scope for a static linter by design (see house baseline note above); it only catches the Tailwind utility, not a literal `letter-spacing` CSS (Cascading Style Sheets, the rules that set a page's colours, fonts and spacing) declaration in a `<style>` block or external stylesheet. The make-side counterpart, `sprezzature-accessibility-text-spacing` (`scripts/text_spacing_preset.py`), emits an opt-in CSS block at the WCAG 1.4.12 minimums for the same tag set, for pages that want to ship the fix as a reader-facing toggle rather than just removing the anti-pattern. |

## Rules grounded in WAI-ARIA authoring practice

| Rule | Requirement | What it catches |
|---|---|---|
| `a-missing-href` | An `<a>` without `href` has no link semantics or keyboard handling | `<a>` used as a click target instead of a real `<button>`. |
| `a-empty` | Every link needs an accessible name | `<a>` whose only content resolves to empty text (checked via `accessible_name()`, which aggregates `aria-label`, `title`, all descendant text and `aria-labelledby` — not just direct text, so `<a><span>Label</span></a>` is read correctly; a character reference such as `&times;` is text). |
| `button-empty` | Every button needs an accessible name | Same check as `a-empty`, applied to `<button>`, with an icon-only exception when an `<svg>` or `<img>` descendant exists. |
| `div-onclick` | A non-interactive element with a click handler needs `role="button"` and `tabindex` to be keyboard-reachable | `<div>` / `<span>` with `onclick` but neither attribute. |
| `input-missing-label` | Every form control needs a programmatically associated label | `<input>` not wrapped in a `<label>`, not referenced by `<label for=...>`, and with neither `aria-label` nor `aria-labelledby`. Hidden, submit, button, reset, and image inputs are exempt. |
| `dialog-missing-close` | A modal needs a way to dismiss it without a mouse | `<dialog>` with no `<button>` whose `value` is `cancel`/`close`, no `<button autofocus>`, and no button whose accessible name matches a small hardcoded set: "close", "cancel" (English), "fermer", "annuler" (French), "schließen" (German). **Known limit:** any other language's close/cancel wording is not recognized and will false-positive; add to the set in `check_dialog_close` (`lint_a11y.py`) as new cases come up. |
| `tabindex-positive` | A positive `tabindex` overrides natural DOM order, which usually surprises keyboard and screen-reader users | Any `tabindex` ≥ 1. `tabindex="0"` and `tabindex="-1"` are fine and not flagged. |
| `aria-hidden-interactive` | `aria-hidden="true"` removes an element from the accessibility tree entirely | A `button` / `a` / `input` / `select` / `textarea` with `aria-hidden="true"` that a keyboard can still reach, so the Tab key lands on a control that announces nothing. Not flagged when the element is out of the tab order: `tabindex="-1"`, `disabled`, `inert`, or an `<a>` without `href`. That pairing is the correct way to hide the second copy of a duplicated link. |
| `img-redundant-aria` | Not a violation, a redundancy | `alt=""` (already the correct decorative marker) combined with `role="presentation"` or `aria-hidden="true"`. Harmless but redundant; flagged as a style warning, not an error. |

## Rules for time-based media (WCAG 1.2, 1.4.2, 2.1.1)

WCAG 1.2 is the one success-criterion family no other rule here touches, and it is the one that locks a Deaf or hard-of-hearing visitor out of a
page entirely rather than merely making it awkward. A `<video>` with no caption
track is not a degraded experience; it is no experience.

What a static linter can and cannot see here: it can tell that a caption track
is **declared**, never that its text is correct or synchronised. It reports the
absence, which is the failure it can prove. Pair it with `sprezzature-audio`,
which drafts the WebVTT the declaration points at.

| Rule | Criterion | What it flags |
|---|---|---|
| `video-missing-captions` | 1.2.2 Captions (Prerecorded), level A | `<video>` with no `<track kind="captions">` or `kind="subtitles"` (a `<track>` with no `kind` counts as subtitles). Skipped for a decorative video, meaning one that is `muted` and has no `controls`. |
| `audio-missing-transcript` | 1.2.1 Audio-only and Video-only (Prerecorded), level A | `<audio>` with neither a caption track nor an accessible name pointing at a transcript. |
| `media-autoplay-sound` | 1.4.2 Audio Control, level A | `<video autoplay>` / `<audio autoplay>` without `muted`. Sound that starts by itself masks a screen reader's own speech — the user cannot hear the tool they navigate with. `muted` satisfies the criterion outright, so muted autoplay is not flagged. |
| `media-missing-controls` | 2.1.1 Keyboard, level A | A media element with no `controls` attribute: nothing to operate from the keyboard. `controls` is not itself a criterion, but its absence with no scripted alternative is a keyboard failure. Skipped for a decorative video (`muted`, no `controls`). |
| `track-missing-srclang` | 1.2.4 / authoring practice | `<track>` with no `srclang`, so assistive technology cannot tell which language the captions are in. |

## What these twenty rules do not cover

The linter is static by design (see `README.md` / `LISEZMOI.md` for why), so it cannot see:

- Keyboard focus order as the browser actually computes it (only the source-level `tabindex` anti-patterns above).
- Screen-reader announcement timing (live regions, focus management on route change).
- Real color contrast ratios against a rendered background: that is the `sprezzature-colors` package's job, not this linter's.
- Anything that only exists after JavaScript runs (content injected client-side, dynamically toggled `aria-*` states).

Pair this linter with `axe-core`, `Pa11y`, or `Lighthouse` for that layer; see `LANDSCAPE.md` / `PAYSAGE.md` for how the tools divide the work.
