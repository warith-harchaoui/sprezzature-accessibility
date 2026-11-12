# AI-assisted alt text

The drafting half of this package writes `alt` text for an image, following the
W3C (World Wide Web Consortium, the body that writes the web's standards) / WAI
(Web Accessibility Initiative) image decision tree
(<https://www.w3.org/WAI/tutorials/images/decision-tree/>). It uses a **local
vision model served by Ollama**: nothing leaves the machine.

- **Model:** `qwen3-vl:8b`, the one model this package uses. The call goes through
  `best_engine_ai_helper.llm.chat` with an explicit engine descriptor: backend
  `ollama`, the endpoint below, this model.
- **Endpoint:** `http://localhost:11434`, overridden by `OLLAMA_URL`. That is the
  address the call reaches and the one an error message names. The
  `SPREZZATURE_LLM_*` variables best-engine-ai-helper reads on its own do not move
  it (until 2026-11-05 they did, and the message then named a server nobody called).
- `OLLAMA_MODEL` exists as an escape hatch for tests. It is not a supported way to
  choose another model.

Runtime: Python 3.10 to 3.13, the same range as the package.

## W3C decision tree

Every image has a *purpose* in the page. Match the purpose to the right alt
strategy before drafting anything. The six purposes are the values of `--kind`
(and of `KINDS`, and of `GET /v1/kinds`).

| Purpose | Alt strategy |
|---|---|
| **decorative** (no information) | `alt=""`: empty alt only. No `role="presentation"` or `aria-hidden` needed. No model call. |
| **informative** (conveys meaning) | Short alt describing the meaning in page context. `--kind informative`, the default. |
| **functional** (inside `<a>` / `<button>`) | Alt describes the *action or destination*, not the image. `--kind functional --context "<what the control does>"`. |
| **text** (mostly text) | Alt is the readable text, verbatim. `--kind text`. |
| **complex** (chart, diagram, infographic) | Short alt plus a long description elsewhere (`<figcaption>` or `aria-describedby`). `--kind complex`, with `--longdesc` for the long description. |
| **group** of related images | One alt describes the whole; the rest get `alt=""`. `--kind group`. |

`alt=""` is the empty-alt signal. **Never omit the `alt` attribute**: a screen
reader then reads the file name.

## Install Ollama and pull the model

The Python dependencies come with `pip install sprezzature-accessibility`. Ollama
and the model weights do not, so one command installs them:

```bash
sprezzature-accessibility-install-alt
```

It:

- installs Ollama if it is missing, with the package manager the host has:
  Homebrew (`brew install ollama`) on macOS, and on Linux when Homebrew is present;
  the official installer script on other Linux hosts; `winget install
  Ollama.Ollama` on Windows;
- starts the Ollama daemon if it is not already running;
- pulls `qwen3-vl:8b`.

Re-running it is harmless: it does nothing when Ollama and the model are present.
With Docker, `docker compose --profile alt up -d` starts an Ollama container beside
the API (Application Programming Interface, the door other programs use) instead.

## Generate alt text

```bash
# informative (default)
sprezzature-accessibility-alt ./public/hero.jpg

# language
sprezzature-accessibility-alt --lang fr ./public/hero.jpg

# functional: describe the destination or action, not the visual
sprezzature-accessibility-alt --kind functional --context "Submit signup form" ./public/icons/check.png

# text in an image: return the readable text verbatim
sprezzature-accessibility-alt --kind text ./public/quote-card.png

# complex (chart): returns a SHORT summary; pair it with a long description
sprezzature-accessibility-alt --kind complex --context "Weekly active users" ./public/chart.png

# complex AND long description: writes the Markdown long description to chart.png.longdesc.md
sprezzature-accessibility-alt --kind complex --longdesc --context "Weekly active users" ./public/chart.png

# Use the text around the image in a Markdown or HTML document as BOTH context
# and vocabulary. The highest-signal source for an embedded image.
sprezzature-accessibility-alt --in blog/post.md ./blog/figures/hero.png

# Walk up to the project root and mine it for proper-noun vocabulary
sprezzature-accessibility-alt --auto-project ./figures/diagram.png

# decorative: no model call; the command prints nothing
sprezzature-accessibility-alt --kind decorative ./public/divider.svg
```

`make-alt` and `sprezzature-accessibility alt` are the same command.

Output: one line of alt text on stdout, capped at 150 characters (`MAX_CHARS`) at a
word boundary, **never** with a trailing `…`. Empty stdout for decorative. Exit code
0 on success, 2 when the model cannot be reached or the image or a named document
cannot be read, 1 when the model client (`best-engine-ai-helper`) is missing from
the install.

Language: `--lang` wins. Without it, the language is detected from the context
text (`--context`, the `--in` document, the vocabulary); with no text at all, it
falls back to the environment locale (`ALT_LANG`, then `LC_ALL`, then `LANG`).

`--resize N` downscales the longest edge to N pixels (1024 by default, 0 disables).
Pillow, which does the downscaling, is in the base install.

### A whole page at once

```bash
sprezzature-accessibility-lint --fix-alt public/
sprezzature-accessibility-lint --fix-alt --dry-run public/index.html
```

`--fix-alt` drafts every `<img>` the lint reports as `img-missing-alt`, as an
informative image, and splices the `alt` into the file. The context is the 400
characters on each side of each reference to that image in the same document, and
the vocabulary is mined from that document. Without `--alt-lang`, the language is the
page's `<html lang>`, else the one detected in the page text, else the environment
locale. Remote images, images
missing from disk, and tags the line-based splice cannot reach are left alone and
reported on stderr.

### Python API

```python
from sprezzature_accessibility import describe, describe_long

alt = describe("public/hero.jpg", kind="informative", lang="fr", context="Careers page hero")
long_text = describe_long("public/chart.png", kind="complex", context="Weekly active users")
```

`describe` also takes `resize`, `model` and `vocabulary`. `describe_long` takes the
same arguments except `vocabulary`.

### HTTP

`POST /v1/alt` (MCP tool `draft_alt_text`) takes `src`, `kind`, `lang`, `context`,
`resize`, `model`, `vocabulary` and `long`, and returns `alt`, `long`, `lang`,
`kind` and `draft` (always true). `src` is a path the server opens or an `http(s)`
URL it fetches, so keep the port on a trusted network (`docker-compose.yml` publishes it on `127.0.0.1` only). It answers 502 when the model
cannot be reached, 503 when the model client is missing from the install, and 404
when the image cannot be read, as a file or as a URL. A browser page cannot call Ollama directly
(Ollama does not answer CORS (Cross-Origin Resource Sharing, the permission a
server gives a page from another site to call it) requests from web pages), so this route is the proxy
to put in front of it.

## Rules the prompt enforces

1. **Image purpose decides the prompt** (per W3C). There is no generic prompt.
2. **Hard cap at 150 characters**: no `…` truncation; the text is cut at a word
   boundary.
3. **Match meaning, not pixels.** A photo of a smiling teacher in a classroom is
   "Teacher leading a class", not "An adult standing in front of children with a
   chalkboard behind".
4. **No banned prefixes**: "image of", "photo of", "picture of", "illustration of",
   and their equivalents in 9 other languages. They are stripped if the model
   ignores the instruction.
5. **Be specific where relevant to meaning.** For news photos, name visible people,
   setting, action; do not sanitise to "a person".
6. **Functional alt describes the action**, not the visual. A magnifying-glass icon
   in a search button gets `alt="Search"`, not `alt="Magnifying glass"`.
7. **Text-as-image is extracted verbatim.**
8. **Complex returns a short alt only**; the long description belongs in
   `<figcaption>` or `aria-describedby`.

## Review workflow

AI-generated alt is a draft, not a final answer. Neither `--fix-alt` nor the
command line marks what it wrote, so tag each drafted attribute yourself if a
review tool is to find it:

```html
<img src="…" alt="Teacher leading a class" data-alt-source="ai">
```

Strip `data-alt-source="ai"` once a person has reviewed and approved it.

## Cache

Drafts are cached on disk so the same input never reaches the model twice.

- **Store:** a `wallet-helper` ledger, one single-file database, `ledger.db`, under
  `~/.cache/sprezzature-skill/alt/` (override the parent directory with
  `SPREZZATURE_CACHE_DIR=<path>`). The Docker compose file points it at a named
  volume.
- **Key:** SHA-256 (Secure Hash Algorithm, a 256-bit fingerprint of the content) of the image bytes actually sent (after resizing), `kind`, `lang`,
  `context` and the model tag, truncated to 32 hex characters.
- **Single flight:** two processes drafting the same image at the same time share
  one model call; the second waits for the first.
- **Bypass once:** `--no-cache`.
- **Bypass globally:** `SPREZZATURE_NO_CACHE=1`.
- **Clear:** delete the directory.

## Failure modes

| Symptom | Likely cause | Fix |
|---|---|---|
| Model unreachable, exit code 2 (502 over HTTP) | Daemon not running | `sprezzature-accessibility-install-alt` (harmless to re-run) or `ollama serve`. |
| Exit code 1 (503 over HTTP), "model client … missing" | `best-engine-ai-helper` absent, as after a `--no-deps` install | `pip install sprezzature-accessibility`. Starting Ollama does not help. |
| `Error: model not found` | Model never pulled | Re-run the installer, or `ollama pull qwen3-vl:8b`. |
| Garbled or hallucinated text | Very small or very large image | The image is downscaled to 1024 px by default; improve the source or try `--resize 768`. |
| Very slow first call | First inference loads the weights | Later calls are faster; keep the daemon up. |

## Related: meta tags

`sprezzature-publish` drafts page-level `<title>`, `<meta name="description">`,
Open Graph and JSON-LD (JavaScript Object Notation for Linked Data, the structured data search engines read) tags with the same local-model setup. That is a separate
package.

## Checklist

- [ ] `sprezzature-accessibility-install-alt` ran and the model is in `ollama list`.
- [ ] `sprezzature-accessibility-alt <test image>` returns a non-empty string.
- [ ] Decorative images use `alt=""` alone (no `role="presentation"`, no `aria-hidden`).
- [ ] Every AI-drafted `alt` is reviewed by a person before it is committed.
- [ ] Complex images pair a short alt with a long description in `<figcaption>` / `aria-describedby`.
- [ ] Functional `alt` describes the action or destination, not the icon.
- [ ] No `alt` ever ends in `…`.
