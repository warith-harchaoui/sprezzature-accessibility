# The twenty-seven rules — standards mapping and known limits

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

## Rules for reading: dyslexia and other reading difficulties (WCAG 1.4.8, BDA)

About one reader in ten has dyslexia to some degree. What helps them is well
documented, and the same settings help readers with low vision, attention
difficulties, or reading in a second language. These seven rules, with
`body-text-tracking-tight` above, check the part of that advice a static linter
can decide. All are **warnings**: WCAG 1.4.8 is level AAA, and a style guide is
advice, so the API never reports them as errors (the command line still exits 1
on any finding, as for every warning).

**Sources.**

- **WCAG 2.2 success criterion 1.4.8 Visual Presentation (AAA)**: for blocks of
  text, "width is no more than 80 characters or glyphs", "text is not justified
  (aligned to both the left and the right margins)", "line spacing (leading) is
  at least space-and-a-half within paragraphs". Failure technique **F88** is
  "using text that is justified".
- **British Dyslexia Association, *Dyslexia Style Guide*** (2023 edition; the
  layout and emphasis rules it states are the same as in earlier editions):
  "Use left-justified with ragged right edge"; "Avoid underlining and italics:
  these tend to make the text appear to run together. Use bold instead";
  "Avoid text in block capitals: this is much harder to read"; "Line spacing of
  1.5 is preferable"; "Lines should not be too long: 60 to 70 characters".
- **Rello & Baeza-Yates (2013)**, "Good fonts for dyslexia", *ASSETS '13*: with
  eye-tracking on 48 readers with dyslexia, italic type significantly impaired
  reading performance.
- **Zorzi et al. (2012)**, *PNAS* 109(28): wider letter-spacing raised reading
  speed and accuracy for dyslexic children (already behind
  `body-text-tracking-tight`).

**What is deliberately not a rule.** A "dyslexia font". Wery & Diliberto (2017,
*Annals of Dyslexia* 67) found no gain in reading rate or accuracy with
OpenDyslexic, and Kuster et al. (2018, *Annals of Dyslexia* 68) none with
Dyslexie; neither the linter nor the reading preset asks for one. Nor is a
minimum font size a rule: the BDA's "12 to 14 point" is a print value, and a
screen's rendered size depends on zoom and distance, which source cannot see.

**How the rules read a page.** Through the cascade, as far as source shows it:
Tailwind utilities on the element and its ancestors, with their breakpoint
prefixes (`md:text-justify` counts from 768 px up; a state variant such as
`hover:` is ignored, the text is judged at rest), `style` attributes, the
legacy `align` attribute, the browser's default italic for `<em>`, `<i>`,
`<cite>` and the like, the default underline of `<u>`, and simple selectors
(tags, classes, ids, descendant and child combinators) in the page's own
`<style>` blocks. A rule behind a pseudo-class or an attribute selector is
conditional and is skipped, which is also why the reading preset's own
`[data-text-spacing]` block is never mistaken for the page's default. Hidden
text (`hidden`, `sr-only`) and `code`, `pre`, `svg` are not read as prose.

**What counts as running text.** One of `p`, `li`, `dd`, `blockquote`, `td`,
`figcaption`, counting its own words and not those of blocks nested in it, of
at least **15 words** (more than a line on a phone; one glance at a short label
is not continuous reading, and the evidence is about continuous reading). Type
of 30 px and up is display type and is exempt, the line `body-text-tracking-tight`
draws.

