"""
sprezzature-accessibility — static HTML accessibility linter.

Fourteen rules from WCAG (Web Content Accessibility Guidelines) and
WAI-ARIA (the W3C's accessible-widget attribute vocabulary), each
decidable by reading the HTML source alone, with no browser involved:
missing alt text, unlabelled inputs, empty buttons, onclick divs,
missing dialog close, lang attribute, heading order, color-only state,
and motion-reduce guards. Stdlib only (Python 3.10+). Pairs with
axe-core / Pa11y, which check the page after a browser has rendered it
(the "runtime DOM"), for the failures that only show up there.
"""

__version__ = "1.0.0"
__author__ = "Warith HARCHAOUI"
__email__ = "warith.harchaoui@gmail.com"
__license__ = "BSD-3-Clause"
