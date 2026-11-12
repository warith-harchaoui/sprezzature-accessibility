# Contributing

## Setup

```bash
git clone https://github.com/warith-harchaoui/sprezzature-accessibility
cd sprezzature-accessibility
pip install -e ".[dev]" -r requirements-dev.txt
git config core.hooksPath .githooks
```

`[dev]` brings pytest and ruff. `requirements-dev.txt` adds what CI (continuous
integration, the checks GitHub runs on every push) also installs: mypy, langdetect
and httpx2 (for the FastAPI test client). The last line turns on the pre-push hook,
which runs ruff, mypy, a collection of the `eval` suite and the tests before a
push.

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
in one fast pass. `mypy` checks the type annotations. CI runs ruff and the tests
on Python 3.12, and a second job installs and imports the package on Python 3.10,
the oldest version promised:

```bash
ruff check .
pytest -q
```

mypy runs in the pre-push hook only, not in CI:

```bash
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
   and its mapping to WCAG (Web Content Accessibility Guidelines) and WAI-ARIA
   (the `role` and `aria-*` attribute vocabulary) to `references/lint-rules.md`. Update every
   rule count written in prose. `tests/test_release_consistency.py` fails when a
   table misses a rule or a count is stale.

7. Update the rule catalogue of the skill,
   `sprezzature_accessibility/skill/references/lint-a11y.md`, and the rule list
   in `sprezzature_accessibility/skill/SKILL.md`.

## The skill

The agent skill ships inside the package, in `sprezzature_accessibility/skill/`.
Its body and `references/lint-a11y.md` are edited here. Two parts are not: the
`description:` of the `SKILL.md` front matter is held to the rules of the
[sprezzature](https://github.com/warith-harchaoui/sprezzature) hub, and
`references/triggers.md` is generated from it by the hub's
`scripts/build_triggers.py`; and
`sprezzature_accessibility/_skill.py` with
`tests/test_the_skill_ships_with_the_package.py` are shared verbatim by every
brick and kept in step by the hub's `scripts/sync_helpers.py`.

## Code standards

See `references/CODING.md`. NumPy docstrings, full typing, ~25-30%
comment density.

## Prose standards

See `references/WRITING.md` (EN) and `references/ECRITURE.md` (FR).
No punctuation dashes, no machine tells.
