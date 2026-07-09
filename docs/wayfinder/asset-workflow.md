# Asset extraction workflow

How official Freenove images become clean course assets, with provenance kept
honest. Resolves the asset-workflow part of the implementation spec (Phase B, B6).

## Two classes of asset

| Class | Lives in | Referenced as | Reused? |
|---|---|---|---|
| Kit-item photo (board, jumper, IDE…) | `course-assets/assets/shared/` | `shared/<name>` | across many days |
| Per-day diagram (wiring, official circuit) | `course-assets/assets/day-NN/` | `day-NN/<name>` | one day |

The build copies `course-assets/assets/` into `docs/course/assets/` on every run.
Lesson files reference the path *relative to that assets root* (e.g.
`image: day-26/circuit-page-172.png`).

## Extracting a per-day diagram

1. Find the official figure in the source PDF (kit is under the gitignored
   `source/`; the manifest `source-manifest/freenove-source.json` records the
   archive it came from). The curriculum spine's "Official source basis" column
   names the sketch/chapter for each day.
2. Crop the diagram to a clean, legible image. Keep it readable on mobile.
3. Save it to `course-assets/assets/day-NN/<slug>.png` with a descriptive name.
4. Write **alt text** that describes the actual connections, not just "a diagram."
5. Add the lesson's `wiring.diagram` block: `image`, `alt`, `caption`, and
   `source: { pdf, chapter, page }`. The validator rejects a diagram with a
   missing `alt` or `source`.
6. Record the asset in `source-manifest/course-assets.json` (PDF, chapter, page).

## Reusing a kit-item photo

Item photos already extracted (board, extension board, HC-SR04, jumper, IDE,
official sketch) live in `course-assets/assets/shared/`. Reference them from any
day's `parts` with `image: shared/<name>` and give each an `alt` and `imageKind`
label ("Manual photo" / "Manual screenshot" / "Manual sketch"). Reuse rather than
duplicate. Add new shared items to the manifest's `shared` list.

## Attribution

Every diagram carries its `source` into the rendered caption *and* the agent
packet, and the colophon repeats chapter/page + license. Freenove material is
CC BY-NC-SA 3.0; the site states it is not affiliated with Freenove. Do not strip
or alter that attribution.
