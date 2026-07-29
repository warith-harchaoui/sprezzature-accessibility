# Triggers

Natural-language phrases that invoke the sprezzature-accessibility skill.

## Direct invocations

- "Run the accessibility linter on this HTML"
- "Check this page for a11y issues"
- "Lint for WCAG compliance"
- "Static accessibility check"
- "A11y pre-commit gate"
- "Check for missing alt text"
- "Find unlabelled inputs"
- "Check ARIA usage"
- "Fix accessibility issues"
- "Run lint_a11y.py"

## Intent-based phrases

- "Is this HTML accessible?"
- "Does this page pass WCAG?"
- "Check for keyboard navigation issues"
- "Look for clickable divs without roles"
- "Are all buttons labelled?"
- "Check headings order"
- "Find color-only state cues"
- "Are there animation issues for reduced-motion users?"
- "Does this dialog have a close button?"

## File patterns

Files matching `*.html` routed to this skill when an accessibility
concern is expressed.

## Related scripts

- `scripts/lint_a11y.py` — main linter
- `scripts/_lang.py` — language detection helper
- `scripts/_argparse.py` — shared parser factory
