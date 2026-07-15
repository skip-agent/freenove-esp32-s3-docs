# ESP32-S3 Lab

A cleaner front door to the **Freenove Super Starter Kit for ESP32-S3**, served
as one static site with two surfaces:

- **The Library** (`/`) — a fast, searchable launchpad over every official
  sketch, library, and datasheet.
- **The Course** (`/course/`) — a guided 30-day, Arduino-first tutorial. Each day
  is one complete win in about 30 minutes, in the "echo sounder" design system.

The site is static HTML/CSS/JS built by a Python script and deployed to
Cloudflare Pages. No backend, no accounts; progress lives in the browser.

## In-page lesson chat (optional backend)

Every lesson page carries a floating **"Ask about this lesson"** widget backed by
a local Ollama cloud model (`qwen3-coder:480b-cloud`). It is **backend-aware**: on
load it health-checks `GET /api/chat` and only mounts if a backend answers. So the
*same generated build* is safe on the public Pages host (no backend there → no
button, nothing broken) and lights up automatically wherever the backend is served.

- **Backend:** `serve.py` at the repo root serves `docs/` plus `GET/POST /api/chat`.
  It binds to `127.0.0.1` and knows nothing about who is allowed in — **auth is an
  edge concern, never in the app.** The model is fixed server-side; Ollama stays
  private on `127.0.0.1:11434` and is never proxied.
- **On the Mac mini:** it runs as launchd job `com.skipper.esp32-lab`
  (`deploy/com.skipper.esp32-lab.plist`) on `127.0.0.1:3013`, served to the
  **tailnet only** via `tsdash serve` (never raw `tailscale serve`, **never
  Funnel**). Tailscale identity is the login, so no anonymous visitor can spend
  tokens. Lesson context comes from each lesson's packet JSON.

### Making it public later (Cloudflare + Access) — no app changes

Because auth lives at the edge, sharing the chat publicly (e.g. with family) needs
**zero changes to `serve.py`, the widget, or the build** — only a new front door
and one config value. Put a named Cloudflare Tunnel + Access in front of the same
local port:

1. Create and route a **named** tunnel to a hostname you own (a Quick Tunnel with
   `--url` only gives a random `trycloudflare.com` host, which Access can't target):
   ```bash
   cloudflared tunnel login
   cloudflared tunnel create esp32-chat
   cloudflared tunnel route dns esp32-chat esp32-chat.<domain>
   # ~/.cloudflared/config.yml:
   #   tunnel: esp32-chat
   #   credentials-file: /Users/agent/.cloudflared/<tunnel-id>.json
   #   ingress:
   #     - hostname: esp32-chat.<domain>
   #       service: http://127.0.0.1:3013
   #     - service: http_status:404
   cloudflared tunnel run esp32-chat      # (run as a service to make it permanent)
   ```
2. In Cloudflare Zero Trust, add an **Access** application for `esp32-chat.<domain>`
   with a policy (email allow-list / one-time PIN) so only invited people get in.
3. **Add the new hostname to the backend's trusted-host allowlist** (the DNS-rebind
   guard), or every send returns 403 even though the widget mounts. Append
   `esp32-chat.<domain>` to `LESSON_CHAT_ALLOWED_HOSTS` (comma-separated; the
   default `:443` port is optional — the backend normalizes it). Edit the repo
   plist, copy it over the installed one, and reload so the running process picks
   up the change:
   ```bash
   # after editing deploy/com.skipper.esp32-lab.plist:
   cp deploy/com.skipper.esp32-lab.plist ~/Library/LaunchAgents/com.skipper.esp32-lab.plist
   launchctl bootout   gui/$(id -u)/com.skipper.esp32-lab
   launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.skipper.esp32-lab.plist
   ```
4. Leave Ollama bound to `127.0.0.1:11434`; only `serve.py`'s port is exposed, and
   only behind Access. The tailnet serve and the public Access door can run at once.

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
