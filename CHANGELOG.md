# Changelog

All notable changes to sprezzature-accessibility are documented here.

## [Unreleased]

## [1.4.2] — 2026-11-05

### Fixed

- **The drafter called one server and named another.** `make-alt`,
  `sprezzature-accessibility-alt`, `--fix-alt` and `POST /v1/alt` read
  `OLLAMA_URL` only to print it in "Cannot reach Ollama at …", while the model
  call went through `best_engine_ai_helper.llm.chat` with no endpoint, so to
  best-engine-ai-helper's own setting (`SPREZZATURE_LLM_BASE_URL`, localhost by
  default). In the compose stack, which sets `OLLAMA_URL=http://ollama:11434`,
  the draft failed against the API container and the message blamed the
  `ollama` service. Every call now passes
  `engine={"backend": "ollama", "base_url": OLLAMA_URL, "llm": …, "vlm": …}`;
  the `vlm` section is the one `chat` reads for a call with an image, and a
  descriptor without it raises `KeyError` before any request.
  `tests/test_the_model_call_goes_where_the_message_points.py` records the
  arguments with a fake `chat` (no server, no model) and fails on the old code.
- **`best-engine-ai-helper>=1.11.0`**, up from `>=0.4.0`, in `pyproject.toml`
  and `scripts/requirements-alt-text.txt`. `engine=` exists from 1.1.0, and
  every release from 1.0.0 to 1.10.0 caps `os-helper` below 3 or 4, so none
  installs beside a brick that needs `os-helper>=4`; 1.11.0 is the first with
  both. Its Python window is unchanged (`>=3.10`), so the reachability table in
  `tests/test_the_promise_covers_what_it_inherits.py` stands.

### Removed

- **The branch that told a reader to install an extra.** `TOOLS` carried an
  extra per tool, empty for all four since 2026-11-01, and its only reader was
  a branch of `missing_extra_message` printing
  `pip install 'sprezzature-accessibility[…]'` plus a `needs […]` mark in
  `sprezzature-accessibility tools`. The field and both branches are gone;
  the message is now `broken_install_message(tool, exc)`, with the same text
  as before. A test holds the premise: pyproject declares no extra but `[dev]`.

### Docs

- README, LISEZMOI and `references/alt-text-ai.md` say what `OLLAMA_URL` does:
  it is the address the call reaches and the one an error names.
  `sprezzature-accessibility-install-alt --help` no longer lists it as the
  installer's endpoint: the installer drives the `ollama` command, which reads
  `OLLAMA_HOST`.

## [1.4.1] — 2026-11-05

### Fixed

- **`sprezzature-accessibility -V` was a usage error.** The front door answered
  `--version` only, while every per-tool command and the README promised `-h`
  and `-V`. The group now takes both.
- **`sprezzature-accessibility tools` cut a summary at its first dot**, so the
  text-spacing line ended on "at the WCAG 1." It now cuts on a sentence end.
- **A missing model client was reported as a dead daemon.** When
  `best-engine-ai-helper` did not import, the drafter said "Cannot reach
  Ollama" and advised `ollama serve`, which cannot repair an install. It now
  raises `ModelClientMissing`, prints the reinstall line and exits 1 (2 stays
  "model unreachable"); `POST /v1/alt` answers 503 for it instead of 502. Two
  tests in `tests/test_alt_from_ollama.py` and one in `tests/test_api_mcp.py`
  hold the split.
- **CI installed `wallet-helper>=1.3,<2`**, looser than the package's own
  `>=1.3.2,<2`, with a comment saying 1.3.2 was not on PyPI. It is; the extra
  constraint is gone and the install follows `pyproject.toml`.

### Docs

- Help and error strings that still spoke of an optional extra (the front door
  epilog, `import sprezzature_accessibility` on a `--no-deps` install, the
  model-client message, the `--fix-alt` help) now say the install is broken
  or name `sprezzature-accessibility-install-alt`. The rule catalogue in
  `lint_a11y.py`'s docstring listed fifteen rules; it lists the twenty.
  Stale "optional" and "extra" comments in `requirements.txt` and the
  Dockerfile are gone. `EXAMPLES.md` names the text-spacing command rather than
  its script file.

## [1.4.0] — 2026-11-04: click everywhere, the page's own language for --fix-alt

### Changed

