#!/usr/bin/env python3
"""Static file server for the ESP32-S3 Lab course, with an in-page lesson chat.

Serves the built site under ``docs/`` with no-cache headers (so browsers over
Tailscale always pick up the latest build), and exposes a single ``/api/chat``
endpoint that backs the floating "ask about this lesson" widget:

  * ``GET  /api/chat`` -> ``200 "ok"``  — a health probe. The widget only mounts
    when this succeeds, so the *same generated site* is safe on the public
    Cloudflare Pages host (no backend there -> no chat button, nothing broken)
    and lights up automatically wherever this backend is present.
  * ``POST /api/chat`` -> streams a reply from a local Ollama cloud model.

Authentication is deliberately NOT handled here: this binds to 127.0.0.1 and
knows nothing about who is allowed in. Access is an edge concern — today the
tailnet (via ``tsdash serve``) is the login; later a Cloudflare Access policy in
front of the same port can share it publicly with no change to this file.

Usage: serve.py [port] [directory]   (directory defaults to ./docs)
"""
import functools
import http.server
import json
import os
import socketserver
import sys
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 3013
DIRECTORY = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "docs")

# Ollama runs a local HTTP API; the model is fixed server-side so this endpoint
# (reachable over the tailnet) can't be used to run arbitrary/expensive models.
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODEL = "qwen3-coder:480b-cloud"

# A NUL byte can't occur in normal model text, so the widget uses it as an
# out-of-band signal: everything after it is a stream-failure notice to SHOW the
# learner but NOT record as an assistant turn (the 200 was already committed once
# streaming began, so failures can't be an HTTP status any more).
STREAM_ERROR_MARK = "\x00"

# A legitimate chat request is a few KB once the widget's fields are bounded;
# refuse anything larger so a huge Content-Length can't be buffered into memory.
MAX_BODY_BYTES = 256 * 1024

# DNS-rebinding defence: POSTs are only accepted when the Host/Origin the browser
# used is a KNOWN-TRUSTED hostname, not merely self-consistent (a rebound attacker
# host equals itself). Defaults cover local direct access; the served tailnet host
# (and any future Cloudflare Access host) is added via LESSON_CHAT_ALLOWED_HOSTS
# in the launchd job. Value is a comma-separated list of host[:port].
def _norm_host(host):
    """Lowercase and drop a default port so `host`, `host:443`, `host:80` match.

    A browser omits the port from Host/Origin on standard 443/80, so an allowlist
    entry written either way (e.g. `esp32-chat.example.com` or `…:443`) matches.
    """
    host = (host or "").strip().lower()
    for default in (":443", ":80"):
        if host.endswith(default):
            return host[: -len(default)]
    return host


ALLOWED_HOSTS = {
    _norm_host(h)
    for h in (
        [f"127.0.0.1:{PORT}", f"localhost:{PORT}", f"[::1]:{PORT}"]
        + os.environ.get("LESSON_CHAT_ALLOWED_HOSTS", "").split(",")
    )
    if h.strip()
}

SYSTEM_TEMPLATE = (
    "You are the ESP32-S3 Lab tutor — a patient firmware coach helping Sam, a "
    "beginner, work through this Arduino-first course for the Freenove Super "
    "Starter Kit for ESP32-S3. Answer his question about the current lesson "
    "clearly and concisely, in plain language, assuming no prior electronics or "
    "embedded experience. Explain unfamiliar terms simply. Do not quiz him and "
    "do not pad with filler.\n\n"
    "Coaching style: when he's mid-build, guide one physical step at a time and "
    "wait rather than dumping the whole procedure. Keep the distinction between "
    "board selection (the compile target, e.g. 'ESP32S3 Dev Module') and port "
    "selection (the connected device, e.g. /dev/cu.usbmodem...) crisp.\n\n"
    "Hardware safety — state these when relevant, never contradict them: check "
    "the wiring against the diagram BEFORE applying power; the ESP32-S3 GPIO is "
    "3.3 V logic, so never feed a pin 5 V; never connect an OUTPUT pin that's "
    "driven HIGH straight to GND (or one driven LOW straight to 3V3) — that "
    "shorts the driver; always use a current-limiting resistor with an LED. "
    "(Tying an INPUT pin to GND or 3V3 through a button is normal and expected — "
    "that's how the button lessons work, especially with INPUT_PULLUP.) If "
    "something could damage the board or a part, say so plainly.\n\n"
    "When you give Arduino/C code or a shell command, show it in a fenced code "
    "block and briefly say what it does. Base your answer on the lesson context "
    "below; if the lesson doesn't cover something, say so instead of inventing "
    "pin numbers or wiring.\n\n"
    "Current lesson: {title}\n\n"
    "Lesson context (for your reference):\n{context}\n\n"
    "Learner progress: {progress}"
)

