"""
fill_alt — close the audit→make loop for the one finding that needed a model.

``lint_a11y`` reports ``img-missing-alt`` and stops there, and its fixer table
says why in a comment: the rules absent from it are the ones whose repair
"needs a content decision the linter cannot make for the user". That was true
while this package could only read HTML. It is not true any more — the
drafting half can look at the image.

What makes the result worth writing into a file is the second input. A model
shown ``hero.jpg`` alone produces *a* description; a model shown ``hero.jpg``
**and the paragraph it sits in** produces the description that page needs.
The W3C decision tree asks what an image is *doing* on the page, and that is a
question about the page, not about the pixels. So every draft here is made
with the surrounding text of the very document being fixed, plus the proper
nouns mined from it, so the alt says "Serre-Ponçon in July" rather than
"a lake".

Why this is not a ``RULE_FIXERS`` entry
---------------------------------------
``--fix`` promises mechanical repairs: deterministic, offline, idempotent,
safe to run unattended in a hook. Drafting calls a model, takes seconds per
image, and writes prose a human should read. Folding it into ``--fix`` would
silently change what that flag means for every existing user. It gets its own
flag, ``--fix-alt``, and its own confirmation that drafts are drafts.

Author
------
`Warith HARCHAOUI, Ph.D. <https://www.linkedin.com/in/warith-harchaoui/>`_
"""

from __future__ import annotations

import html
import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lint_a11y import Finding, lint_file  # noqa: E402

#: ``src="…"`` on the offending line. Single or double quoted.
_SRC_RE = re.compile(r"""\bsrc\s*=\s*["']([^"']+)["']""")

#: Where to splice the new attribute: right after ``<img``.
_IMG_OPEN_RE = re.compile(r"<img\b", re.IGNORECASE)


@dataclass
class Draft:
    """One image, and what the model proposed for it."""

    line: int
    src: str
    alt: str
    context_chars: int

    def __str__(self) -> str:
        return f"L{self.line} {self.src} → {self.alt!r}"


def _resolve(document: Path, src: str) -> Path | None:
    """Turn an ``src`` attribute into a file on disk, or ``None``.

    Remote sources are returned as ``None`` rather than fetched: this runs
    over a developer's working tree, and silently reaching out to whatever a
    page happens to link to is not something a lint should do.
    """
    if re.match(r"^(?:https?:)?//|^data:", src, re.IGNORECASE):
        return None
    candidate = (document.parent / src.split("?")[0].split("#")[0]).resolve()
    return candidate if candidate.is_file() else None


def _insert_alt(line: str, alt: str) -> str | None:
    """Splice ``alt="…"`` into the first ``<img`` on this line."""
    match = _IMG_OPEN_RE.search(line)
    if match is None:
        return None
    escaped = html.escape(alt, quote=True)
    return f'{line[: match.end()]} alt="{escaped}"{line[match.end():]}'


def fill_missing_alt(
    path: Path,
    ignored: set[str] | None = None,
    *,
    lang: str | None = None,
    kind: str = "informative",
    dry_run: bool = False,
) -> tuple[list[Draft], list[Finding]]:
    """
    Draft and write ``alt`` for every image in ``path`` that has none.

    Parameters
    ----------
    path : Path
        HTML document to repair. Image sources are resolved relative to it.
    ignored : set of str or None, optional
        Rule ids to suppress, passed through to the lint.
    lang : str or None, optional
        BCP-47 base tag for the drafts. Detected from the document's own text
        when ``None`` — a French page should not be given English alt text
        because the machine's locale happens to be English.
    kind : str, optional
        W3C image purpose assumed for every image in this pass. ``informative``
        is the honest default: it is the purpose that calls for a description,
        and the one a human is most likely to be reviewing anyway. Images that
        are really decorative want ``alt=""``, which a person has to decide.
    dry_run : bool, optional
        Draft and report without touching the file.

    Returns
    -------
    (list of Draft, list of Finding)
        What was written (or would be), and the ``img-missing-alt`` findings
        that could not be drafted — a remote source, an image not on disk, or
        a tag the line-based splice could not reach.
    """
    # Imported here, not at module scope: the drafting half lives behind the
    # ``[alt]`` extra, and this module is importable without it so the error
    # message can name the extra instead of a traceback.
    try:
        from _vocab import resolve_vocab_terms, surrounding_text
        from alt_from_ollama import describe, detect_lang
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise ImportError(
            "--fix-alt needs the drafting half of this package. Install it "
            "with: pip install 'sprezzature-accessibility[alt]'"
        ) from exc

    findings = [
        f for f in lint_file(path, ignored or set()) if f.rule == "img-missing-alt"
    ]
    if not findings:
        return [], []

    raw = path.read_text(encoding="utf-8", errors="ignore")
    lines = raw.splitlines()
    drafts: list[Draft] = []
    unreachable: list[Finding] = []

    for finding in findings:
        index = finding.line - 1
        if not 0 <= index < len(lines):
            unreachable.append(finding)
            continue
        match = _SRC_RE.search(lines[index])
        if match is None:
            unreachable.append(finding)
            continue
        image = _resolve(path, match.group(1))
        if image is None:
            unreachable.append(finding)
            continue

        # The second input, and the reason this lives in the linter rather
        # than beside the model: the text around *this* reference, in *this*
        # document, plus the proper nouns the document uses.
        context = surrounding_text(path, image)
        vocabulary = resolve_vocab_terms(image, in_doc=path)
        language = lang or detect_lang()

        alt = describe(
            str(image),
            kind=kind,
            lang=language,
            context=context,
            vocabulary=vocabulary,
        )
        if not alt:
            unreachable.append(finding)
            continue

        spliced = _insert_alt(lines[index], alt)
        if spliced is None:
            unreachable.append(finding)
            continue
        lines[index] = spliced
        drafts.append(
            Draft(
                line=finding.line,
                src=match.group(1),
                alt=alt,
                context_chars=len(context),
            )
        )

    if drafts and not dry_run:
        text = "\n".join(lines)
        if raw.endswith("\n"):
            text += "\n"
        path.write_text(text, encoding="utf-8")

    return drafts, unreachable
