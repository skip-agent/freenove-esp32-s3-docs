# Site content model and navigation

Resolved for: [Specify the site content model and navigation](https://github.com/skip-agent/freenove-esp32-s3-docs/issues/6)
Map: [Wayfinder Map: TinySkiff ESP32-S3 guided 30-day tutorial spec](https://github.com/skip-agent/freenove-esp32-s3-docs/issues/1)

Builds on: [lesson voice + day template](lesson-template.md) (#3), [30-day curriculum spine](curriculum-spine.md) (#4), and the approved [Day 26 guided-day prototype](guided-day-prototype-day-26-ultrasonic.md) (#5), now generated at [`/course/day-26-ultrasonic/`](../course/day-26-ultrasonic/index.html).

---

## Executive answer

Ship **one site with two surfaces that share a spine**:

1. **The Course** — the guided 30-day path. New. Each day is one lesson page in the approved echo-sounder design system.
2. **The Library** — the existing launchpad (`build_site.py` → `docs/index.html`). Kept almost as-is as the searchable reference for every sketch, library, and datasheet.

The key move: **each day is a single structured lesson file that is the one source of truth.** The build step renders that one file into three outputs — the HTML lesson page, the agent JSON packet, and the day's entry in the course map. Authoring a day means writing one file; the page, the coaching packet, and navigation stay in lock-step automatically.

Everything stays a **static site** built by an extended `build_site.py` and served on Cloudflare Pages. No framework change, no backend, no accounts. Progress lives in the browser.

---

## 1. Site structure

```
docs/                            ← published root (Cloudflare Pages)
  index.html                     ← Library launchpad (existing, preserved)
  styles.css  app.js  data.json  ← Library assets (existing)
  assets/                        ← shared kit images (existing)
  course/                        ← NEW: the guided course
    index.html                   ← course map — "the voyage", 30 days
    course.css  course.js        ← shared course/lesson styling + behaviour
                                   (productised from prototype-preview.{css,js})
    assets/
      shared/                    ← reused item photos (board, jumpers, IDE…)
      day-03/ … day-30/          ← per-day diagrams extracted from the PDFs
    day-03-blink/index.html      ← one folder per day → clean URL /course/day-03-blink/
    …
    day-26-ultrasonic/index.html
    packets/
      TSK-DAY03-BLINK.json       ← agent packet, emitted from the same source
      …

lessons/                         ← NEW: authored source of truth (not published)
  day-03-blink.yml
  …
  day-26-ultrasonic.yml
  _glossary.yml                  ← shared explainer definitions, keyed by topic
```

**URLs**

| Path | Page |
|---|---|
| `/` | Landing → course-forward, Library one click away (see §7 decision) |
| `/course/` | Course map: 30 days as a voyage chart, with progress |
| `/course/day-26-ultrasonic/` | A single guided day |
| `/index.html` (Library) | Searchable reference browser (unchanged) |
| `/course/packets/TSK-DAY26-ULTRASONIC.json` | Machine-readable lesson packet |

Per-day **folders with `index.html`** give clean, shareable, stable URLs (`/course/day-26-ultrasonic/`) with no server rewrites — important on Pages.

---

## 2. Lesson data model — `tinyskiff.lesson.v1`

One file per day under `lessons/`. It is a **superset of the existing `tinyskiff.lessonPacket.v0`** already shipped with the prototype, so the packet becomes a projection of the lesson, not a second thing to maintain.

The page has fixed slots (hero, parts, wiring, pins, steps, code focus, theory, test, challenge + logbook, agent). Content-carrying sections are **objects with an `intro` plus their items** (so each section can hold its own lead prose), not bare lists. Free prose lives inside fields as short Markdown strings supporting `` `code` ``, `**bold**`, `*em*`, and inline `{glossary-key}` explainer chips. Recommended authoring format: **YAML** (readable, comments allowed, diff-friendly); the build parses it to the packet JSON.

The **canonical, complete example is [`lessons/day-26-ultrasonic.yml`](../../lessons/day-26-ultrasonic.yml)** — copy it when authoring a new day. The shape below is abbreviated to the field names the validator enforces (see `scripts/lesson_schema.py`):

```yaml
schema: tinyskiff.lesson.v1
lessonCode: TSK-DAY26-ULTRASONIC        # stable agent-assist code; DAYNN must match `day`
day: 26
slug: day-26-ultrasonic                 # must match the day's slug in _course.yml
title: Measure the room with sound
status: draft | review | published      # only `published` days render + link
estimatedTimeMinutes: 30                # template rule: ≤ 30
tracks: { main: arduino, optional: micropython }   # main must be arduino
learnerProfile: adult beginner; no electronics assumed
mission: >                              # the goal slot (also the packet mission)
  Build a tiny depth sounder with the HC-SR04…
unlocks: The board can measure the world by timing a signal out and back.

hero:                                    # → the instrument hero
  instrument: sounder
  instrumentTitle: Live echo sounder
  readout: { label: Distance, value: "24.31", unit: cm }
  headline: Measure the room|with {sound}    # '|' = line break, '{x}' = emphasis
  lede: Today you build a tiny depth sounder…
  pills: [ { text: About 30 minutes, key: true }, Arduino first ]

parts:                                                    # → parts grid
  intro: Six things, nothing more…
  items:
    - name: HC-SR04 sensor
      image: shared/item-hcsr04.jpg      # relative to course-assets/assets/
      imageKind: Manual photo
      alt: Official manual image of the HC-SR04…   # required (provenance)
      blurb: The distance sensor with two round transducers.
      explain: hcsr04                    # → glossary key

wiring:
  intro: The official Freenove diagram is your chart…
  diagram:
    image: day-26/circuit-page-172.png
    alt: Official Freenove diagram showing VCC→5V, Trig→GPIO13…   # required
    caption: Official Freenove circuit — C Tutorial, Chapter 19, page 172.
    source: { pdf: C_Tutorial.pdf, chapter: 19, chapterTitle: Ultrasonic Ranging, page: 172 }
  pins:                                                   # → interactive pin table
    - { from: VCC, to: 5V, why: Powers the sensor., explain: vcc }
  safety:                                                 # inline callouts, only when real
    - { label: Check before power., body: Keep pins in module order; unplug USB first. }

steps:                                                    # → checkable build steps
  intro: This is the main path…
  items:
    - Connect `VCC → 5V`, `Trig → GPIO 13`, `Echo → GPIO 14`, `GND → GND`.
    - Open Serial Monitor at `115200` baud. {serial}     # inline explainer chip
  done: { title: Sounder's live., body: …, icon: "🌊" }

code:                                                     # → code panel + annotations
  intro: You don't need the whole sketch today…
  arduino:
    file: Sketch_19.1_Ultrasonic_Ranging.ino             # display label
    sketch: C/Sketches/Sketch_19.1_Ultrasonic_Ranging/…  # full source path (Library link)
    variant: C/Sketches/Sketch_19.2_…                    # optional; → packet
    excerpt: |
      #define trigPin 13
      pingTime = pulseIn(echoPin, HIGH, timeOut);
    notes:
      - { code: "pulseIn(...)", text: Times how long Echo stays HIGH., explain: pulsein }
  micropython:                                            # optional block; omit to hide the tab
    file: 18.1_Ultrasonic_Ranging/Ultrasonic_Ranging.py
    path: Python/Python_Codes/18.1_Ultrasonic_Ranging/…  # full source path
    excerpt: "trigPin = Pin(13, Pin.OUT, 0)"
    notes: [ { code: "Pin(13, Pin.OUT, 0)", text: Trigger output. } ]
    note: Same pins, same behaviour…                     # closing note

theory:                                                   # optional; complete if present
  title: Physics of a ping
  summary: Send a ping, wait for the echo…                # → packet plainLanguage
  intro: The whole day is one loop…
  flow: [ { n: Send a ping, title: Trig fires, body: … } ]
  formula: distance = **speed of sound** × **echo time** ÷ 2   # **term** → accent
  notes: [ { title: Why readings wobble, body: …, explain: wobble } ]

test:
  intro: Success and recovery sit side by side…
  baud: 115200
  expected: [ "Distance: 24.31cm", "Distance: 23.92cm" ]
  expectedNote: A good reading changes when you move the object.
  checks:
    - { symptom: "0 cm or frozen?", fix: "Check Trig, Echo, GND, and the target's shape." }

challenge:
  title: "Try this: a mini range log"
  railLabel: Try this
  intro: Same working setup, one new skill…
  summary: Measure three targets; choose a keep-out threshold and say why.   # → packet
  cards: [ { title: Measure three targets, body: … } ]
  logbook: [ What did you measure?, Which reading was most stable? ]

agent:
  intro: Every lesson ships with a code and a machine-readable packet…
  behaviour: guide one physical step at a time…          # page callout prose
  coachInstructions: [ Guide one physical step at a time…, … ]   # → packet list

source:                                                   # attribution, always preserved
  license: CC BY-NC-SA 3.0
  licenseNote: Based on Freenove official material…; preserve attribution.
```

**Glossary (`lessons/_glossary.yml`)** holds every explainer once, keyed by topic (`hcsr04`, `trig`, `pulsein`…), each with `title` / `body` / `shortcut`. Lessons reference a key; the build inlines the definition into both the page's lightbox data and the agent packet. Shared terms are written once and reused across all 30 days.

---

## 3. Images

- **Two asset classes.** Reusable *kit item* photos (board, jumper, IDE) live in `course/assets/shared/` and are referenced by many days. *Per-day diagrams* (wiring, official circuit) live in `course/assets/day-NN/`.
- **Provenance travels with the image.** Every diagram field carries `source` (PDF, chapter, page) and required `alt`. The build renders attribution near the asset and keeps the source in the packet — satisfying the CC BY-NC-SA obligation the map calls out.
- **Extraction is a one-time content task per day**, not a runtime concern: crop the official diagram from the PDF into a clean lesson asset (the prototype already did this for Day 26). The `source-manifest/` records where each came from.
- Official item images the launchpad already copies (`Super.jpg`, `ESP32S3_Pinout.png`, Arduino config shots) are reused rather than duplicated.

---

## 4. Code snippets

- The lesson stores a **code *focus*** — a handful of annotated lines — never the full sketch. The full official sketch stays in the Library and on GitHub; the lesson links to it.
- Annotations are structured (`code` + `text` + optional `explain` key) so they render as the side-by-side notes in the prototype and feed the agent packet.
- **Arduino is the main path; MicroPython is an optional tab.** Omitting the `micropython` block simply hides the tab for days that have no Python equivalent — no empty tabs.
- Syntax highlighting stays build-time/static (lightweight token spans as in the prototype), no client highlighter dependency.

---

## 5. Progress and day navigation

- **Course map (`/course/`)** shows all 30 days as a voyage chart grouped by arc (e.g. *First light* d1–5, *Reading the world* d13–21, *Talking to the internet* d27–30 — from the spine). Each day tile shows number, mission, time, and completion state.
- **Within a day**: the "Day N of 30" voyage rail (section scroll-spy, as built), plus **prev / next day** links so the course reads as a sequence.
- **Progress is client-side (`localStorage`), no accounts.** Two levels, both already prototyped: per-step checkmarks within a day, and whole-day completion. The map reads the same store to show ticks and a **"resume — Day N"** affordance.
- Progress is a convenience layer, never a gate: any day is directly reachable by URL.

---

## 6. Search and the Library

- **The Library launchpad is preserved wholesale.** It stays the fast, searchable browser over every sketch, library, and datasheet — exactly what `build_site.py`/`app.js`/`data.json` already do. No regression to that surface.
- **Two-way cross-links** stitch the surfaces together:
  - Each guided day links to its official source sketch in the Library and to the official Freenove docs.
  - Library sketch entries that a day is built on get a **"Taught in Day N →"** backlink (derived automatically from the lessons' `codeFocus.sketch` paths at build time).
- **Course search is optional and lightweight**: extend the existing client search to also index published lessons (title, mission, day). Recommended as a fast-follow, not a blocker.

---

## 7. Build pipeline

Extend the existing script rather than adopt a framework:

- Add `collect_lessons()` — parse every `lessons/*.yml`, resolve glossary keys, validate against `tinyskiff.lesson.v1` (required fields, `estimatedTimeMinutes ≤ 30`, alt text present, attribution present).
- Add `render_lesson(lesson)` → `docs/course/day-NN-slug/index.html` using the productised prototype template.
- Add `render_course_index(lessons)` → `docs/course/index.html` (the voyage map).
- Add `emit_packet(lesson)` → `docs/course/packets/<CODE>.json` (the `v0` packet shape, projected from the lesson).
- Promote the prototype's `prototype-preview.{css,js}` into `course/course.{css,js}` as the shared, tokenised design system.
- `validate_site.py` gains lesson-schema checks so a malformed or over-length day fails the build.

Result: `python scripts/build_site.py` produces the whole static site — Library and Course — deployable to Pages as today.

---

## 8. Decisions — confirmed

Skipper confirmed all four (2026-07-08).

1. **Lesson source format → YAML structured files.** The page is slot-based and the same data must feed the agent packet, so structured YAML beats prose-in-Markdown-body (which would need re-parsing into slots).
2. **Landing page → course-forward.** `/` leads with "Start the 30-day course" and keeps the Library one click away. Interim: stay library-first until the first real day exists, then flip.
3. **Progress storage → `localStorage`, no accounts.** Matches the light-infra stance. Accounts/sync are a possible later course, out of this map.
4. **Generator → keep and extend Python `build_site.py`.** Output is static HTML and the prototype is vanilla HTML/CSS/JS, so a static generator would add tooling for no gain. Revisit only if authoring grows past hand-written YAML.

---

## What this unblocks

- [Assemble the ready-to-implement tutorial spec](https://github.com/skip-agent/freenove-esp32-s3-docs/issues/7) can now fold in this content model and navigation, plus the per-day image map, into one implementation-ready backlog with acceptance criteria per day.
- Implementation itself (rendering all 30 days, wiring the build, deploying) remains out of scope for this Wayfinder map, by design.