- **The last three argparse commands are click.** `sprezzature-accessibility-lint`,
  `sprezzature-accessibility-text-spacing` and `sprezzature-accessibility-mcp`
  keep their flags, defaults, choices, help texts and exit codes (2 on a usage
  error), and each `main` takes `argv`. `scripts/_argparse.py` had no caller left
  and is deleted. `tests/test_every_command_is_click.py` asks every console
  script for `--help` and scans the shipped sources for an argparse import; it
  fails on the previous code. The examples in the `--help` epilogs stay one per
  line, which `sprezzature-accessibility-alt` had lost to click's rewrapping.
- **The container serves `/mcp` too.** The Dockerfile CMD and the compose
  service run `sprezzature-accessibility-mcp --host 0.0.0.0 --port 8000`, which
  mounts the MCP endpoint on the same app as `/v1/...`. The previous CMD,
  uvicorn on `api:app`, never imported the MCP module. Checked by starting the
  server and calling `/health` and MCP `initialize` on one port;
  `tests/test_the_image_serves_mcp.py` holds the CMD.
- **The `description` on PyPI no longer says "stdlib only".** The lint needs
  click, and the package drafts alt text with a local model.

### Fixed

- **`--resize` did nothing on a default install.** Pillow was declared nowhere,
  so `maybe_resize` found no Pillow and sent the original bytes, whatever the
  flag said. `Pillow>=10.0.0` is a base dependency, and the README lines saying
  Pillow was optional are gone. `tests/test_resize_shrinks_the_image.py` drives
  `--resize 64` on a generated 400x200 image and reads 64x32 at the model.
- **`--fix-alt` drafted in the machine's language, not the page's.** Without
  `--alt-lang`, `fill_missing_alt` asked only the environment locale, while the
  flag's help promised detection from the document: a French page linted on an
  English machine got English alt text. It now uses the page's `<html lang>`,
  then detection on the page text (the same `detect_text_language` the
  single-image command uses), then the locale.
  `tests/test_fix_alt_writes_in_the_page_language.py` holds the order; two of
  its four tests fail on the previous code.
- **The API's fallback alt-text limit said 125; the engine cuts at 150.** When
  the engine cannot be imported, `api.py` now reads `DEFAULT_BASE` and
  `MAX_CHARS` from the engine's source instead of keeping copies.
  `tests/test_the_api_states_the_engine_limit.py` checks they agree.
- `scripts/requirements-alt-text.txt` floors follow `pyproject.toml`
  (`best-engine-ai-helper>=0.4.0`, `wallet-helper>=1.3.2`). Stale comments
  about argparse twins and the `[alt]` extra are corrected in `pyproject.toml`,
  `__init__.py`, `_tools.py`, `api.py`, `alt_from_ollama.run` and
  `docker-compose.yml`.

### Docs

The documents now say what the code does today. Each claim was checked against
the code, `--help` output and real runs.

- **README / LISEZMOI.** The alt-text drafter was nearly absent: `--fix-alt`,
  `--alt-lang`, `sprezzature-accessibility-alt`, `install-alt` and the
  `tools` sub-command are now documented, with the five surfaces (library, CLI,
  FastAPI with Docker and compose, MCP, skill), the five routes and their
  `operation_id`, and the five MCP tools. Corrected: "stdlib only, no pip install
  required" (the install needs click; the lint *imports* the standard library
  only); "optional `langdetect`" (a base dependency since 1.3.0); "for a
  pre-commit hook: three packages" over a body that said two; Python 3.10+ (the
  manifest says 3.10 to 3.13). The unverifiable "57 packages" count is gone.
  The `--fix-alt` language order is documented (see Fixed below).
- **TRIGGERS.md.** `sprezzature-accessibility-lint --list-rules` does not exist;
  the rules are listed by `list_rules` and `references/lint-rules.md`. Routing
  now runs on the domain's closed vocabulary (elements, WCAG criteria, the six
  image purposes, the rule ids). The tables cover every tool and all five MCP
  tools (`list_kinds` and `draft_alt_text` were missing). Drafting is no longer
  described as "behind the `[alt]` extra".
- **references/alt-text-ai.md.** Every command named `python
  scripts/alt_from_ollama.py`, which has no entry point; they now use
  `sprezzature-accessibility-alt`. Python 3.9+ became 3.10 to 3.13. The cache is
  a `wallet-helper` ledger, not a stdlib-only directory shared with
  `meta_from_ollama.py` (a `sprezzature-publish` script). The hand-written
  FastAPI proxy is replaced by `POST /v1/alt`. `OLLAMA_MODEL` is a test escape
  hatch, not an override. Pillow is optional and not installed.
- **references/lint-rules.md.** `aria-hidden-interactive` skips elements out of
  the tab order; `body-text-tracking-tight` skips display-size text;
  "decorative" video means `muted` without `controls`; `dialog-missing-close`
  accepts an autofocused button, not any autofocused element.
