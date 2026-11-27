# Examples

## Lint a single file

```bash
sprezzature-accessibility-lint public/index.html
```

Output (text):

```
public/index.html:
  L  14  [img-missing-alt] <img> missing alt attribute. Use alt="" for decorative images.
  L  27  [a-empty] <a> has no accessible name.

2 finding(s) across 1 file(s).
```

Exit code: `1` (findings present).

## Lint a directory recursively

```bash
sprezzature-accessibility-lint public/
```

## Output for machine consumption

JSON (JavaScript Object Notation) is plain text in named fields that a script can
read.

```bash
sprezzature-accessibility-lint --format json public/index.html | jq '.findings_total'
```

That prints `2`. The full document, without the jq filter:

```json
{
  "findings_total": 2,
  "files": [
    {
      "file": "public/index.html",
      "findings": [
        {"rule": "img-missing-alt", "line": 14, "message": "..."},
        {"rule": "a-empty", "line": 27, "message": "..."}
      ]
    }
  ]
}
```

## Ignore specific rules

```bash
sprezzature-accessibility-lint --ignore heading-skip,motion-no-reduce-guard public/
```

## Auto-fix in place

```bash
sprezzature-accessibility-lint --fix public/index.html
```

Output (the first line on stderr, the second on stdout):

```
public/index.html: applied 2 fix(es); 1 unfixable finding(s); 1 remaining.
1 remaining finding(s) after fix pass.
```

Exit code: `1` while findings remain, `0` once none do.

Rules with a fixer: `html-missing-lang`, `img-redundant-aria`,
`tabindex-positive`, `aria-hidden-interactive`, `motion-no-reduce-guard`,
`body-text-tracking-tight`.

The other twenty-one need a content decision and are reported, not fixed:
`img-missing-alt` (see `--fix-alt` below), `a-missing-href`, `a-empty`,
`button-empty`, `div-onclick`, `input-missing-label`, `dialog-missing-close`,
`heading-skip`, `color-only-state`, the five media rules
(`video-missing-captions`, `audio-missing-transcript`, `track-missing-srclang`,
`media-missing-controls`, `media-autoplay-sound`), and the seven reading rules
(`body-text-justified`, `body-text-centered-long`, `body-text-italic-long`,
`body-text-all-caps-long`, `body-text-leading-tight`, `body-text-line-too-long`,
`text-underline-not-link`): realigning or re-measuring a page is a design
decision, and the reading preset below is their make-side answer.

## Reading for dyslexic readers

```html
<!-- page.html -->
<html lang="en"><body>
  <div class="mx-auto max-w-4xl px-5">
    <p class="text-justify text-sm">Running text of twenty words or so, the kind
    a reader takes in line by line, set justified and small on a wide column.</p>
    <p>Read <span class="underline">this part</span> twice.</p>
  </div>
</body></html>
```

```bash
sprezzature-accessibility-lint page.html
```

Reports `body-text-justified` (rivers of space, WCAG 1.4.8 failure F88),
`body-text-leading-tight` (`text-sm` brings a 20px line on 14px type, 1.43),
`body-text-line-too-long` (`max-w-4xl` less padding is about 120 characters of
14px text) and `text-underline-not-link`. The fix is `text-left` (or nothing),
`leading-relaxed`, `max-w-prose`, and bold instead of the underline.

## Preview fix without writing

```bash
sprezzature-accessibility-lint --fix --dry-run public/index.html
```

Exits 0 always (preview, not a verdict).

## Draft the missing alt text

```bash
sprezzature-accessibility-lint --fix-alt public/index.html
```

Every `<img>` without `alt` gets a draft from the local vision model, made from
the image and the text around it in that page. One line per draft goes to stderr,
then a reminder that drafts are drafts. The mechanical fixes run in the same pass.
It needs Ollama and `qwen3-vl:8b` (`sprezzature-accessibility-install-alt`).

One image at a time, with its purpose declared:

```bash
sprezzature-accessibility-alt --kind functional --context "Search" icons/magnifier.png
```

Output: the alt text on stdout, nothing else. See `references/alt-text-ai.md`.

## Make-side: emit a comfortable-reading toggle