| Rule | Source | What it catches | Threshold |
|---|---|---|---|
| `body-text-justified` | WCAG 1.4.8, F88; BDA | Running text whose computed `text-align` is `justify` at any breakpoint: Tailwind `text-justify` on it or an ancestor, `style="text-align: justify"`, `align="justify"`, a `<style>` rule. With no hyphenation to absorb the slack, the stretched spaces line up into rivers that a dyslexic reader follows down instead of across. | 15 words |
| `body-text-centered-long` | BDA (left aligned) | A centred running-text unit of 30 words or more. Every line starts somewhere else, so the eye has to search for each one. | 30 words: about three lines at 70 characters. A centred lead of one or two lines under a hero heading is a settled convention and is not reported. |
| `body-text-italic-long` | BDA; Rello & Baeza-Yates 2013 | The outermost element where italic starts (class `italic`, `font-style: italic`, `<em>`, `<i>`…), counting only the words the italic reaches (a `not-italic` descendant is not counted). Emphasis of a few words is what italic is for. | 15 words |
| `body-text-all-caps-long` | BDA | Two shapes: an `uppercase` (or `text-transform: uppercase`) reaching 15 words, and running text typed in capitals (at least 15 capitalised words, 80 % of its words). A short eyebrow label and a few acronyms in prose pass. | 15 words |
| `body-text-leading-tight` | WCAG 1.4.8; BDA | Running text whose computed line height is under 1.5 at any breakpoint: `leading-none` (1), `leading-tight` (1.25), `leading-snug` (1.375), a fixed `leading-N` over the font size, `leading-[1.3]`, `line-height` in a `style` or `<style>`, and the line height a Tailwind `text-*` size brings with it. Tailwind's defaults put `text-xs` at 1.33, `text-sm` at 1.43 and `text-xl` at 1.4, so a `<p class="text-sm">` is reported until it carries a `leading-normal` (or `text-sm/6`). | 1.5, 15 words |
| `body-text-line-too-long` | WCAG 1.4.8; BDA asks 60 to 70 | Running text longer than one line whose longest possible line exceeds 80 characters at some breakpoint. The width is worked out from source: the nearest `max-w-*`, `w-*`, `container`, or `max-width` in a `style`/`<style>`, capped by the widest screen the breakpoint allows, minus `p-*`/`px-*` padding, divided by any `grid-cols-N` / `columns-N` crossed on the way (with `col-span-N`), then turned into characters at 0.5 em per character of the element's font size (one `ch` is one character). `max-w-prose` (65ch) passes; `max-w-4xl` of `text-lg` (about 95 characters) does not. | 80 characters |
| `text-underline-not-link` | BDA; web convention | An underline at rest (`underline`, `text-decoration: underline`, `<u>`) on text that is not a link and not inside one, not a `<button>`, `<summary>` or element with a link or button role, and holding no link. An underline promises a link, and the rule cuts through the descenders. `<abbr>` is exempt. | any visible text |

**Known limits.** A linked stylesheet is not read: alignment, italics or line
height set there are invisible, and "no width limit at all" is only reported on
a page whose styles are all in its own markup (with a linked stylesheet the
text may be bounded there, so the rule stays silent rather than guess). The
Tailwind theme is the default one: a project that redefines its font sizes or
`maxWidth` scale in `tailwind.config.js` is judged on the defaults. A flex row
shares its width by content, so text inside one is not judged for line length,
and gaps between grid columns are not subtracted. The average character width
is an estimate, taken at the wide end (0.5 em) so the line-length rule errs
quiet. None of the seven has a `--fix`: realigning, re-leading or re-measuring
a page is a design decision, and the reading preset below is the make-side
answer.

**The make side.** `sprezzature-accessibility-reading` (also installed as
`sprezzature-accessibility-text-spacing`, its first name) emits an opt-in CSS
preset toggled by `[data-text-spacing="comfortable"]` on an ancestor: the
WCAG 1.4.12 spacing block (line height 1.5, letter spacing 0.12em, word
spacing 0.16em, 2em after paragraphs), then `max-width: 70ch`,
`text-align: start`, `font-style: normal` and `text-transform: none` on running
text (`td` is left out of the measure: a cell's width belongs to its table).
`--spacing-only` prints the first block alone, as 1.5 did.

## What these twenty-seven rules do not cover

The linter is static by design (see `README.md` / `LISEZMOI.md` for why), so it cannot see:

- Keyboard focus order as the browser actually computes it (only the source-level `tabindex` anti-patterns above).
- Screen-reader announcement timing (live regions, focus management on route change).
- Real color contrast ratios against a rendered background: that is the `sprezzature-colors` package's job, not this linter's.
- Anything that only exists after JavaScript runs (content injected client-side, dynamically toggled `aria-*` states).

Pair this linter with `axe-core`, `Pa11y`, or `Lighthouse` for that layer; see `LANDSCAPE.md` / `PAYSAGE.md` for how the tools divide the work.
