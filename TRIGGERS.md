# Triggers

When to run the accessibility linter, and what to call.

This file is written for an agent — a Claude Code / OpenCode skill, an MCP
host, anything choosing a tool on someone's behalf. Humans are welcome, but
the routing rules below are the point.

---

## The generalisation, stated once

> **Writing HTML is the trigger. Nobody has to ask.**
> The listed phrasings below all route here, but waiting for one of them is
> the mistake: the markup you just generated is exactly the markup nobody
> has checked. Run `lint_html` over any page, component, form or dialog you
> author, before you hand it over — the same way you would not ship code
> without running it once.

When someone *does* ask, the request arrives in one of three shapes:

| The user is… | Call | Typical phrasings (EN / FR) |
|---|---|---|
| **asking for a check** | `lint_html` | "is this accessible", "a11y lint", "check for missing alt", "does this pass WCAG", « vérifie l'accessibilité », « il manque des alt ? » |
| **asking what is covered** | `list_rules` | "what do you check", "which rules", "can you catch X", « qu'est-ce que tu vérifies » |
| **asking for a fix** | `lint_html`, then edit | "fix the accessibility issues", "make this WCAG-friendly", « corrige l'accessibilité » |

The third shape is the common one and the one to get right: lint first, fix
what it names, lint again. Findings carry a line number and a rule id, so a
fix is a targeted edit rather than a rewrite.

---

## What to call, on every surface

| Job | CLI | MCP tool |
|---|---|---|
| Lint markup | `sprezzature-accessibility-lint <file.html>` | `lint_html` (takes a string) |
| What the rules are | `sprezzature-accessibility-lint --list-rules` | `list_rules` |
| WCAG 1.4.12 text-spacing preset | `sprezzature-accessibility-text-spacing` | *(not an MCP tool)* |

The text-spacing preset emits CSS into a project, which is a file job rather
than a question; the command writes it, and a tool that returned CSS for an
agent to paste would be the worse half of that.

---

## What this cannot see — say so when you report

The linter parses source. There is no browser and no runtime DOM, which is
what makes it fast enough for a pre-commit hook and is also its boundary:

- It cannot see markup **JavaScript builds**, only what is in the file.
- It cannot compute **colour contrast** — that is `sprezzature-colors`
  (`check_contrast`), and a page can pass here and still be unreadable.
- It cannot follow **focus order** or test a real keyboard traversal.
- It does not draft **alt text**; it only reports that alt is missing.
  Drafting is `sprezzature-vision`.

So a clean result means "none of the listed rules fired", never "this page
is accessible". Report it that way. It is a gate before a real audit
(axe-core, Pa11y, Lighthouse, and a person), not a substitute for one.

---

## File patterns

`*.html` routes here whenever an accessibility concern is expressed — and,
per the generalisation above, whenever such a file was just written.
