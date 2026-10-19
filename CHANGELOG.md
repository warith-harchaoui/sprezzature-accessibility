# Changelog

All notable changes to sprezzature-accessibility are documented here.

## [1.1.1] — 2026-10-19

### Fixed

- **The two Click commands named a module, not an extra.** On a bare install,
  `sprezzature-accessibility-alt` and `-install-alt` answered
  `ModuleNotFoundError: No module named 'click'` — a traceback about a
  third-party package the reader never asked for, for a command their own
  `pip install` had just created. Click is an extra here on purpose: the
  argparse twin of every command needs nothing. They now name
  `pip install 'sprezzature-accessibility[alt]'`.
- **`body-text-tracking-tight` flagged display type.** A `<p>` at
  `text-4xl tracking-tight` holding a KPI figure is one glance, not a
  paragraph, and the evidence behind that rule is about continuous reading.
  The rule's own docstring had promised the exemption for headings; it could
  not see it inside a `<p>`. Found by `sprezzature-ui` — the package whose job
  is to set the example — failing this lint on its own shipped card.

## [1.1.0] — 2026-10-17

The package gains its missing half. It could say what a page got wrong about
images; it could not say what the image was. Now it can do both, and the
second is informed by the first.

### Added

- **`--fix-alt`**, which closes the audit→make loop for the one finding that
  needed a model. The lint reports `img-missing-alt`; this drafts the text
  and writes it in, using the image **and the surrounding text of the very
  page being fixed** — the heading above it, the sentence beside it, and the
  proper nouns the document itself uses. The W3C decision tree asks what an
  image is *doing* on the page, which is a question about the page, not about
  the pixels.
- **The drafting half**, merged in from the former `sprezzature-vision`:
  `make-alt` (argparse) and `sprezzature-accessibility-alt` (click) over one
  engine, `sprezzature-accessibility-install-alt` for the model, nine prompts
  tuned per image purpose, an on-disk cache, and language detection from the
  document rather than the machine's locale.
- **A library surface.** `sprezzature_accessibility` exported only
  `__version__` before. It now exports `lint_file` and `fix_file` eagerly,
  and the drafting functions lazily.

### Changed

- `--fix` is unchanged, deliberately. It promises mechanical, offline,
  idempotent repairs, and drafting is none of those: it calls a model, takes
  seconds per image, and writes prose a human should read. Folding it in
  would silently change what the flag means for everyone already using it.
- The drafting half sits behind an **optional `[alt]` extra**. The lint stays
  stdlib-only with zero dependencies, which is the reason it is worth
  reaching for in a pre-commit hook: `pip install sprezzature-accessibility`
  for the audit, `pip install "sprezzature-accessibility[alt]"` for both.

## [1.0.3] - 2026-10-02: the half of the dependency guard nobody runs

### Fixed

- **`mcp.py` defined `main` twice, and the two took different arguments.** One
  definition sits in the `except ImportError` branch reached when the `[mcp]`
  extra is absent, the other in the `else` branch that serves the real
  endpoint. A single console script reaches both, so to a caller they are one
  function. They were not: the fallback took nothing while the real one took
  `argv`, so `main(["--host", "127.0.0.1"])` answered on a machine with the
  extra and raised `TypeError` on a machine without it. The broken half is the
  one a reader who skipped the extra meets first.
- **The declared homepage named a host that no longer answers.**
  `project.urls` pointed at `harchaoui.org`, now returning 503, and PyPI
  prints that link on the package page. It points at `sprezzature.ai`.
- **The quick start showed a command a PyPI reader cannot run.** `python
  scripts/...` is a path that exists in a clone and not in a wheel.

### Added

- **A type gate**, `mypy.ini` plus one CI step. The monorepo carried one while
  the skills lived there; at the split ruff came with the package and mypy did
  not, so no standalone package checked its own annotations. Run by hand, it
  found the `main` defect above in six packages at once. The step runs once, on
  3.12: this is a gate, not a test matrix.
- **Two tests for the same ground.** `test_mcp_fallback_signature.py` reads the
  source as a syntax tree, so it needs neither mypy nor an install.
  `test_console_scripts_exist.py` checks that every command the help text names
  is a command pip installs; it could previously report green while testing
  nothing when its scan found no candidates, which a new case rules out.
- **A versioned `.githooks/pre-push`** running the same lint, type and test
  steps as the workflow, in the same order, so a red state cannot reach the
  remote.

## [1.0.2] - 2026-09-14: the rule count on the package page itself

### Fixed

- **1.0.1 corrected the count in five files and shipped it wrong in the
  sixth.** `pyproject.toml`'s `description` is the one line PyPI prints above
  everything else, and it still said "15 WCAG/WAI rules". The guard added in
  1.0.1 could not catch it: its list of count-claiming files was written by
  hand and did not include the file the package page renders. It does now —
  the same lesson as the release it was written for, one level up.

## [1.0.1] - 2026-09-14: the linter has twenty rules, and every document said fifteen

### Fixed

- **Five rules nobody knew existed.** `ALL_RULES` holds twenty; the README, the
  LISEZMOI, `references/lint-rules.md`, the module docstring and the CLI help
  all said fifteen. The five left out are one coherent family —
  `video-missing-captions`, `audio-missing-transcript`, `media-autoplay-sound`,
  `media-missing-controls`, `track-missing-srclang` — and WCAG 1.2 is the only
  criterion family no other rule here touches. It is also the one that locks a
  Deaf or hard-of-hearing visitor out of a page rather than merely making it
  awkward: a `<video>` with no caption track is not a degraded experience, it
  is no experience.

  A reader of the README could not learn their `<video>` was being checked at
  all. That is the expensive half of the mistake — not a wrong number, an
  invisible feature. `references/lint-rules.md` gains a table for them with the
  criterion each maps to, and the limit that matters: a static linter can tell
  that a caption track is **declared**, never that its text is correct or
  synchronised. It reports the absence, which is the failure it can prove.

- Two phrasings of the form "the other fourteen rules" that go stale on every
  addition by construction. The arithmetic is gone rather than corrected.

### Added

- `tests/test_release_consistency.py`. `__version__` must equal the version
  pyproject declares — it is what `api.py` hands FastAPI, so it reaches
  `/openapi.json` and the headline an MCP host displays, and in
  `sprezzature-figures` that pair drifted through an entire release. The
  CHANGELOG must lead with the same number. And any rule count written at a
  reader, digits or words, English or French, must equal `len(ALL_RULES)`;
  writing that check is what turned up the two stale phrasings above.

## [1.0.0] - 2026-07-29

### Added

- Initial release extracted from the sprezzature monorepo.
- `scripts/lint_a11y.py`: 14-rule static HTML accessibility linter with
  text and JSON output, `--ignore`, `--fix`, and `--dry-run` modes.
- `scripts/_lang.py`: shared language detection helper (stdlib + optional
  langdetect) used by the html-missing-lang auto-fixer.
- `scripts/_argparse.py`: shared argparse factory used across all scripts.
- Rules: img-missing-alt, img-redundant-aria, a-missing-href, a-empty,
  button-empty, div-onclick, input-missing-label, dialog-missing-close,
  html-missing-lang, tabindex-positive, aria-hidden-interactive,
  heading-skip, color-only-state, motion-no-reduce-guard.
- Auto-fixers for: html-missing-lang, img-redundant-aria, tabindex-positive,
  aria-hidden-interactive, motion-no-reduce-guard.
