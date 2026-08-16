# Landscape

Accessibility tools split into two families by how they inspect a page. A
**static** tool reads the HTML source text, the way you would with your
eyes; it never opens a browser. A **runtime DOM** tool drives a real
browser, lets it fully render the page into a DOM (the tree of elements a
browser assembles while displaying it), and inspects that live tree, which
catches things no static read can, at the cost of needing a browser engine
to run. This compares `sprezzature-accessibility`, a static tool, to the
main accessibility testing tools available today, most of which are
runtime-DOM.

## Tool comparison

| Tool | Type | Browser needed | Fixable | CI-friendly | Python |
|---|---|---|---|---|---|
| **sprezzature-accessibility** | Static linter | No | Yes (5 rules) | Yes | Yes |
| axe-core | Runtime DOM | Yes | No | Yes (via CLI) | No |
| Pa11y | Runtime DOM | Yes (Chromium) | No | Yes | No |
| WAVE | Browser ext. | Yes | No | No | No |
| htmlhint | Static HTML | No | No | Yes | No |

### Ratings

| Dimension | sprezzature-accessibility | axe-core | Pa11y | WAVE |
|---|---|---|---|---|
| Rule coverage | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Speed (CI) | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐ |
| Zero-dep install | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐ | N/A |
| Auto-fix | ⭐⭐⭐ | ⭐ | ⭐ | ⭐ |
| False positives | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |

## When to use what

Use `sprezzature-accessibility` as a **first gate** in pre-commit and CI:
it catches the obvious violations in milliseconds, with no Chromium to
spin up. Follow it with axe-core or Pa11y in a separate browser-test job
for runtime DOM coverage.

WAVE is better suited to manual audits and exploratory testing. It gives
a visual overlay that helps a human understand the issue in context.

htmlhint checks HTML syntax and some structural rules, not accessibility.
The two tools are complementary.
