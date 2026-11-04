# sprezzature-accessibility

[![License](https://img.shields.io/badge/license-BSD--3--Clause-blue.svg)](https://github.com/warith-harchaoui/sprezzature-accessibility/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%20to%203.13-blue.svg)](https://www.python.org/)

[🇫🇷 LISEZMOI.md](https://github.com/warith-harchaoui/sprezzature-accessibility/blob/main/LISEZMOI.md) · 🇬🇧 README.md

[![logo](https://raw.githubusercontent.com/warith-harchaoui/sprezzature-accessibility/main/assets/logo.png)](https://sprezzature.ai/)

A web page is accessible when someone using a screen reader, a keyboard alone (no
mouse), or a browser's reduced-motion setting can still use it. This package checks
HTML source code for the mistakes that most often break that, and drafts the piece
of content those mistakes most often leave out: an `<img>` with no `alt` text is as
invisible to a screen reader as if the image were missing from the page.

The audit half is a static linter: twenty rules from WCAG (Web Content Accessibility
Guidelines, the W3C standard that defines what "accessible" means for the web) and
WAI-ARIA (Web Accessibility Initiative, Accessible Rich Internet Applications: the
attribute vocabulary, `role`, `aria-label` and the like, that lets custom widgets
describe themselves to assistive software), each one decidable by reading the HTML
text alone. No browser opens, no page renders, no JavaScript runs, so there is no
DOM (Document Object Model, the tree of elements a browser builds while rendering a
page) to inspect. The lint imports only the Python standard library, which is what
makes it fast enough for a pre-commit hook or a CI (continuous integration) step: a
deterministic gate before any change lands in production.

The rules cover missing alt text, unlabelled inputs, empty buttons, clickable
`<div>`s a keyboard cannot reach, dialogs with no keyboard way to close them, a
missing `lang` attribute (which breaks screen-reader pronunciation), heading levels
that jump instead of nesting in order, status shown by colour alone (a red/green
pair a colour-blind reader cannot tell apart), animations with no reduced-motion
guard, negative letter-spacing on running text (which slows reading for dyslexic
readers), and five checks on time-based media: captions, transcripts, unmuted
autoplay, keyboard controls and caption-track language. Six of the twenty rules
also ship a mechanical auto-fix (`--fix`), so the gate can repair what it safely
can instead of only reporting it.

The make half drafts the missing alt text with a local vision model (`qwen3-vl:8b`
through Ollama), following the W3C image-purpose decision tree. `--fix-alt` does it
in place, from the image and the text around it on the same page. Nothing leaves
the machine, and every draft is a draft: a person reads it before it is committed.

This package only ever reads source code, so it cannot catch what only shows up
once a page renders in a browser: keyboard focus order, screen-reader announcement
timing, colour contrast against a real background. Pair it with axe-core, Pa11y or
Lighthouse, which drive a real browser, for that layer. The two are complementary:
this one is the fast, no-browser first gate; those are the slower, browser-accurate
second pass.

## How it works

![Flow diagram. At the top, the HTML you are holding feeds two lanes. The left lane makes: it reads the page around an image, asks a local vision model, and writes the alt attribute back into the page. The right lane audits: it scans the source text with no browser, decides twenty rules, and returns findings as text or JSON with exit code 1 on any finding. Both lanes meet in one outcome, a page a screen reader can read and a keyboard can reach.](https://raw.githubusercontent.com/warith-harchaoui/sprezzature-accessibility/main/assets/how-it-works.svg)

## Features

- 20 rules covering img, a, button, div/span, input, dialog, html, tabindex, aria,
  heading order, colour-only state, motion-reduce guards, body-text letter-spacing,
  and time-based media: video captions, audio transcripts, unmuted autoplay,
  keyboard controls, and caption-track language.
- Auto-fix for 6 rules (`--fix`): `lang` detection and insertion, redundant aria
  removal, tabindex demotion, aria-hidden strip, motion-reduce guard append,
  tight-tracking strip. Idempotent: a second run applies nothing.
- Alt-text drafting (`--fix-alt` for a whole page, `sprezzature-accessibility-alt`
  for one image): six image purposes (informative, decorative, functional, text,
  complex, group), the page's own text as context, output capped at 150
  characters, results cached on disk.
- `sprezzature-accessibility-text-spacing`: the make-side counterpart to the
  letter-spacing rule. It emits an opt-in "comfortable reading" CSS block at the
  WCAG 1.4.12 Text Spacing minimums, for pages that want to ship the fix as a
  reader-facing toggle.
- Text and JSON output, composable with jq or any CI parser.
- Exit code 1 on any finding, 0 on a clean run: usable as a pre-commit gate.
- Python 3.10 to 3.13. The lint path imports the standard library only, plus
  `langdetect` when it is installed (the `html-missing-lang` fixer uses it to
  guess the page language).

## Install

One line, and it is everything: the lint, the alt-text drafter, the language
detector, the HTTP API and the MCP server.

```bash
pip install sprezzature-accessibility
```

`pip install 'sprezzature-accessibility[dev]'` adds the test toolchain (pytest,
ruff) and nothing else.

The drafter also needs Ollama and the model on the machine. One command installs
Ollama if it is missing (Homebrew, the official Linux installer, or winget on
Windows), starts its daemon and pulls `qwen3-vl:8b`:

```bash
sprezzature-accessibility-install-alt
```

Pillow is not a dependency. When it is installed, images are downscaled before
they are sent to the model (`--resize`); without it, the original bytes are sent.

### For a pre-commit hook: two packages

The lint needs the standard library plus click, and that is why it fits in a
pre-commit hook: it runs in milliseconds, with no browser and no model behind it.
Most of a full install is the HTTP and MCP surfaces, which a hook has no use for.
So a hook installs the lint and nothing else:

```bash
pip install --no-deps sprezzature-accessibility
pip install click
```

That is two packages on top of a fresh venv: click, and this one. It is stated as
a delta rather than a total on purpose: what `venv` seeds is the interpreter's
business, and it differs (3.11 adds setuptools, 3.13 does not). The delta is what
this package can promise. On such an install `--fix` cannot guess a page language
(no `langdetect`), so it leaves `html-missing-lang` for a person to fix.

This is tested on every push.
`tests/test_the_hook_install_is_the_lint_and_nothing_else.py` builds exactly that
venv, checks by name what landed in it, and runs the shipped
`sprezzature-accessibility-lint` against a page with a known defect. And
`tests/test_the_lint_stays_out_of_the_extra.py` checks that nothing on the lint
path imports the drafting dependencies.

## Quick start

```bash
# Lint a single page
sprezzature-accessibility-lint public/index.html

# Lint a directory recursively, exit 1 on any finding
sprezzature-accessibility-lint public/

# JSON output for CI pipeline consumption
sprezzature-accessibility-lint --format json public/index.html

# Suppress two rules
sprezzature-accessibility-lint --ignore heading-skip,motion-no-reduce-guard public/

# Auto-fix what can be fixed mechanically
sprezzature-accessibility-lint --fix public/

# Preview what --fix would change, without writing (always exits 0)
sprezzature-accessibility-lint --fix --dry-run public/

# Draft the missing alt text in place, then run the mechanical fixes
sprezzature-accessibility-lint --fix-alt public/

# Same, with the alt text written in French
sprezzature-accessibility-lint --fix-alt --alt-lang fr public/
```

`--fix-alt` drafts every `<img>` that has no `alt`, as an informative image, using
the text around that image in the same document and the proper nouns found in it.
Without `--alt-lang`, the language is the page's `<html lang>`, else the one
detected in the page text, else the environment locale (`ALT_LANG`, then `LC_ALL`,
then `LANG`). Remote images, images missing from disk and tags that span several
lines are left alone and reported. It runs before the mechanical fixes, so one invocation
leaves the page in its final state.

### One image at a time

```bash
sprezzature-accessibility-alt --kind informative photo.jpg
sprezzature-accessibility-alt --kind functional --context "Submit form" icon.png
sprezzature-accessibility-alt --kind complex --longdesc --in docs/chart.md chart.png
```

The alt text goes to stdout. `--kind decorative` prints nothing and calls no model:
a decorative image takes `alt=""`. `--longdesc` also writes a long description to
`<image>.longdesc.md`. `--in DOC`, `--vocab FILE`, `--vocab-from PATH` and
`--auto-project` give the model the spellings of the project's own names; without
`--lang`, the language is detected from that text. `--no-cache` bypasses the cache for one run. `make-alt` is another name for the
same command.

## The five surfaces

The same engine answers on five surfaces.

| Surface | Entry point |
|---|---|
| Library | `import sprezzature_accessibility` |
| Command line | `sprezzature-accessibility` (alias `make-a11y`) and one command per tool |
| HTTP API (FastAPI) | `uvicorn sprezzature_accessibility.api:app`, or `docker compose up` |
| MCP server | `sprezzature-accessibility-mcp` |
| Agent skill | `SKILL.md`, maintained in the [sprezzature](https://github.com/warith-harchaoui/sprezzature) hub |

### Library

```python
from pathlib import Path

from sprezzature_accessibility import describe, fix_file, lint_file

for f in lint_file(Path("public/index.html")):
    print(f.line, f.rule, f.message)

applied, skipped, remaining = fix_file(Path("public/index.html"), set(), dry_run=True)

alt = describe("hero.jpg", kind="informative", lang="fr", context="Careers page hero")
```

`KINDS` lists the six image purposes. `describe_long` writes the long description
of a complex image. The drafting names (`describe`, `describe_long`, `detect_lang`,
`surrounding_text` and the rest of `__all__`) are loaded on first use, so
`import sprezzature_accessibility` stays as light as the lint.

### Command line

One front door, built on click, with two spellings and four tools:

```bash
sprezzature-accessibility --help          # the four tools, with what each does
sprezzature-accessibility tools           # which tools can run on this machine
sprezzature-accessibility lint public/    # same as sprezzature-accessibility-lint public/
make-a11y lint public/                    # the historical spelling of the same command
```

| What it does | Sub-command | Own command |
|---|---|---|
| Lint HTML; `--fix`, `--fix-alt`, `--dry-run`, `--format`, `--ignore`, `--alt-lang` | `lint` | `sprezzature-accessibility-lint` |
| Emit the WCAG 1.4.12 comfortable-reading CSS | `text-spacing` | `sprezzature-accessibility-text-spacing` |
| Draft alt text for one image | `alt` | `sprezzature-accessibility-alt` (alias `make-alt`) |
| Install Ollama, start it, pull `qwen3-vl:8b` | `install-alt` | `sprezzature-accessibility-install-alt` |

Both front-door spellings resolve to one callable over one table
(`sprezzature_accessibility/_tools.py`), so a tool cannot be listed in one and
missing from the other. The per-tool commands are what a script or a hook should
call. Shell completion for bash and zsh is printed at the end of
`sprezzature-accessibility --help`.

### HTTP API

```bash
uvicorn sprezzature_accessibility.api:app --host 127.0.0.1 --port 8000
curl -s -X POST localhost:8000/v1/lint \
  -H 'content-type: application/json' \
  -d '{"html": "<img src=\"a.png\">"}'
```

| Route | operation_id | What it returns |
|---|---|---|
| `GET /health` | `health` | `{"status": "ok"}` |
| `GET /v1/rules` | `list_rules` | Every rule, with its severity |
| `POST /v1/lint` | `lint_html` | Findings for a string of HTML, with error and warning counts |
| `GET /v1/kinds` | `list_kinds` | The six image purposes, each with what it is for |
| `POST /v1/alt` | `draft_alt_text` | A drafted alt text, and a long description on request |

The API lints a string, never a URL: fetching on a caller's behalf would turn it
into an open proxy. `POST /v1/alt` answers 502 when the local model cannot be
reached and 404 when the image file does not exist. Interactive documentation is at
`/docs`.

With Docker, `docker compose up -d` builds the image and serves the API on port
8000, with `./work` mounted at `/work`. `docker compose --profile alt up -d` also
starts an Ollama container for the drafter. The image serves the HTTP routes only;
the MCP endpoint is mounted by `sprezzature-accessibility-mcp`.

### MCP server

MCP (Model Context Protocol) lets an agent host call these routes as tools.

```bash
sprezzature-accessibility-mcp                      # 127.0.0.1:8000
sprezzature-accessibility-mcp --host 0.0.0.0 --port 9000
```

It serves the same FastAPI app with the MCP endpoint mounted at `/mcp`. The five
tools are the five routes above, named by their `operation_id`: `health`,
`list_rules`, `lint_html`, `list_kinds`, `draft_alt_text`. The defaults come from
`SPREZZATURE_ACCESSIBILITY_HOST` and `SPREZZATURE_ACCESSIBILITY_PORT` when they are
set.

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
| `aria-hidden-interactive` | error | aria-hidden on a still-focusable interactive element |
| `heading-skip` | error | headings skip levels downward |
| `color-only-state` | warning | red/green token with no icon or text |
| `motion-no-reduce-guard` | warning | animation without motion-reduce peer |
| `body-text-tracking-tight` | warning | tight letter-spacing on running text |
| `video-missing-captions` | error | `<video>` with audio and no `<track kind="captions">` (WCAG 1.2.2) |
| `audio-missing-transcript` | error | `<audio>` with no text alternative (WCAG 1.2.1) |
| `track-missing-srclang` | warning | `<track>` without `srclang`: caption language unknown |
| `media-missing-controls` | error | `<video>`/`<audio>` with nothing to operate from the keyboard (WCAG 2.1.1) |
| `media-autoplay-sound` | error | unmuted `autoplay` masks a screen reader (WCAG 1.4.2) |

The severity is the one the HTTP API reports. The command line exits 1 on any
finding, warnings included. Six of these rules also carry a mechanical fixer,
applied by `--fix`.

## License

BSD-3-Clause. Copyright 2026 Warith HARCHAOUI.
