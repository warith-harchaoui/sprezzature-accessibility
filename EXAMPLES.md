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

## JSON output for machine consumption

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

The other fourteen need a content decision and are reported, not fixed:
`img-missing-alt` (see `--fix-alt` below), `a-missing-href`, `a-empty`,
`button-empty`, `div-onclick`, `input-missing-label`, `dialog-missing-close`,
`heading-skip`, `color-only-state`, and the five media rules
(`video-missing-captions`, `audio-missing-transcript`, `track-missing-srclang`,
`media-missing-controls`, `media-autoplay-sound`).

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

## Make-side: emit a comfortable-reading CSS toggle

The audit-side `body-text-tracking-tight` rule flags narrow letter-spacing on
running text; `text_spacing_preset.py` emits the opposite — an opt-in CSS
block a page can ship, at the WCAG 1.4.12 Text Spacing minimums:

```bash
sprezzature-accessibility-text-spacing
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
```

A page ships the toggle by setting `data-text-spacing="comfortable"` on
`<html>` (via a button/checkbox the reader controls, persisted however the
page already persists a dark-mode choice) once this CSS block is included.

Custom attribute, values, and output file:

```bash
sprezzature-accessibility-text-spacing \
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
