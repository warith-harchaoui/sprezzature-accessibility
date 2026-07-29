# Examples

## Lint a single file

```bash
python scripts/lint_a11y.py public/index.html
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
python scripts/lint_a11y.py public/
```

## JSON output for machine consumption

```bash
python scripts/lint_a11y.py --format json public/index.html | jq '.findings_total'
```

Output:

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
python scripts/lint_a11y.py --ignore heading-skip,motion-no-reduce-guard public/
```

## Auto-fix in place

```bash
python scripts/lint_a11y.py --fix public/index.html
```

stderr output:

```
public/index.html: applied 2 fix(es); 1 unfixable finding(s); 1 remaining.
1 remaining finding(s) after fix pass.
```

Rules with a fixer: `html-missing-lang`, `img-redundant-aria`,
`tabindex-positive`, `aria-hidden-interactive`, `motion-no-reduce-guard`.

Rules without a fixer (require a content decision): `a-empty`,
`button-empty`, `input-missing-label`, `heading-skip`, `dialog-missing-close`,
`color-only-state`.

## Preview fix without writing

```bash
python scripts/lint_a11y.py --fix --dry-run public/index.html
```

Exits 0 always (preview, not a verdict).

## Pre-commit hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: a11y-lint
        name: Accessibility lint
        entry: python scripts/lint_a11y.py
        language: python
        files: \.html$
        args: ["public/"]
```
