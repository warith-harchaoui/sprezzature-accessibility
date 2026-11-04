# Triggers

When to use sprezzature-accessibility, and what to call.

This file is written for an agent: a Claude Code or OpenCode skill, an MCP (Model
Context Protocol) host, anything choosing a tool on someone's behalf. Humans are
welcome, but the routing rules are the point.

---

## The generalisation, stated once

> **Holding HTML is the trigger. Nobody has to ask.**
> The markup you just generated is exactly the markup nobody has checked. Run
> `lint_html` over any page, component, form or dialog you author, before you hand
> it over, the same way you would not ship code without running it once. And an
> `<img>` with no `alt` is not a finding to report and leave: draft the alt.

Route on the domain's vocabulary, not on how the request is phrased. This package
answers when the request or the file in hand is about one of these objects:

- **HTML elements and attributes the rules read**: `<img>` and `alt`, `<a>` and
  `href`, `<button>`, `<input>` and `<label>`, `<dialog>`, `<html lang>`,
  `tabindex`, `role`, `aria-*`, `onclick` on `<div>`/`<span>`, `<h1>` to `<h6>`
  order, `<video>`, `<audio>`, `<track>` (`kind`, `srclang`), `controls`,
  `autoplay`, `muted`.
- **Standards it maps to**: WCAG (Web Content Accessibility Guidelines) success
  criteria 1.1.1, 1.2.1, 1.2.2, 1.2.4, 1.4.1, 1.4.2, 1.4.12, 2.1.1, 2.3.3, 2.4.6, 3.1.1;
  WAI-ARIA (the attribute vocabulary for accessible widgets); the W3C alt-text
  decision tree.
- **Image purposes**, the closed set the drafter takes: `informative`,
  `decorative`, `functional`, `text`, `complex`, `group`. Plus the long
  description a complex image needs.
- **Reading comfort**: Tailwind `tracking-tight` / `tracking-tighter` on running
  text, `motion-reduce:` guards, `animate-*`, and the WCAG 1.4.12 text-spacing
  values (line height 1.5, letter spacing 0.12em, word spacing 0.16em, paragraph
  spacing 2em).
- **Any of the twenty rule ids**, listed in `README.md` and
  `references/lint-rules.md`.

The request then takes one of four shapes: check the markup, say what is checked,
repair the markup, or write the missing words. The table below maps each shape to a
tool.

### Not this package

- **Colour contrast or colour-vision deficiency**: `sprezzature-colors`. A page can
  pass here and still be unreadable.
- **Captions written from recorded speech**: `sprezzature-audio`. This package
  checks that a caption track is declared; that one writes the WebVTT.
- **How an interface feels** (laws of UX): `sprezzature-ux-laws`.
- **Building the page** in the first place: `sprezzature-ui`.

---

## Every tool, and the request it answers

| Tool | The request it answers |
|---|---|
| `lint_html` (lint) | "Is this markup accessible?" Findings with rule id, line, severity, from the source alone. |
| `lint --fix` | "Fix what can be fixed safely." Six mechanical repairs, idempotent, offline. |
| `lint --fix-alt` | "Write the missing alt texts in this page." Drafts each one from the image and the text around it. |
| `list_rules` | "What do you check?" Every rule id and its severity. Ask before using `ignore`: an unknown id is silently ignored. |
| `list_kinds` | "Which image purpose is this?" The six purposes, each with what it is for. |
| `draft_alt_text` (alt) | "Describe this image as alt text." One image, one declared purpose, optional long description. |
| text-spacing | "Give readers a comfortable-reading toggle." Emits the WCAG 1.4.12 CSS into the project. |
| install-alt | "The drafter cannot reach a model." Installs Ollama, starts it, pulls `qwen3-vl:8b`. |
| `health` | "Is the server up?" Use only to diagnose a connection. |

The common shape is the repair, and the order matters: lint first, fix what it
names, lint again. Findings carry a line number and a rule id, so a fix is a
targeted edit rather than a rewrite. For an image, the purpose is the one judgement
the model cannot make: choose it (call `list_kinds` if unsure) before drafting.

---

## What to call, on every surface

The MCP tool name is the route's `operation_id`.

| Job | CLI | MCP tool | HTTP route |
|---|---|---|---|
| Lint markup | `sprezzature-accessibility-lint <file-or-dir>` | `lint_html` (takes a string) | `POST /v1/lint` |
| Repair mechanically | `sprezzature-accessibility-lint --fix <file-or-dir>` | *(not an MCP tool)* | *(none)* |
| Draft every missing alt in a page | `sprezzature-accessibility-lint --fix-alt <file-or-dir>` | *(not an MCP tool)* | *(none)* |
| List the rules | *(no flag; see `references/lint-rules.md`)* | `list_rules` | `GET /v1/rules` |
| List the image purposes | `sprezzature-accessibility-alt --help` (the `--kind` choices) | `list_kinds` | `GET /v1/kinds` |
| Draft alt text for one image | `sprezzature-accessibility-alt --kind <purpose> <image>` | `draft_alt_text` | `POST /v1/alt` |
| Text-spacing CSS | `sprezzature-accessibility-text-spacing` | *(not an MCP tool)* | *(none)* |
| Install the model | `sprezzature-accessibility-install-alt` | *(not an MCP tool)* | *(none)* |
| Liveness | *(none)* | `health` | `GET /health` |
| Which tools run here | `sprezzature-accessibility tools` | *(not an MCP tool)* | *(none)* |

Every CLI tool is also a sub-command of the front door: `sprezzature-accessibility
lint`, `text-spacing`, `alt`, `install-alt` (alias `make-a11y`; `make-alt` is an
alias of `sprezzature-accessibility-alt`). The MCP server is
`sprezzature-accessibility-mcp`, which mounts the endpoint at `/mcp` on the same
FastAPI app.

The jobs that write files (`--fix`, `--fix-alt`, the text-spacing CSS, the model
install) are command-line only. They change a project or a machine, and a tool that
returned the result for an agent to paste would be the worse half of that.

---

## What this cannot see: say so when you report

The linter parses source. There is no browser and no runtime DOM (Document Object
Model, the tree a browser builds), which is what makes it fast enough for a
pre-commit hook and is also its boundary:

- It cannot see markup **JavaScript builds**, only what is in the file.
- It cannot compute **colour contrast**: that is `sprezzature-colors`.
- It cannot follow **focus order** or test a real keyboard traversal.
- It reports that a caption track is **declared**, never that its text is right.

So a clean result means "none of the listed rules fired", never "this page is
accessible". Report it that way. It is a gate before a real audit (axe-core, Pa11y,
Lighthouse, and a person), not a substitute for one. A drafted alt text is a draft
too: a model cannot know what an image is for on that page.

---

## File patterns

`*.html` routes here whenever one of the objects above is in question and,
per the generalisation, whenever such a file was just written. Images (`*.png`,
`*.jpg` and the like) route here when what is wanted is their alt text or
long description.
