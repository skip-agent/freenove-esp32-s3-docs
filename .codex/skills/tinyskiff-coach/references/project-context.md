# TinySkiff project context

- Course: TinySkiff ESP32-S3 Lab, based on the Freenove Super Starter Kit for ESP32-S3.
- Live site: `https://esp32.tinyskiff.xyz` on Cloudflare Pages.
- Authoritative Mac mini checkout: `/Users/agent/Projects/freenove-esp32-s3-docs`, reachable as `ssh mac-mini` (user `agent`).
- GitHub: `https://github.com/skip-agent/freenove-esp32-s3-docs`.
- Lesson source of truth: `lessons/day-NN-slug.yml`.
- Generated lesson: `docs/course/day-NN-slug/index.html`.
- Generated agent packet: `docs/course/packets/<LESSON-CODE>.json`.
- Shared renderer/design: `scripts/course_build.py`, `course-assets/course.css`, and `course-assets/course.js`.
- Build with the repo venv: `.venv/bin/python scripts/build_site.py`.
- Validate: `.venv/bin/python scripts/validate_site.py`.
- Tests: `.venv/bin/python -m unittest discover -s scripts/tests`.
- Pushes to `main` that change `docs/**` deploy through `.github/workflows/deploy.yml`.

## Known coaching evidence

- Current Arduino IDE on macOS opens the dialog through `Arduino IDE → Settings…`, although its window title may still say “Preferences.”
- In the observed IDE, **Additional boards manager URLs** is a long text field. Paste the ESP32 URL directly into it and click **OK** once. The adjacent icon manages multiple URLs and is optional.
- ESP32 stable package URL: `https://espressif.github.io/arduino-esp32/package_esp32_index.json`.
- Install **esp32 by Espressif Systems** from Boards Manager.
- The Freenove board target is **ESP32S3 Dev Module**.
- On macOS, identify the port by unplugging/reconnecting; the returning item commonly contains `usbserial` or `usbmodem`. Ignore Bluetooth, audio, and debug-console entries.
- If no serial device appears, check a known data-capable cable and another USB port before the CH343 driver.

## Editing guardrails

- Preserve learner evidence verbatim enough to reproduce the mismatch.
- Edit YAML/source first; never hand-edit only a generated page.
- Regenerate only owned outputs and inspect the diff for unrelated churn.
- Layout changes require a rendered screenshot at desktop and a responsive breakpoint.
- Existing dirty files on the Mac mini belong to the user; use an isolated worktree when needed.