- **EXAMPLES.md.** The list of rules without a fixer named six of fourteen. The
  pre-commit example passed file names to a command that takes one target;
  it now sets `pass_filenames: false` and `language: system`.
- **CONTRIBUTING.md.** CI's `ruff check .` and mypy steps, `requirements-dev.txt`,
  the pre-push hook, `_SEVERITY`, and both rules tables.
- **LANDSCAPE / PAYSAGE.** "2.3 ms on a 16 KiB page" had no measurement in the
  repository behind it; replaced by what the tests do check.
- **Docstrings and help strings.** `mcp.py` described the colour brick's tools
  (`check_contrast`, `simulate_color_blindness`, `get_palette`); `alt_cli.py`
  described an argparse twin removed on 2026-10-25;
  `sprezzature-accessibility-install-alt --help` named a command
  `sprezzature a11y alt` that does not exist, and its closing hint pointed at
  `python scripts/alt_from_ollama.py`.

## [1.3.0] — 2026-11-01: one `pip install`

### Changed — one `pip install`

**Everything this package does now installs with it.** 5 extras became
**one**, and it is not a feature: `[dev]` is the test toolchain.

  The drafting half (best-engine-ai-helper, wallet-helper), the language
  detector and both surfaces. The base was **one** dependency.

  **One real cost, stated plainly.** The lint's argument was that it "is
  stdlib-only on purpose: it runs in milliseconds in a minimal CI container and
  in a pre-commit hook". The *install* half of that is spent: a pre-commit
  install now pulls the model client. The *import* half survives and is what
  made the argument true in practice — the lint still loads nothing but click,
  and `tests/test_the_lint_stays_out_of_the_extra.py` is now the only thing
  standing between that and one module-level import. Before, a careless import
  cost a reader who had opted into the drafter; now it costs everybody, on every
  run of the hook. The guard was rewritten to say so rather than deleted.

Measured across the suite before touching anything: **59 extras over eleven
repositories**, and **six bricks whose base was a single dependency** — so
`pip install <brick>` installed almost nothing and did almost nothing, and
choosing the right extra was a thing a reader had to know *before* the package
could do its job. Here the base goes from **1** to **8**
dependencies.

All eleven unions were dry-run resolved in a clean venv before any manifest was
edited, so this is a measured feasibility and not an optimistic one.

### Fixed — the places that encoded the extras

Install lines, error messages, docstrings, the `Dockerfile`, the CI workflow and
the README/LISEZMOI install sections all named extras that no longer exist. pip
treats an unknown extra as a **warning and exits 0**, so none of these would
have failed loudly: they would have quietly installed nothing.

The hub's `test_no_document_promises_an_extra_that_does_not_exist` found the
cross-repository ones — a document in one brick naming another brick's extra —
which no per-repository pass would have caught.


### Added — the pre-commit install, measured instead of promised

This package's argument for itself is that the lint "runs in milliseconds in a
minimal CI container and in a pre-commit hook, which is the reason anyone
reaches for it over axe-core". Folding the extras into the base took
`pip install sprezzature-accessibility` from **1 package to 57** — measured —
and most of those 57 are the HTTP and MCP surfaces, which a hook has no use
for.

The install half of that argument was spent, and the answer is not to
reintroduce an extra: one `pip install` for the product is the right call,
because a reader should not have to know a magic word before the package
works. The answer is to give a hook a documented, tested way to take only what
it runs:

```sh
pip install --no-deps sprezzature-accessibility
pip install click
```

**Two packages on top of a fresh venv** — click, and this one — and the lint
runs. A delta and not a total, and the first version of this file learned why
the hard way: it asserted "three packages: pip, click and this one" and went
red on CI's 3.10 and 3.11 runners, which seed **setuptools** as well.
`ensurepip` stopped doing that in 3.12 and this was written on a 3.13, so the
total was measuring the interpreter. Verified under 3.11 after the change:
total of four, delta of exactly two.
`tests/test_the_hook_install_is_the_lint_and_nothing_else.py` builds that venv,
counts what landed **by name** (a count alone would pass on a run that
installed `requests` and dropped `click`), and runs the shipped
`sprezzature-accessibility-lint` against a page with one known defect — proving
the result is *usable* and not merely installed, which are different claims and
the second is the one people assume they checked. A third assertion requires
both READMEs to carry the command: a tested command nobody can discover is not
available, and a documented one that drifts from the tested one is worse than
none.

