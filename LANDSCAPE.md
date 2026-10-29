# Landscape

`sprezzature-accessibility` is the accessibility brick of the
[sprezzature](https://sprezzature.ai/) suite, ten Python packages for building
publication-quality web content. It does two things the rest of the field keeps
apart: it audits HTML source for twenty WCAG (Web Content Accessibility
Guidelines, the W3C standard that defines what "accessible" means for the web)
and WAI-ARIA (Web Accessibility Initiative, Accessible Rich Internet
Applications, the attribute vocabulary that lets custom widgets describe
themselves to assistive software) defects decidable without a browser, and then
it drafts the alternative text it has just told you is missing.

## How it fits in the ecosystem

```
sprezzature suite
├── sprezzature-accessibility  ← this package (20 static rules, 6 with a fixer)
├── sprezzature-colors         (contrast, colour-vision deficiency simulation)
├── sprezzature-ux-laws        (30 laws of UX, 8 decidable from source)
├── sprezzature-ui             (the screens this one audits afterwards)
├── sprezzature-figures        (167 chart types, written as SVG directly)
├── sprezzature-maps           (the same numbers attached to real places)
├── sprezzature-cli-gui        (a web form over a command-line tool)
├── sprezzature-publish        (Markdown to a findable site, narration included)
├── sprezzature-audio          (speech to text, text to speech)
└── sprezzature-video          (what a film about a project claims, checked)
```

What comes before: `sprezzature-ui` writes the markup, `sprezzature-publish`
turns documents into pages, `sprezzature-figures` writes the SVG embedded in
them. What comes after: a browser-driven engine, axe-core or Pa11y or
Lighthouse, for everything a rendered page reveals and a source file cannot.
The sister brick doing the neighbouring job is `sprezzature-colors`: contrast
is an accessibility question this package deliberately does not answer, because
a contrast ratio is computed on the colour a pixel ends up, which is a
rendering result. `sprezzature-audio` owns the other half of the media story:
this package checks that a caption track is declared, that one checks whether
the captions are readable.

## When to choose it

- **A pre-commit hook on a repository of HTML templates.** The lint is standard
  library only and reads a typical 16 KiB page in 2.3 ms on an Apple M-series
  laptop. Nothing to spin up, no Chromium to download, no container image to
  grow.
- **A continuous integration (CI) gate in a minimal Python image.** Exit code 1
  on any finding, 0 on clean, JSON for whatever has to parse the result. No Node
  toolchain is required, which matters in a repository that does not otherwise
  have one.
- **A page with video or audio on it.** Five of the twenty rules are WCAG 1.2
  and its neighbours: a caption track present, a transcript or accessible name
  on `<audio>`, `srclang` on every `<track>`, controls a keyboard can operate,
  and unmuted `autoplay`. This is the part of the standard the rest of the field
  treats as manual. axe-core deprecated its `audio-caption` rule and Lighthouse
  never shipped one.
- **An image with no alt, on a page that says what the image is for.**
  `--fix-alt` drafts the attribute with a local vision model, reading the image
  and the four hundred characters on each side of that `<img>` in that very
  document, plus the proper nouns mined from it. Nothing leaves the machine.
- **A procurement conversation where source code may not leave the building.**
  The Deque linter's editor extension calls a hosted server. This one calls
  nothing, and the model behind `--fix-alt` runs on your own hardware.

## When to pick something else

- **axe-core**, when you want the engine the industry has already agreed on.
  Ninety-four active rules against this package's twenty, a documented
  zero-false-positive design, an `incomplete` bucket for everything it cannot
  settle, and adapters for Playwright, Cypress, Jest, WebdriverIO and Puppeteer.
  It is also the only one here with an official Model Context Protocol (MCP)
  server, shipped in 2026. If you run exactly one accessibility tool, run that
  one.
- **Pa11y**, when you want a single command that gates a list of URLs in CI and
  you do not mind the three hundred megabytes of Chrome that arrive with it.
  `pa11y-ci` merges two engines, axe-core and a maintained fork of
  HTML_CodeSniffer, and its `--threshold` and `--standard WCAG2AA` flags are
  better CI ergonomics than anything in this package.
- **Microsoft Accessibility Insights**, when the question is keyboard order. Its
  Tab Stops view draws the focus path over the live page, and no static read of
  source can produce that picture. It is free, and it is the strongest thing in
  the free tier for the one failure mode a linter is structurally blind to.
- **axe DevTools Linter (Deque)**, when the markup is JSX, Vue single-file
  components, Angular templates, Liquid or HTL rather than `.html`. Forty-four
  rules, editor and CI integrations, a REST API, and a company behind it. This
  package reads HTML with Python's `html.parser` and will not be learning
  JavaScript syntax.
- **Biome**, when the repository is already JavaScript or TypeScript. Version
  2.4 added fifteen HTML accessibility rules in Rust, `useMediaCaption` among
  them, and it is faster than anything else in this table.
- **AltText.ai or Azure AI Vision**, when ten thousand product photographs in a
  content management system need alt text this week. One laptop running one
  model is the wrong shape of machine for that job.
- **Siteimprove, Level Access or QualiBooth**, when what is actually needed is a
  signed report, a dashboard a compliance officer reads, and somebody to call.
  None of that is what a linter is.

## Ideas worth stealing

Twenty-two competing tools were read for this document. Studying a competitor and bringing
nothing back is wasted work, so here is what is worth taking, best return first.
Two entries are refusals, with the reason, which is a valid entry.

**[IBM Equal Access](https://github.com/IBMa/equal-access/blob/main-4.x/accessibility-checker/README.md):
what prints and what fails are two different questions.** Its CI assertion
splits `reportLevels` (what appears in the output) from `failLevels` (what makes
the assertion fail), and adds a baseline file so an existing page can be adopted
without the gate going red on day one. Here the severity table already exists:
`_SEVERITY` in `sprezzature_accessibility/api.py` marks five of the twenty rules
as warnings, and the command line cannot see it. `lint_a11y.py` exits 1 on any
finding, so a `color-only-state` warning fails a build exactly as hard as an
`<img>` with no alt at all. The work is to move `_SEVERITY` next to
`ALL_RULES`, give `Finding` a `severity` field, and add `--fail-on error`. Cost:
an afternoon. It is first because the package already has this idea and wired
only half of it.

**[axe-core](https://github.com/dequelabs/axe-core): a third outcome between
pass and fail.** Every tested element lands in one of four buckets, `violation`,
`pass`, `incomplete` or `inapplicable`, and anything the engine cannot settle
goes to `incomplete` rather than into violations; five rules carry
`reviewOnFail: true` so a failed check is routed there by design. That is how
axe keeps its zero-false-positive reputation without dropping the finding. Here,
`check_dialog_close` in `lint_a11y.py` recognises a close button by matching
five hardcoded words across English, French and German, and
`references/lint-rules.md` already admits in writing that any other language
will false-positive. That rule, and `color-only-state`, belong in a `review`
bucket, reported separately and out of the exit code by default. Cost: half a
day on top of the entry above, and it has to be the same afternoon, because a
severity level invented twice is a severity level that drifts.

**[AltText.ai](https://alttext.ai/docs/webui/adding-images/): a house style
applied to every draft.** Its "Final Pass" is an instruction the customer writes
once, up to 768 characters, appended to every alt text the service generates,
which is how a shop makes every description say "men's running shoe" rather than
"a shoe". Here `--fix-alt` has no way to carry a house rule at all: a
documentation site that wants "name the command, not the screenshot", or a
newsroom that wants surnames in capitals, has to edit
`scripts/prompts/alt_short_informative.yaml` and lose the edit on the next
upgrade. The prompts are already YAML with substituted runtime fields, so an
`--alt-style FILE` flag landing in the same `{ctx}` slot `surrounding_text` uses
is half a day. What AltText.ai gets wrong is worth saying in the same breath:
that hand-written instruction is its *only* context channel, because its
documentation shows the surrounding body text of the page is never sent to the
model.

**[Pa11y](https://github.com/pa11y/pa11y): gate by conformance level, not by
rule name.** Pa11y takes `--standard WCAG2A`, `WCAG2AA` or `WCAG2AAA`, so a team
gates on level A without naming a single rule. Here `--ignore` accepts rule ids
only, which means a team wanting level A alone has to list every AA rule by hand
and maintain that list as rules are added. The mapping exists already, as prose,
in the two tables of `references/lint-rules.md`; it wants to be a `wcag` field
on each `ALL_RULES` entry so that `--level A` becomes a one-line selector. Cost:
an afternoon for the mapping, and it pays twice, because the SARIF entry above
needs the same field for its `helpUri`. Pa11y's `--threshold` is the half to
refuse: a budget of tolerated findings is a budget that only ever grows.

**[axe-sarif-converter](https://github.com/microsoft/axe-sarif-converter): SARIF
as a third output format.** Microsoft ships a converter precisely because axe
does not emit SARIF (Static Analysis Results Interchange Format, the JSON schema
GitHub code scanning reads), and SARIF is what turns findings into inline
annotations on a pull request instead of lines in a log nobody opens. Here:
`--format sarif` beside `text` and `json` in `lint_a11y.py`, written with
`json.dump` and no new dependency. The fields are already lying around, the
`ruleId` is `Finding.rule`, the message is `Finding.message`, the `helpUri` is
the anchor in `references/lint-rules.md`. Cost: a day, most of it reading the
schema rather than writing code.

**[html-validate](https://html-validate.org/wcag.html): publish what the tool
does not check.** It keeps a page listing WCAG 2.2 criterion by criterion with
its coverage marked, including the criteria it does not touch at all, and that
page does more for its credibility than any rule count. Here
`references/lint-rules.md` already says this per rule, which is the easy
direction. The missing half is the inverse view: the success criteria with no
rule at all, where a reader learns that contrast is ceded to
`sprezzature-colors` on purpose, that focus order needs axe-core, and that
WCAG 1.4.12 is covered here by a static proxy rather than by a conformance test.
Cost: a day of writing, no code, and it is the cheapest honesty on this list.

**[axe DevTools Linter](https://docs.deque.com/linter/4.0.0/en/linter-home/):
the file types, and why this one will not follow. Refused.** The Deque linter
reads JSX, TSX, Vue single-file components, Angular templates, Liquid, HTL and
Markdown, not only `.html`, which is where most teams' markup actually lives.
The refusal is worth stating rather than leaving implicit: the parser here is
`html.parser` from the standard library, and teaching it JSX means shipping a
JavaScript parser, which is the one dependency that would end the stdlib-only
claim this package is built on. The honest answer stays the one the README
already gives: a template that compiles to HTML gets linted after it compiles.

**accessiBe and UserWay: the repair that repairs nothing. Refused.** An overlay
patches the live DOM (Document Object Model, the tree a browser builds while
displaying a page) in the visitor's browser, which leaves the defect in the
source and ships it again on the next deploy. The United States Federal Trade
Commission accepted a consent order against accessiBe in January 2025, final in
April, with a one million dollar payment, barring the company from claiming an
automated product can make a site WCAG-compliant without competent and reliable
evidence; a class action against UserWay was filed in July 2024 by a customer
who bought the overlay and was sued anyway. Here the refusal is already written
into the design, in `fill_alt.py`'s own docstring, and the sentence worth
lifting out of it is that `--fix-alt` writes a draft into the file where a
person reviews it, rather than a patch into the page where nobody does. Cost:
nothing, which is why it belongs in a list about return.

## How the field divides

**Static against runtime.** A static tool reads the HTML source text, the way
you would with your eyes, and never opens a browser. A runtime tool drives a
real browser, lets it render the page into a DOM, and inspects that live tree.
The split is not about quality, it is about what each can prove. Only the
runtime tool can measure text against the background it ends up on, or walk the
focus order a keyboard will actually follow. Only the static tool can name the
file and the line, run before the page exists, and finish in milliseconds. The
runtime family is much the larger of the two: axe-core, Pa11y, Lighthouse, WAVE,
IBM Equal Access and Accessibility Insights all live there, and four of those
six are axe-core wearing different clothes. The static family is thin, and one
commercial player owns most of it.

**Detect against generate.** Almost everything in this table reports and stops.
A second, newer family does the opposite: it writes the content the page is
missing, which in practice means alt text. AltText.ai, AutoAlt.ai, Azure AI
Vision and the open-weight models you can run yourself all sit there. The two
families barely overlap, and that gap is what this package aims at. The linter
that found the missing alt is the thing best placed to write it, because it is
already holding the document the image sits in, and what an image is *doing* on
a page is a question about the page rather than about the pixels. The W3C's own
[alt decision tree](https://www.w3.org/WAI/tutorials/images/decision-tree/)
sorts images by purpose, informative, decorative, functional, text, complex,
group, and purpose is only legible in context; WebAIM's alt-text guidance has a
section headed "Context is Everything" and gives the same photograph four
different correct alt texts on four different pages.

That is a standards argument, and there is a measured one beside it. Nikita
SRIVATSAN, Sofia SAMANIEGO, Omar FLOREZ and Taylor BERG-KIRKPATRICK, at ICLR
2024, trained on 371,000 images paired with their alt text and the post around
them: a model conditioned on both the image and the surrounding text beat
image-only work by more than double on BLEU@4. Ananya GUBBI MOHANBABU and Amy
PAVEL, at ASSETS 2024, put context-aware descriptions in front of twelve blind
and low-vision participants, who rated them significantly higher on quality,
relevance, imaginability and plausibility; their abstract says flatly that
existing tools describe images without considering the surrounding webpage
context. The hosted vendors still do not. AltText.ai's own documentation shows
its context channels are a keyword box, a product-name field, and a custom
instruction the customer types once; the body text of the page is never sent.
Azure's captioning endpoint takes an image and nothing else.

That is also where a local model stops being a compromise and becomes the
requirement. `qwen3-vl:8b` is a six-gigabyte download with a 256,000-token
context window, so the paragraph around the image, the heading above it and the
project's own vocabulary all fit in one prompt, at no cost per image and with
nothing leaving the machine. An interface billed per image has no reason to
want a page of extra tokens on every call.

**Library against product, and the overlay question.** A third split cuts across
both: whether you install a library or buy an outcome. Siteimprove, Level Access
and QualiBooth sell monitoring, dashboards and somebody to call, at four and
five figures a year. The overlays, accessiBe and UserWay, sell the promise that
one script tag fixes the site, and that promise is now legally expensive. They
are in the table because they are in the market, and because a comparison that
quietly omits the biggest-selling category of its own field is not a comparison.
They score badly on signal precision and on repair for reasons other people have
already written down: the Overlay Fact Sheet, maintained by Karl GROVES and
carrying over a thousand signatories, among them editors of the WCAG, ARIA and
HTML specifications and contributors to NVDA and JAWS, states in one line that
automated application of text alternatives for images is not reliable. UsableNet
reported in 2026 that roughly one sued company in five already had an
accessibility widget installed.

**The ceiling nobody gets past.** Deque's own study across roughly thirteen
thousand audited pages puts automated detection at about 57 % of issues by
volume, and at 20 % to 30 % when counted as a share of WCAG success criteria
rather than of issues. An independent run of axe-core against the W3C's
Accessibility Conformance Testing answer key caught 37.5 % of the failing
examples. Those two numbers get conflated constantly in vendor material, and
neither is a ceiling any tool in this table argues its way past. The 2026 edition
of the WebAIM Million found detected WCAG failures on 95.9 % of the top million
home pages, missing image alt text on 53.1 % of them, and 16.2 % of all images
sampled with no alt attribute at all. The field is not short of tools. It is
short of pages that ran one.

## How it compares

Every tool is rated 1 to 5 on each criterion, higher is better (⭐ weak to
⭐⭐⭐⭐⭐ strongest). The scores are an argued judgement, not a benchmark, and
every column is oriented so that more stars mean stronger on that trait: for
cost, more stars mean freer or more open; for install weight, more stars mean
lighter. A tool that does not do what a column measures scores ⭐, because on a
capability scale "does not do this" is a 1. The machine-readable source is
[`assets/landscape.csv`](assets/landscape.csv), generated from the table below:
23 tools across 15 criteria.

| Tool | Runs without a browser | Speed in continuous integration | Fit for a pre-commit hook | Install lightness | Points at the source line | Mechanical auto-fix | Drafts the missing alt text | WCAG rule coverage | Time-based media coverage | Catches rendered-page defects | Signal precision | Free or open source | Local and offline | Maturity and ecosystem | Commercial support |
| --- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| sprezzature-accessibility | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐ |
| axe-core | ⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| axe DevTools Linter | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Pa11y | ⭐ | ⭐⭐ | ⭐ | ⭐ | ⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ |
| Lighthouse | ⭐ | ⭐⭐ | ⭐ | ⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ |
| WAVE | ⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| IBM Equal Access | ⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| Accessibility Insights | ⭐ | ⭐⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| HTML_CodeSniffer | ⭐ | ⭐⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐ |
| eslint-plugin-jsx-a11y | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐ |
| Biome | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| html-validate | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| htmlhint | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ |
| AccessLint | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐⭐ |
| A11yInspect | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| Siteimprove | ⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| QualiBooth | ⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| accessiBe | ⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| UserWay | ⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| AltText.ai | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| AutoAlt.ai | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐⭐ |
| Azure AI Vision | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Qwen3-VL via Ollama | ⭐⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐ |

![sprezzature-accessibility against 22 other accessibility and alt-text tools, positioned on two axes derived from principal component analysis. This package sits top right, in a cluster with Biome, htmlhint, eslint-plugin-jsx-a11y, html-validate and the axe DevTools Linter: the tools that read source text, name a line and never open a browser. Opposite it, to the left, sit the engines that render the page first, axe-core, Pa11y, Lighthouse, IBM Equal Access and Siteimprove, which see much more and cost much more to run. Below and to the right sit the alt-text services and the overlays, AltText.ai, AutoAlt.ai, Azure AI Vision, accessiBe and UserWay, light to adopt and sold rather than installed. The horizontal axis opposes the breadth of an engine that renders to the lightness of a tool that only reads; the vertical axis opposes open, local, line-level tooling at the top to bought outcomes at the bottom.](assets/landscape.svg)

The source is [`assets/landscape.csv`](assets/landscape.csv), the star table
above and nothing added, and the map is regenerated with:

```sh
python ../sprezzature/scripts/landscape_to_csv.py LANDSCAPE.md
standpoint assets/landscape.csv --outdir assets --stem landscape --check
```

`standpoint` puts the first row of the table top right and orients everything
else around it. That is a convention of the drawing, not a claim about quality:
this file belongs to this package, so this package is the reference point, and
the rotation applied to get it there was +43.1°. The geometry underneath is
ordinary correlation principal component analysis (PCA) and is deterministic,
so the same table gives the same map every run, whatever model named the poles.
The four words at the edges come from a local language model; the loadings
below are the control, and they are the part to trust.

**Horizontal, 33.8 % of the variance, "Thoroughness" on the left against
"Efficiency" on the right.** Catches rendered-page defects (−0.41), WCAG rule
coverage (−0.35) and maturity and ecosystem (−0.26) pull left; runs without a
browser (+0.38), mechanical auto-fix (+0.32), install lightness (+0.31) and
drafts the missing alt text (+0.31) pull right. This is the trade the whole
document is about, and the map found it without being told: an engine that
renders the page sees more, is trusted more, and has been around longer, and it
costs a browser to run. `sprezzature-accessibility` is at the far right by
construction, as the reference row, but AltText.ai is marked the strongest
option toward that pole, which is the map saying the right-hand side is a
category and not a prize.

**Vertical, 26.6 % of the variance, "Stability" at the bottom against "Agility"
at the top.** Free or open source (+0.40), local and offline (+0.39), speed in
continuous integration (+0.39), fit for a pre-commit hook (+0.36) and points at
the source line (+0.36) load together at the top; commercial support (−0.30)
and drafts the missing alt text (−0.21) at the bottom. The top pole is one
coherent thing, a tool you install and run yourself over your own files, and
the bottom is its opposite, an outcome you buy. Biome is the strongest option
toward the top, Siteimprove the weakest overall, and accessiBe, UserWay and the
alt-text services sit low beside it.

**Two axes carry 60.4 % of the table.** Four tenths of what these fifteen
criteria say is not on this page. Time-based media coverage loads at −0.12 and
+0.20, which is close to nothing on either axis: it is the column where this
package is most unusual, and a direction only two or three rows move along is
not one of the first two directions. The same is true in reverse of signal
precision, where this package is weakest among the static tools. The map is a
first orientation; the table is the evidence.

`--check` confirms the reference is top right and the axis labels are legible,
and reports the figure as not fully readable: four pairs of point labels risk
overlapping, axe-core with Pa11y and with Lighthouse, the axe DevTools Linter
with AccessLint, and Biome with htmlhint. Those pairs genuinely score alike, so
the overlap is the table being honest rather than the drawing being wrong, and
nothing was nudged to separate them. `standpoint` also writes a prose
interpretation beside the figure; it is not reproduced here, because a model
reading back ratings somebody wrote is not a finding.

## Sources

- [axe-core rule descriptions](https://github.com/dequelabs/axe-core/blob/develop/doc/rule-descriptions.md), the authoritative list by WCAG level, including the deprecated `audio-caption`
- [axe DevTools Linter documentation](https://docs.deque.com/linter/4.0.0/en/linter-home/), file types, integrations, and the statement that it analyses source rather than a running application
- [Pa11y](https://github.com/pa11y/pa11y) and [pa11y-ci](https://github.com/pa11y/pa11y-ci), runners, standards and thresholds
- [IBM Equal Access accessibility-checker](https://github.com/IBMa/equal-access/blob/main-4.x/accessibility-checker/README.md), `reportLevels`, `failLevels` and baseline files
- [Accessibility Insights FastPass](https://accessibilityinsights.io/docs/web/getstarted/fastpass/), and the Tab Stops view
- [The WCAG 2.2 support table of html-validate](https://html-validate.org/wcag.html)
- [eslint-plugin-jsx-a11y](https://github.com/jsx-eslint/eslint-plugin-jsx-a11y) and [the HTMLHint rule list](https://htmlhint.com/rules/)
- [The WebAIM Million](https://webaim.org/projects/million/), the annual accessibility survey of the top one million home pages, and [WebAIM on alternative text](https://webaim.org/techniques/alttext/), whose "Context is Everything" section is the plain-language version of the argument above
- [The W3C alt decision tree](https://www.w3.org/WAI/tutorials/images/decision-tree/), the taxonomy `--fix-alt` implements
- SRIVATSAN, SAMANIEGO, FLOREZ and BERG-KIRKPATRICK, [*Alt-Text with Context*](https://arxiv.org/abs/2305.14779), ICLR 2024, and GUBBI MOHANBABU and PAVEL, [*Context-Aware Image Descriptions for Web Accessibility*](https://dl.acm.org/doi/10.1145/3663548.3675658), ASSETS 2024
- [AltText.ai's documentation on adding images](https://alttext.ai/docs/webui/adding-images/), which is where its context channels are listed
- [The Overlay Fact Sheet](https://overlayfactsheet.com/en/), maintained by Karl GROVES
- [ACT Rules Format 1.1](https://www.w3.org/WAI/news/2026-02-05/act-rules-11), a W3C Recommendation since February 2026
- [The FTC order against accessiBe](https://www.ftc.gov/news-events/news/press-releases/2025/01/ftc-takes-action-against-accessibe-deceiving-consumers-about-its-ai-product-web-accessibility)
