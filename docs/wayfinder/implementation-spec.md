# ESP32-S3 Lab — ready-to-implement spec

Resolves: [Assemble the ready-to-implement tutorial spec](https://github.com/skip-agent/freenove-esp32-s3-docs/issues/7)
Map: [Wayfinder Map: ESP32-S3 guided 30-day tutorial spec](https://github.com/skip-agent/freenove-esp32-s3-docs/issues/1)

This is the capstone. It folds every resolved decision into one document an implementer can build from. It does not re-argue those decisions; it consolidates and makes them actionable.

**Inputs (all resolved):**
- [#2 Source inventory](https://github.com/skip-agent/freenove-esp32-s3-docs/issues/2) — official C/Arduino material is the backbone; MicroPython optional; PDF diagrams must be extracted.
- [#3 Lesson voice + day template](lesson-template.md) — friendly workshop guide; mission-card day.
- [#4 30-day curriculum spine](curriculum-spine.md) — the day-by-day plan.
- [#5 Guided-day prototype](guided-day-prototype-day-26-ultrasonic.md) — the approved "echo-sounder" design system (Day 26); now generated at [`/course/day-26-ultrasonic/`](../course/day-26-ultrasonic/index.html).
- [#6 Site content model + navigation](site-content-model.md) — two surfaces, one static site; `tinyskiff.lesson.v1`; four decisions confirmed.

---

## 1. Goals

- Turn the existing launchpad into a **guided 30-day, Arduino-first course** for an adult beginner with no electronics assumed, each day a ≤30-minute complete win.
- **One source of truth per day.** A single lesson file renders to the learner page, the agent-coaching packet, and the course-map entry.
- **Preserve the Library.** The current searchable launchpad stays intact as the reference surface.
- **Stay static and light.** Extended `build_site.py` → Cloudflare Pages. No backend, no accounts, progress in the browser.
- **Every lesson is agent-coachable** via its lesson code and machine-readable packet.
- **Attribution is structural**, not manual: Freenove source, PDF page, and alt text travel with each asset (CC BY-NC-SA).

## 2. Non-goals

- No new backend, database, auth, or user accounts.
- No framework migration (no Astro/Next/Svelte); vanilla static HTML/CSS/JS.
- Not writing all 30 days of production copy in this map — this spec defines the machine and the acceptance bar; authoring days is tracked work that follows.
- Camera, SD/audio, USB HID, deeper MicroPython/network tracks — deferred to a follow-up course.
- No commercial derivatives beyond the source's CC BY-NC-SA constraints.

## 3. Information architecture

One site, two surfaces sharing a spine (full detail in [site-content-model.md](site-content-model.md)):

| Surface | URL | Role |
|---|---|---|
| Landing | `/` | Course-forward entry; Library one click away |
| Course map | `/course/` | The "voyage" — 30 days grouped by arc, with progress |
| Guided day | `/course/day-NN-slug/` | One lesson in the echo-sounder design system |
| Library | `/index.html` | Existing searchable reference browser (preserved) |
| Packet | `/course/packets/<CODE>.json` | Machine-readable lesson packet |

Navigation model: course map → day (with prev/next + section scroll-spy rail) ↔ Library, with two-way cross-links ("Taught in Day N" ⇄ "Official sketch"). Progress (`localStorage`) drives day ticks and a "resume — Day N" affordance; never a gate.

## 4. Lesson / content format

- Author **one YAML file per day** under `lessons/day-NN-slug.yml`, plus a shared `lessons/_glossary.yml`.
- The file is structured (slot-based) because the page has fixed slots and the same data feeds the packet. Prose lives in fields as short Markdown strings.
- Explainers are referenced by glossary key; defined once, reused across all days; rendered into both the page's lightbox data and the packet.
- Arduino is the main path; a `micropython` block is optional — omitting it hides the tab.

## 5. Data model — `tinyskiff.lesson.v1`

Superset of the shipped `tinyskiff.lessonPacket.v0`. Full annotated schema in [site-content-model.md §2](site-content-model.md). Required fields and invariants the validator enforces:

- **Identity:** `schema`, `lessonCode` (unique, `TSK-DAYNN-…`), `day` (1–30, unique), `slug` (unique, matches folder), `title`, `status` ∈ {draft, review, published}.
- **Framing:** `mission` (the goal), `estimatedTimeMinutes` (**≤ 30**), `tracks.main = arduino`.
- **Body slots** (content sections are objects with an `intro` + items; as implemented — see [site-content-model.md §2](site-content-model.md) and `lessons/day-26-ultrasonic.yml`): `hero`, `parts.items[]` (each with `image`, `imageKind`, `alt`, `blurb`, optional `explain`), `wiring` (`diagram` with `image`+`alt`+`caption`+`source{pdf,chapter,page}`, `pins[]`, optional `safety[]`), `steps.items[]`, `code.arduino` (`sketch`, `excerpt`, `notes[]`), optional `code.micropython`, optional `theory` (`flow[]`, `formula`, `notes[]` — complete if present), `test` (`expected[]`, `checks[]`), `challenge` (`title`, `summary`, `logbook[]`), `agent` (`coachInstructions[]`).
- **Provenance:** every image carries `alt`; every diagram carries `source`; `source.license` present.
- **Glossary keys** referenced in any `explain:` field must exist in `_glossary.yml`.

Build projects the lesson to the `v0` packet shape for `/course/packets/<CODE>.json`, so the packet is never hand-maintained.

## 6. Asset plan

- **Two classes:** reusable kit-item photos in `docs/course/assets/shared/`; per-day diagrams in `docs/course/assets/day-NN/`.
- **Extraction is a per-day content task:** crop the official diagram from the source PDF into a clean lesson asset (done already for Day 26). Record origin in `source-manifest/`.
- **Provenance + alt required** on every asset (validator-enforced); attribution renders near the asset and persists into the packet.
- Reuse the assets the launchpad already copies (`Super.jpg`, `ESP32S3_Pinout.png`, Arduino config screenshots) rather than duplicating.
- Per-day image map (which official figures each day needs) is produced during authoring, seeded from the curriculum spine's "Official source basis" column.

## 7. Design system

The approved echo-sounder system from #5, productised:
- Promote `prototype-preview.{css,js}` → `docs/course/course.{css,js}` as the shared, tokenised system (palette, Fraunces + Inter + Spline Sans Mono type scale, components).
- Components the template renders: sonar/instrument hero, "Day N of 30" voyage rail with scroll-spy, parts grid, interactive pin table, checkable steps + progress + completion, Arduino/MicroPython code tabs, theory flow, instrument serial readout, challenge + logbook, agent panel, colophon.
- Explainers and image zoom use the accessible `<dialog>` lightbox pattern (focus handling, ESC/backdrop, focus return).
- Quality floor: responsive to mobile, visible keyboard focus, `prefers-reduced-motion` respected.

## 8. Build pipeline

Extend `scripts/build_site.py` (keep Python, per confirmed decision):

1. `collect_lessons()` — parse `lessons/*.yml`, resolve glossary keys, validate against `tinyskiff.lesson.v1`.
2. `render_lesson(lesson)` → `docs/course/day-NN-slug/index.html` via the productised template.
3. `render_course_index(lessons)` → `docs/course/index.html` (voyage map).
4. `emit_packet(lesson)` → `docs/course/packets/<CODE>.json`.
5. `derive_backlinks(lessons)` — map `code.arduino.sketch` paths to Library entries for "Taught in Day N".
6. Landing: render `/` course-forward once ≥1 day is published (interim: library-first).
7. `validate_site.py` gains lesson-schema + invariant checks (≤30 min, alt/source present, unique day/code/slug, glossary keys resolve) so a bad day fails the build.

`python scripts/build_site.py` continues to produce the entire static site — Library + Course — deployable to Pages exactly as today.

## 9. Acceptance criteria

**Per lesson** (from the #3 template; validator + review):
- Completable by an adult beginner in ≤30 minutes; starts with a concrete mission.
- Lists only that day's parts/software; action-first numbered steps.
- Uses official images with alt text and preserved attribution.
- Includes only *relevant* safety/troubleshooting; exactly one challenge; a logbook prompt.
- Explanations short and inline; MicroPython only as an optional side path.
- Renders cleanly to page **and** valid packet; all glossary keys resolve.

**Per build / system:**
- `build_site.py` emits Library + Course; `validate_site.py` passes; no console errors on any page.
- Lesson pages responsive to mobile; keyboard-navigable; lightbox focus behaviour correct; reduced-motion respected.
- Progress persists across reloads; every day reachable by direct URL.
- Library search and existing launchpad functions unchanged; cross-links resolve both directions.
- Attribution + non-affiliation present on every page using source material.

## 10. Build-ticket outline

Phased so a single real lesson proves the whole pipeline before authoring scales. Suggested as the child tickets of a future *implementation* map (out of scope to execute here).

**Phase A — the machine (before content scales)**
- **B1 · Productise the design system.** `prototype-preview.*` → `course/course.{css,js}`, tokenised; template extracted so it's data-driven, not hand-written HTML. *Accept:* Day 26 re-renders identically from the template.
- **B2 · Lesson schema + validator.** Define `tinyskiff.lesson.v1`; add schema + invariant checks to `validate_site.py`. *Accept:* a malformed/over-length day fails the build with a clear error.
- **B3 · Build pipeline.** `collect_lessons` / `render_lesson` / `render_course_index` / `emit_packet` / `derive_backlinks`. *Accept:* one YAML day builds to page + packet + map entry.
- **B4 · Course map + navigation + progress.** `/course/` voyage map, prev/next, `localStorage` progress + resume. *Accept:* progress persists; map reflects completion.

**Phase B — prove it end-to-end**
- **B5 · Convert Day 26 to a real lesson file.** Author `lessons/day-26-ultrasonic.yml` from the shipped prototype; delete the hand-written prototype HTML in favour of the generated page. *Accept:* generated Day 26 matches the approved prototype; packet is byte-reasonable vs the existing one.
- **B6 · Asset extraction workflow.** Documented steps + `source-manifest/` entries for pulling official diagrams. *Accept:* Day 26 assets sourced through the workflow.

**Phase C — author the course**
- **B7 · Author days in batches** (e.g. 1–5 setup/first-light, 6–12, 13–21, 22–30), each day meeting §9. *Accept per batch:* all days validate, render, and read at the #3 quality bar.
- **B8 · Glossary build-out.** Fill `_glossary.yml` as terms first appear. *Accept:* no unresolved keys.

**Phase D — connect + ship**
- **B9 · Landing flip + Library cross-links.** Course-forward `/`; "Taught in Day N" ⇄ "Official sketch"; optionally index lessons in search. *Accept:* both surfaces linked; search intact.
- **B10 · Deploy + verify on Pages.** *Accept:* live site serves Library + Course; spot-checked on desktop + mobile.

## 11. Risks and open items

- **Authoring is the long pole.** The machine (Phase A/B) is small; writing 30 good days is the real effort. Batching + a strict template keep quality even.
- **PDF diagram extraction is manual per day.** Budget content time; the manifest keeps provenance honest.
- **Scope creep from "just one more feature"** (accounts, richer interactivity). Hold the line: static + `localStorage`; richer tracks are a follow-up course.
- **Day-26 double-source risk.** Once B5 lands, the generated lesson is canonical; retire the hand-written prototype to avoid drift.

---

## Status

With #7 resolved, the Wayfinder planning map ([#1](https://github.com/skip-agent/freenove-esp32-s3-docs/issues/1)) is complete: source, voice/template, spine, prototype, content model, and this implementation spec are all settled. **Implementation itself is out of scope for this map** and should open as a new build map using the Phase A–D ticket outline above.