It carries **no marker**, so it runs on every push. This repository learned the
cost of the alternative the same day, when two of `sprezzature-figures`' wheel
tests turned out to be among 428 deselected ones and only the pre-push hook
noticed.

The two halves are deliberately two tests. The import guard would still pass on
a 57-package install a hook never wanted; this one would still pass if the lint
quietly grew a module-level import of something pip installs anyway.

### Fixed — three messages that named a dead extra

The `/v1/alt` 503 no longer blames a missing extra: it names the two packages
that failed to import and says the install is incomplete, since they are base
dependencies. Both install sections carried four `pip install` lines, three of
which became identical when the extras went, under prose still claiming
"everything heavier is an extra". And `missing_extra_message`'s no-extra branch
— the only live one now — gives the reader something to run.


### Fixed — the draft cache could kill the run it was there to speed up

`scripts/alt_from_ollama.py` opens a `wallet_helper.SqliteLedger` to memoize
its model calls. **`wallet-helper` 1.3.1 — the newest release on PyPI — runs
`PRAGMA journal_mode=WAL` inside that constructor.** Going into WAL needs
exclusive access to the database file, and SQLite answers a journal-mode change
with `SQLITE_BUSY` *without consulting the busy handler*, so the thirty-second
timeout on that connection does not cover the one statement that needs it.

Three processes opening a cold ledger in the same instant therefore left one
dead on `database is locked` — and three processes drafting the same image is
precisely the case the ledger exists for.
`tests/test_two_drafts_of_one_image_cost_one_call.py` spawns exactly that, and
it is what found it: **3 failures in 15 runs**, measured, and failing the same
way before any of this release's changes.

It is fixed upstream in `wallet-helper` 1.3.2. **A fix nobody can install is
not a fix**: this package's CI resolves `wallet-helper>=1.3,<2` from the index,
and the index serves 1.3.1. So `_open_ledger` defends the caller against the
version it actually gets. Measured with the 1.3.1 code path in place:
**0 failures in 15 runs**.

Retrying is the right shape here rather than a papering-over: the ledger's whole
contract is "wait for the other process instead of duplicating its work", so
waiting tens of milliseconds for its own file to settle is the behaviour already
being asked for. What *would* paper over it is catching the error and running
the model anyway — three times, which is the cost the ledger exists to avoid.

**The pattern is `sprezzature-audio`'s and `sprezzature-publish`'s, not a new
one**, down to the `OPEN_ATTEMPTS` and `OPEN_BACKOFF` names and numbers. They
already carry it in their `scripts/_wallet.py`, and their own test for it reads
"the creation race, which cost a sibling repository a red run" — the sibling it
cost was this one. The first draft of this fix reinvented it and was worse in
two measurable ways, both corrected before landing:

- a **fixed** backoff where theirs is **jittered**. Three processes backing off
  on one schedule collide again on the next rung, which is the collision being
  recovered from;
- a `RuntimeError` on exhaustion where theirs **degrades** to the JSON
  `Ledger` over the same directory, with a warning on stderr. Raising trades a
  cache for a crash, and the crash *is* the defect — so the first draft
  re-entered the failure through the fix. What is lost on exhaustion is only
  cross-process single-flight; the memoization, the result, and a tool that
  answers all survive.

A corrupt file is also told apart from a lock, and in that order, because
`OperationalError` subclasses `DatabaseError`: no number of retries repairs a
bad file, and swapping the clauses would silently stop retrying locks at all.

`tests/test_the_draft_cache_survives_its_own_cold_start.py` covers it by
**injecting** the lock rather than racing for it, because the window is
narrower than a test can aim at — three shapes of deliberate contention were
tried upstream and none reproduced it, the busy handler *does* apply to
ordinary lock waits. Five assertions, failing for five different reasons: the
ladder is actually walked; it degrades instead of raising; a corrupt file is
not retried; the warning names the fixing release and what was lost instead of
leaving the reader with `database is locked`; and — the one that matters most —
**the shim carries its own removal condition.** The last test asserts the floor
is still below 1.3.2, so the day the floor moves past it, this file and
`_open_ledger` fail and say to delete themselves. A compatibility shim with no
removal condition becomes permanent by default.

## [1.2.1] - 2026-10-21

### Fixed

- **`TRIGGERS.md` routed an agent to a package that no longer exists.** The
  file told a reader that drafting alt text was `sprezzature-vision`'s job.
  That package was folded into this one; the command is
  `sprezzature-accessibility-alt`, behind the `[alt]` extra. An agent
  following the line ran nothing, or worse, reported the capability as
  belonging elsewhere and stopped. Found by a new guard in the monorepo
  that reads every brick's `TRIGGERS.md` and checks each command and MCP
  tool name it quotes against what the nine packages actually install.