# Fields pulled from the structured lesson packet (tinyskiff.lessonPacket.v0),
# in reading order, to build a compact, reliable context instead of scraping the
# rendered page's innerText.
PACKET_FIELDS = (
    ("mission", "Mission"),
    ("parts", "Parts"),
    ("wiring", "Wiring"),
    ("steps", "Build steps"),
    ("codeFocus", "Code focus"),
    ("theoryModel", "Theory / how it works"),
    ("test", "Expected result / how to tell it worked"),
    ("coachInstructions", "Coaching notes"),
    ("troubleshooting", "Troubleshooting"),
    ("challenge", "Try-it challenge"),
)


CONTEXT_BUDGET = 9000     # total chars of lesson context sent to the model


def _truncate(text, limit):
    """Trim text to a char limit at a whitespace boundary, marking the cut."""
    if len(text) <= limit:
        return text
    cut = text[: max(0, limit - 14)].rstrip()
    return cut + " …[truncated]"


def context_from_packet(packet):
    """Flatten selected lesson-packet fields into a bounded text block.

    Keeps EVERY present section represented rather than dropping later ones
    wholesale: if the sections fit the budget they're included whole, otherwise
    each section gets an equal share of the budget and is trimmed to fit. This
    guarantees a small-but-important section (e.g. troubleshooting) isn't skipped
    just because earlier sections were large.
    """
    if not isinstance(packet, dict):
        return ""
    sections = []
    for key, label in PACKET_FIELDS:
        value = packet.get(key)
        if not value:
            continue
        rendered = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
        sections.append((label, rendered))
    if not sections:
        return ""

    joined = [f"## {label}\n{body}" for label, body in sections]
    total = sum(len(s) for s in joined) + 2 * (len(joined) - 1)
    if total > CONTEXT_BUDGET:
        # Fair share per section (reserve room for the "## label\n" header + join).
        share = CONTEXT_BUDGET // len(sections) - 2
        joined = [
            f"## {label}\n{_truncate(body, max(40, share - len(label) - 4))}"
            for label, body in sections
        ]
    return "\n\n".join(joined)


def build_messages(body):
    """Compose the model messages from the widget's request, server-side."""
    title = str(body.get("lessonTitle") or "the current lesson")[:200]
    # Prefer the structured packet; fall back to the page's scraped text.
    context = context_from_packet(body.get("lessonPacket"))
    if not context:
        context = str(body.get("lessonText") or "")[:9000]
    progress = str(body.get("progress") or "unknown")[:600]
    raw = body.get("messages")
    if not isinstance(raw, list):  # a non-list "messages" would break iteration
        raw = []
    convo = [
        {"role": m.get("role"), "content": str(m.get("content", ""))[:4000]}
        for m in raw
        if isinstance(m, dict) and m.get("role") in ("user", "assistant")
    ][-12:]
    # The window can start on an assistant reply whose question was trimmed off,
    # leaving it orphaned after the system prompt; drop leading assistant turns
    # so the retained history always begins with a user message.
    while convo and convo[0]["role"] != "user":
        convo.pop(0)
    system = SYSTEM_TEMPLATE.format(title=title, context=context, progress=progress)
    return [{"role": "system", "content": system}] + convo


class CourseHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def _request_host_trusted(self):
        """True if the host the browser targeted is on the trusted allowlist.

        Behind the tailscale/tsdash proxy the browser-facing host arrives as
        X-Forwarded-Host (falling back to Host for direct local access). Checking
        it against an explicit allowlist — rather than comparing Host to Origin —
        is what defeats DNS rebinding, where the attacker host matches itself.
        """
        host = (self.headers.get("X-Forwarded-Host") or self.headers.get("Host") or "")
        return _norm_host(host.split(",")[0]) in ALLOWED_HOSTS

    def _origin_trusted(self):
        """True if there's no Origin, or its host is on the trusted allowlist."""
        origin = self.headers.get("Origin")
        if origin is None:
            return True
        return _norm_host(urllib.parse.urlsplit(origin).netloc) in ALLOWED_HOSTS

    def do_GET(self):
        # Health probe. The widget mounts only when this responds with our
        # sentinel HEADER, not merely 200 — a static host (e.g. Cloudflare Pages)
        # serves its HTML fallback with 200 for unknown routes, so an "ok" status
        # or body alone would wrongly mount the widget there. The custom header
        # can't appear in a static host's fallback, so it reliably identifies
        # this backend and keeps the public build clean.
        if self.path.split("?")[0] == "/api/chat":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("X-Lesson-Chat", "ok")
            self.end_headers()
            self.wfile.write(b"ok")
            return
        super().do_GET()

    def do_POST(self):
        if self.path.split("?")[0] != "/api/chat":
            self.send_error(404, "Not found")
            return
        # CSRF + DNS-rebinding defence. A site the learner visits while on the
        # tailnet could fire a "simple" cross-origin POST (text/plain, no
        # preflight) and spend cloud tokens under their Tailscale identity, or use
        # a rebound hostname to reach this port. So: require application/json
        # (forces a CORS preflight this server never approves), require the
        # browser-facing host to be on the trusted allowlist, and reject any
        # off-allowlist Origin. The widget always sends application/json to a
        # trusted host, so it is unaffected.
        ctype = (self.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        if ctype != "application/json":
            self.send_error(415, "Unsupported Media Type")
            return
        if not self._request_host_trusted():
            self.send_error(403, "Untrusted host")
            return
        if not self._origin_trusted():
            self.send_error(403, "Cross-origin request refused")
            return
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            self.send_error(400, "Invalid Content-Length")
            return
        # A well-formed request is a few KB (context is bounded server-side); cap
        # the body so a huge Content-Length can't be read wholesale into memory
        # and exhaust the process (which also serves the static site).
        if length < 0 or length > MAX_BODY_BYTES:
            self.send_error(413, "Request body too large")
            return
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            self.send_error(400, "Invalid JSON body")
            return
        # A scalar/array is valid JSON but build_messages() expects a mapping;
        # reject it here as a controlled 400 rather than a proxied 502 + traceback.
        if not isinstance(body, dict):
            self.send_error(400, "JSON body must be an object")
            return

        payload = json.dumps(
            {"model": MODEL, "messages": build_messages(body), "stream": True}
        ).encode("utf-8")
        req = urllib.request.Request(
            OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"}
        )

        # Open the upstream BEFORE committing 200: if Ollama is offline or
        # rejects the model, fail with a real non-2xx so the widget shows an
        # error and doesn't record the failure text as a valid assistant turn.
        try:
            resp = urllib.request.urlopen(req, timeout=180)
        except Exception as exc:  # noqa: BLE001 - connection refused, HTTP error, timeout…
            self.send_error(502, f"Model backend unavailable: {exc}")
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        done_seen = False
        stream_failed = False
        try:
            with resp:
                for line in resp:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    # Ollama can report a mid-stream failure as an `error` field;
                    # surface it instead of silently leaving the widget on "…".
                    err = obj.get("error")
                    if err:
                        stream_failed = True
                        self.wfile.write(
                            f"{STREAM_ERROR_MARK}[Model error: {err}]".encode("utf-8")
                        )
                        self.wfile.flush()
                        break
                    chunk = (obj.get("message") or {}).get("content", "")
                    if chunk:
                        self.wfile.write(chunk.encode("utf-8"))
                        self.wfile.flush()
                    if obj.get("done"):
                        done_seen = True
                        break
            # A clean HTTP EOF before any `done` frame is still a truncated answer;
            # flag it out-of-band so the widget doesn't record a partial/empty turn.
            if not done_seen and not stream_failed:
                self.wfile.write(
                    f"{STREAM_ERROR_MARK}[The model stopped before finishing.]".encode("utf-8")
                )
                self.wfile.flush()
        except Exception as exc:  # noqa: BLE001 - a drop mid-stream (200 already sent)
            try:
                self.wfile.write(
                    f"{STREAM_ERROR_MARK}[Connection to the model dropped: {exc}]".encode("utf-8")
                )
            except OSError:
                pass


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    handler = functools.partial(CourseHandler, directory=DIRECTORY)
    with Server(("127.0.0.1", PORT), handler) as httpd:
        httpd.serve_forever()
