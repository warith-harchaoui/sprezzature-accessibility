# Contributing

## Setup

```bash
git clone https://github.com/warith-harchaoui/sprezzature-accessibility
cd sprezzature-accessibility
pip install -e ".[dev,lang]"
```

## Tests

```bash
pytest
```

## Lint

`ruff` is the Python linter and formatter this project uses: it reads the
source without running it and flags style issues (unused imports, wrong
quote style, and the like) in one fast pass.

```bash
ruff check scripts/ sprezzature_accessibility/
```

## Adding a rule

1. Add a `check_<rule_name>(root: Element) -> list[Finding]` function in
   `scripts/lint_a11y.py`.
2. Register it in `ALL_RULES` dict.
3. If a mechanical fix exists, add a `_fix_<rule_name>` function and
   register it in `RULE_FIXERS`.
4. Add a test in `tests/test_accessibility.py`.
5. Document the rule in `EXAMPLES.md`, the rules table in `README.md`, and
   its WCAG/WAI-ARIA mapping in `references/lint-rules.md`.

## Code standards

See `references/CODING.md`. NumPy docstrings, full typing, ~25-30%
comment density.

## Prose standards

See `references/WRITING.md` (EN) and `references/ECRITURE.md` (FR).
No punctuation dashes, no machine tells.
