# Contributing

## Setup

```bash
git clone https://github.com/warith-harchaoui/sprezzature-accessibility
cd sprezzature-accessibility
pip install -e ".[dev]" -r requirements-dev.txt
git config core.hooksPath .githooks
```

`[dev]` brings pytest and ruff. `requirements-dev.txt` adds what CI also installs:
mypy, langdetect and httpx2 (for the FastAPI test client). The last line turns on
the pre-push hook, which runs the same steps as CI before a push.

## Tests

```bash
pytest -q
```

The default run deselects the `eval` marker. Those tests judge the quality of
real model output and need a running Ollama with `qwen3-vl:8b`; run them with
`pytest -m eval` (see `tests/fixtures/images/README.md`).

## Lint and types

`ruff` is the Python linter this project uses: it reads the source without
running it and flags style issues (unused imports, import order, and the like)
in one fast pass. `mypy` checks the type annotations. CI runs:

```bash
ruff check .
mypy sprezzature_accessibility
mypy scripts
```

## Adding a rule

1. Add a `check_<rule_name>(root: Element) -> list[Finding]` function in
   `scripts/lint_a11y.py`.
2. Register it in the `ALL_RULES` dict.
3. If a mechanical fix exists, add a `_fix_<rule_name>` function and
   register it in `RULE_FIXERS`.
4. If the rule is a warning rather than an error, add it to `_SEVERITY` in
   `sprezzature_accessibility/api.py`.
5. Add a test in `tests/test_lint_a11y.py` or `tests/test_accessibility.py`.
6. Add the rule to the rules tables in both `README.md` and `LISEZMOI.md`,
   and its WCAG/WAI-ARIA mapping to `references/lint-rules.md`. Update every
   rule count written in prose. `tests/test_release_consistency.py` fails when a
   table misses a rule or a count is stale.

## Code standards

See `references/CODING.md`. NumPy docstrings, full typing, ~25-30%
comment density.

## Prose standards

See `references/WRITING.md` (EN) and `references/ECRITURE.md` (FR).
No punctuation dashes, no machine tells.