CSS (Cascading Style Sheets) is the language that sets a page's colours, fonts
and spacing; WCAG (Web Content Accessibility Guidelines) is the standard that
says what an accessible page is.

The audit-side reading rules flag what makes running text hard to read;
`sprezzature-accessibility-reading` emits the opposite, an opt-in CSS preset a
page can ship: the WCAG 1.4.12 Text Spacing minimums, then lines of 70
characters, start-aligned, upright, in their own case (WCAG 1.4.8 and the
British Dyslexia Association style guide). Its first name,
`sprezzature-accessibility-text-spacing`, is still installed and runs the same
command.

```bash
sprezzature-accessibility-reading
```

Output:

```css
/* Comfortable reading: WCAG 1.4.12 Text Spacing minimums, opt-in via
   [data-text-spacing="comfortable"]. Pairs with the body-text-tracking-tight audit
   rule in sprezzature-accessibility/scripts/lint_a11y.py. */
[data-text-spacing="comfortable"] blockquote,
[data-text-spacing="comfortable"] dd,
[data-text-spacing="comfortable"] figcaption,
[data-text-spacing="comfortable"] li,
[data-text-spacing="comfortable"] p,
[data-text-spacing="comfortable"] td {
  line-height: 1.5;
  letter-spacing: 0.12em;
  word-spacing: 0.16em;
}
[data-text-spacing="comfortable"] blockquote,
[data-text-spacing="comfortable"] dd,
[data-text-spacing="comfortable"] p {
  margin-bottom: 2.0em;
}
/* Reading: WCAG 1.4.8 Visual Presentation and the British Dyslexia
   Association style guide. Bounded lines, start-aligned (never
   justified or centred), upright, in their own case. Pairs with the
   body-text-* reading rules of sprezzature-accessibility's lint. */
[data-text-spacing="comfortable"] blockquote,
[data-text-spacing="comfortable"] dd,
[data-text-spacing="comfortable"] figcaption,
[data-text-spacing="comfortable"] li,
[data-text-spacing="comfortable"] p {
  max-width: 70ch;
  text-align: start;
  font-style: normal;
  text-transform: none;
}
```

`--spacing-only` prints the first block alone, as 1.5 did; `--measure 65` sets
another line length, `--measure 0` leaves the width alone. No font is set: the
studies of "dyslexia fonts" (OpenDyslexic, Dyslexie) found no reading gain.

A page ships the toggle by setting `data-text-spacing="comfortable"` on
`<html>` (via a button/checkbox the reader controls, persisted however the
page already persists a dark-mode choice) once this CSS block is included.

Custom attribute, values, and output file:

```bash
sprezzature-accessibility-reading \
  --attr data-reading-mode --value on \
  --letter-spacing 0.16 --word-spacing 0.32 \
  --out reading-mode.css
```

## Pre-commit hook

The lint takes one target, a file or a directory, so the hook lints the
directory and does not receive file names. `language: system` uses the command
already on `PATH`, for instance from the two-package install in the README
(`pip install --no-deps sprezzature-accessibility` then `pip install click`).

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: a11y-lint
        name: Accessibility lint
        entry: sprezzature-accessibility-lint
        language: system
        files: \.html$
        pass_filenames: false
        args: ["public/"]
```

## Install the agent skill

The skill an agent reads ships inside the package, at
`sprezzature_accessibility/skill/`. Ask whether the copy an agent reads is in step,
then refresh it:

```bash
sprezzature-accessibility-skill
sprezzature-accessibility-skill --install
```

Output on a machine that never had it: the report, then the install, which says
the same thing before it copies.

```
sprezzature-accessibility: (not installed) (/Users/you/.claude/skills/sprezzature-accessibility)
Pass --install to copy the shipped skill there.
sprezzature-accessibility: (not installed) (/Users/you/.claude/skills/sprezzature-accessibility)
sprezzature-accessibility: installed
```

Run again, it answers `sprezzature-accessibility: in step with …` and exits 0.
When a previous copy is replaced, the last line names where it was moved.

`--agent opencode` targets `~/.opencode/skills` instead, and `--path` prints the
folder pip installed. `sprezzature-accessibility skill` is the same command.