- **Two counts of the rules disagreed with the rules.** The module
  docstring said fourteen; there are twenty. The rules table was missing
  from `LISEZMOI.md` entirely and one rule was missing from the English
  one. A number quoted to a reader has to come from the thing it
  describes, and three of them here did not.
- **The alt-text tests called a real model.** They now do not, so the
  default run needs nothing downloaded; the eval suite is excluded from
  the default run as `sprezzature-publish` already did it.
- **`httpx>=0.27` declared**, which starlette 1.9.0 needs for its
  `TestClient`.
- **The pre-push hook's mypy step was unpassable** on any machine with
  numpy installed, on all nine bricks. The rule now tolerates exactly one
  shape of failure, where every error reported lies outside the
  repository, and nothing else.

## [1.2.0] - 2026-10-19: the front door the skill was already promising

Since the monorepo split, this package's `SKILL.md` has told an agent the
tools are "invoked as `sprezzature-accessibility …`". Nothing installed that
command. An agent following the contract ran something that did not exist and
found out at the shell; a guard in the monorepo caught it by comparing all
nine skills against all nine `[project.scripts]` tables, and found two other
packages in the same state on the way.

### Added

- **`make-a11y` (argparse) and `sprezzature-accessibility` (click)**, two
  front doors over the same four tools — `lint`, `text-spacing`, `alt`,
  `install-alt`. Both read a single table (`sprezzature_accessibility/cli.py`)
  and share the one sentence said about a missing extra, so a tool cannot
  appear in one and be missing from the other, nor be explained differently by
  each. `make-a11y --help` prints the catalogue, which until now did not exist
  anywhere: four commands on the PATH and nothing listing them together.

  The table carries **full dotted module paths** rather than bare names,
  because these four do not all live in one place — the audit half is in the
  scripts package, the drafting half's command line is in the main one. A
  table that assumed a single prefix would have quietly excluded `alt`.

  Every per-tool command stays exactly where it was. Nothing here replaces
  `sprezzature-accessibility-lint`, `-text-spacing`, `-alt` or `make-alt`,
  which is what a script should keep calling.

- **A `[click]` extra.** Click belongs to one of the two front doors, so it is
  an extra rather than a dependency, and the import in `cli_click.py` is
  **guarded**. The lint half of this package has no dependencies at all —
  standard library, milliseconds, no browser — which is what makes it worth
  putting in a pre-commit hook; a twin that imported click at module load
  would end that silently, because the failure arrives at the console script
  rather than at the install. A bare install gets a sentence naming the extra,
  and is told `make-a11y` needs nothing.

  The guard is checked by hiding click from a subprocess, and verified by
  sabotage: with the `try/except` removed, three tests fail.

### Fixed

- **Two conditional definitions of `main` disagreed about their signature** in
  `alt_cli_click.py` — `() -> None` against `(argv) -> int`. A caller who
  imported `main` and passed an argv got a `TypeError` on the machine where
  the extra was missing and nowhere else, which is the hardest kind of bug to
  be told about: the person who hits it has the broken install and you have
  the working one. The refusal now matches the real command exactly.

- **The lazy export resolver had no return annotation.** `-> Any` is the PEP
  562 convention; `-> object`, tried first, type-checks the module and breaks
  every caller, since what comes back is called.

- **The README's PyPI-safety check read code blocks as links**, so an example
  containing a relative `href` failed the build. The rule is narrowed to the
  prose rather than weakened by an allow-list, with a second test proving a
  real relative link in prose still fails.

### Infrastructure

- The pre-push gate gained the step that checks the `eval` suite still
  collects. `-m eval` is excluded from the default run, so a syntax error in
  those files is invisible until somebody asks for them by name. The step was
  in the monorepo, pointing at an empty folder, long after the eval modules
  moved here.

## [1.1.1] — 2026-10-19

### Fixed

- **The two Click commands named a module, not an extra.** On a bare install,
  `sprezzature-accessibility-alt` and `-install-alt` answered
  `ModuleNotFoundError: No module named 'click'` — a traceback about a
  third-party package the reader never asked for, for a command their own
  `pip install` had just created. Click is an extra here on purpose: the
  argparse twin of every command needs nothing. They now name
  `pip install 'sprezzature-accessibility'`.
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
  for the audit, `pip install "sprezzature-accessibility"` for both.

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
