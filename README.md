# TinySkiff ESP32-S3 Lab

A cleaner front door to the **Freenove Super Starter Kit for ESP32-S3**, served
as one static site with two surfaces:

- **The Library** (`/`) — a fast, searchable launchpad over every official
  sketch, library, and datasheet.
- **The Course** (`/course/`) — a guided 30-day, Arduino-first tutorial. Each day
  is one complete win in about 30 minutes, in the "echo sounder" design system.

The site is static HTML/CSS/JS built by a Python script and deployed to
Cloudflare Pages. No backend, no accounts; progress lives in the browser.

## How a lesson works

Each day is **one source-of-truth file** — `lessons/day-NN-slug.yml`
(`tinyskiff.lesson.v1`). The build projects it into three outputs that never
drift:

- the guided page → `docs/course/day-NN-slug/index.html`
- the agent packet → `docs/course/packets/<CODE>.json` (`tinyskiff.lessonPacket.v0`)
- the entry in the course map → `docs/course/index.html`

Shared explainers live once in `lessons/_glossary.yml`; the 30-day voyage spine
(arcs + day order) lives in `lessons/_course.yml`. The productised design system
and image assets live in `course-assets/` and are copied into `docs/course/`.

See `docs/wayfinder/site-content-model.md` §2 for the annotated data model,
`docs/wayfinder/implementation-spec.md` for the full spec, and
`docs/wayfinder/asset-workflow.md` for how images are extracted.

## Build

The build needs Python 3 and PyYAML. Homebrew Python is externally managed, so
use a virtualenv:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

.venv/bin/python scripts/build_site.py     # build Library + Course into docs/
.venv/bin/python scripts/validate_site.py  # fail on a malformed/over-length day
.venv/bin/python -m unittest discover -s scripts/tests   # unit tests
```

`build_site.py` regenerates only what it owns (the Library files, `docs/assets/`,
and `docs/course/`); the hand-written planning docs under `docs/wayfinder/` are
left in place. The kit source lives under the gitignored `source/` folder.

## Authoring a new day

1. Extract any diagrams (see `docs/wayfinder/asset-workflow.md`) into
   `course-assets/assets/day-NN/` and record them in `source-manifest/`.
2. Write `lessons/day-NN-slug.yml` (copy `lessons/day-26-ultrasonic.yml` as the
   reference). Set `status: draft` until it's ready; only `published` days render
   a page and link from the course map.
3. Add any new explainer terms to `lessons/_glossary.yml`.
4. Run the build + validator + tests. A missing `alt`, a missing `source`, an
   over-length day (> 30 min), an unresolved glossary key, or a duplicate
   day/code/slug fails the build with a clear message.
