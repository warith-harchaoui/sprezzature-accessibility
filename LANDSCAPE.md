# Landscape

This compares `sprezzature-accessibility` to the main accessibility
testing tools available today.

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
