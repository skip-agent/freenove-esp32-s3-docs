#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

import course_build
import lesson_schema

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "source" / "Freenove_Super_Starter_Kit_for_ESP32_S3-main"
OUT = ROOT / "docs"
ASSETS = OUT / "assets"
ONLINE_BASE = "https://docs.freenove.com/projects/fnk0083/en/latest/"
GITHUB_ZIP = "https://github.com/Freenove/Freenove_Super_Starter_Kit_for_ESP32_S3/archive/refs/heads/main.zip"
REPO_URL = "https://github.com/Freenove/Freenove_Super_Starter_Kit_for_ESP32_S3"


def clean_name(s: str) -> str:
    s = re.sub(r"^Sketch_", "", s)
    s = re.sub(r"[_-]+", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def read_text(path: Path, limit: int = 1800) -> str:
    try:
        txt = path.read_text(errors="replace")
    except Exception:
        return ""
    txt = txt.replace("\r\n", "\n")
    return txt[:limit]


def file_size_label(path: Path) -> str:
    try:
        n = path.stat().st_size
    except Exception:
        return ""
    units = ["B", "KB", "MB", "GB"]
    f = float(n)
    for u in units:
        if f < 1024 or u == units[-1]:
            return f"{f:.1f} {u}" if u != "B" else f"{int(f)} B"
        f /= 1024
    return str(n)


def online_doc_url(track: str, project_dir: str) -> str:
    # The official docs use chapter pages, not 1:1 sketch pages. Link the track landing
    # and let site search route users to the right official chapter.
    if track == "C":
        return ONLINE_BASE + "fnk0083/codes/C.html"
    return ONLINE_BASE + "fnk0083/codes/Python.html"


def collect_c_sketches() -> list[dict]:
    out = []
    base = SRC / "C" / "Sketches"
    for ino in sorted(base.glob("*/**/*.ino")):
        project = ino.parent.name
        num = re.match(r"Sketch_([0-9]+(?:\.[0-9]+)?)", project)
        out.append({
            "track": "C / Arduino",
            "kind": "sketch",
            "number": num.group(1) if num else "",
            "title": clean_name(project),
            "folder": str(ino.parent.relative_to(SRC)),
            "file": ino.name,
            "language": "Arduino C++",
            "code": read_text(ino, 2400),
            "sourceUrl": f"{REPO_URL}/tree/main/{ino.parent.relative_to(SRC).as_posix()}",
            "docsUrl": online_doc_url("C", project),
        })
    return out


def collect_python_projects() -> list[dict]:
    out = []
    base = SRC / "Python" / "Python_Codes"
    for d in sorted([p for p in base.iterdir() if p.is_dir()], key=lambda p: p.name):
        files = sorted([p for p in d.rglob("*.py") if p.is_file()])
        main = files[0] if files else None
        num = re.match(r"([0-9]+(?:\.[0-9]+)?)", d.name)
        out.append({
            "track": "Python / MicroPython",
            "kind": "project",
            "number": num.group(1) if num else "",
            "title": clean_name(d.name),
            "folder": str(d.relative_to(SRC)),
            "file": main.name if main else "",
            "language": "MicroPython",
            "code": read_text(main, 2400) if main else "",
            "sourceUrl": f"{REPO_URL}/tree/main/{d.relative_to(SRC).as_posix()}",
            "docsUrl": online_doc_url("Python", d.name),
        })
    return out


def collect_libraries() -> list[dict]:
    libs = []
    for p in sorted((SRC / "C" / "Libraries").glob("*.zip")):
        libs.append({"track": "C / Arduino", "name": p.stem, "file": p.name, "size": file_size_label(p), "sourceUrl": f"{REPO_URL}/tree/main/{p.relative_to(SRC).as_posix()}"})
    for p in sorted((SRC / "Python" / "Python_Libraries").glob("*.py")):
        libs.append({"track": "Python / MicroPython", "name": p.stem, "file": p.name, "size": file_size_label(p), "sourceUrl": f"{REPO_URL}/blob/main/{p.relative_to(SRC).as_posix()}"})
    return libs


def collect_pdfs() -> list[dict]:
    docs = []
    for p in sorted(SRC.rglob("*.pdf")):
        rel = p.relative_to(SRC).as_posix()
        docs.append({"title": p.stem.replace("_", " "), "folder": str(p.parent.relative_to(SRC)), "file": p.name, "size": file_size_label(p), "sourceUrl": f"{REPO_URL}/blob/main/{rel}"})
    return docs


def copy_assets() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    for name in ["Super.jpg", "ESP32S3_Pinout.png", "Arduino_Configuration_USB_OTG.png", "Arduino_Configuration_USB_UART.png"]:
        src = SRC / name
        if src.exists():
            shutil.copy2(src, ASSETS / name)
    site_assets = ROOT / "site-assets"
    if site_assets.exists():
        for p in site_assets.iterdir():
            if p.is_file():
                shutil.copy2(p, OUT / p.name)


FONTS_HEAD = (
    '<link rel="preconnect" href="https://fonts.googleapis.com" />\n'
    '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />\n'
    '  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Spline+Sans+Mono:wght@400;500;600&display=swap" rel="stylesheet" />'
)


def _day_range(a: int, b: int) -> str:
    return f"Day {a}" if a == b else f"Days {a}–{b}"


def render_html(data: dict, ctx: dict) -> str:
    """Render the course-forward landing (`/`).

    The course is the product: the hero leads with the 30-day voyage and a live
    progress tracker (localStorage, shared with the course map), the arcs preview
    one click from the full map, and the searchable reference Library is a clearly
    secondary band below. The landing carries its own light, minimal design
    (landing.css) — approachable for a first-time ESP32 learner — and does not
    inherit the course pages' heavier styling.
    """
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    course_payload = json.dumps({
        "total": ctx["total"],
        "publishedDays": ctx["publishedDays"],
        "slugs": ctx["slugs"],
        "day1Slug": ctx["day1Slug"],
    }, ensure_ascii=False).replace("</", "<\\/")
    title = "ESP32-S3 Lab — learn the ESP32-S3 in 30 guided days"
    day1_href = f"./course/{ctx['day1Slug']}/" if ctx["day1Slug"] else "./course/"

    legs = []
    for i, leg in enumerate(ctx["legs"], start=1):
        rng = _day_range(leg["dayFrom"], leg["dayTo"])
        href = f"./course/{leg['startSlug']}/" if leg["startSlug"] else "./course/"
        legs.append(f"""        <a class=\"leg\" href=\"{href}\">
          <span class=\"leg-no mono\">{i:02d}</span>
          <span class=\"leg-body\">
            <span class=\"leg-range mono\">{rng}</span>
            <span class=\"leg-name\">{html.escape(leg['name'])}</span>
            <span class=\"leg-sub\">{html.escape(leg['subtitle'])}</span>
          </span>
        </a>""")
    legs_html = "\n".join(legs)
    leg_words = {
        1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five",
        6: "Six", 7: "Seven", 8: "Eight", 9: "Nine", 10: "Ten",
    }
    leg_count_word = leg_words.get(len(ctx["legs"]), str(len(ctx["legs"])))

    counts = (
        (len(data["projectsC"]), "C / Arduino sketches"),
        (len(data["projectsPython"]), "MicroPython projects"),
        (len(data["libraries"]), "libraries"),
        (len(data["pdfs"]), "datasheets & PDFs"),
    )
    stats_html = "\n".join(
        f'          <div class=\"lib-stat\"><b>{n}</b><span>{label}</span></div>'
        for n, label in counts
    )

    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <meta name=\"description\" content=\"A guided, Arduino-first 30-day course for the Freenove Super Starter Kit for ESP32-S3 — plus a searchable library of every official sketch, example, and datasheet.\" />
  <title>{title}</title>
  {FONTS_HEAD}
  <link rel=\"stylesheet\" href=\"./landing.css\" />
</head>
<body>
  <div class=\"page\">
    <header class=\"hero\" id=\"top\">
      <div class=\"hero-grid\">
        <div class=\"hero-copy\">
          <p class=\"eyebrow\">ESP32-S3 Lab</p>
          <h1>Learn the ESP32-S3 in <span class=\"hl\">30 guided days</span>.</h1>
          <p class=\"lede\">A friendly, Arduino-first course built on the Freenove Super Starter Kit. Each day you wire one small circuit, run it, and understand why it works — about 30 minutes, one real win.</p>
          <div class=\"cta-row\">
            <a class=\"btn btn-primary\" href=\"{day1_href}\">Start Day 1 →</a>
            <a class=\"btn btn-ghost\" href=\"./course/\">See the 30-day map</a>
          </div>
          <p class=\"hero-foot\">Free · No account · Runs in your browser</p>
        </div>
        <aside class=\"voyage-card\" id=\"mapProgress\" aria-label=\"Your course progress\">
          <div class=\"voyage-head\">
            <span class=\"voyage-title\">Your voyage</span>
            <span class=\"voyage-count\"><b id=\"doneCount\">0</b> / {ctx['total']} days</span>
          </div>
          <div class=\"voyage\" id=\"mapVoyage\" role=\"img\" aria-label=\"Days completed\"></div>
          <a class=\"voyage-resume\" id=\"mapResume\" href=\"#\" hidden>Resume →</a>
          <p class=\"voyage-note\" id=\"firstRun\">Cast off with Day 1 — your place is saved as you go.</p>
        </aside>
      </div>
    </header>

    <main>
      <section class=\"legs-section\">
        <div class=\"section-head\">
          <p class=\"eyebrow\">The voyage</p>
          <h2 class=\"section-h2\">{leg_count_word} legs, thirty days.</h2>
          <p class=\"section-sub\">The course runs as one voyage — from first light to the open network. Start at the beginning, or jump into any leg.</p>
        </div>
        <div class=\"legs\">
{legs_html}
        </div>
      </section>

      <section class=\"lib\" id=\"library\">
        <div class=\"section-head\">
          <p class=\"eyebrow\">The reference library · optional</p>
          <h2 class=\"section-h2\">Every official example, in one searchable place.</h2>
          <p class=\"section-sub\">Already comfortable with the board? Skip the course and browse every sketch, example, library, and datasheet from the official kit — no spelunking through a 200&nbsp;MB ZIP.</p>
          <div class=\"lib-stats\">
{stats_html}
          </div>
        </div>

        <div class=\"toolbar\">
          <input id=\"search\" type=\"search\" placeholder=\"Search blink, camera, servo, BLE, LCD…\" aria-label=\"Search examples\" />
          <select id=\"trackFilter\" aria-label=\"Filter by track\">
            <option value=\"all\">All tracks</option>
            <option value=\"C / Arduino\">C / Arduino</option>
            <option value=\"Python / MicroPython\">Python / MicroPython</option>
          </select>
        </div>
        <div id=\"projectCount\" class=\"proj-count mono\"></div>
        <div id=\"projectGrid\" class=\"proj-grid\"></div>

        <div class=\"res-grid\">
          <article class=\"res-card\">
            <h3>Libraries</h3>
            <div id=\"libraries\" class=\"res-list\"></div>
          </article>
          <article class=\"res-card\">
            <h3>Docs &amp; datasheets</h3>
            <div id=\"pdfs\" class=\"res-list compact\"></div>
          </article>
        </div>
      </section>
    </main>

    <footer class=\"colophon\">
      <p><strong>ESP32-S3 Lab.</strong> A guided course and library built on the official Freenove Super Starter Kit for ESP32-S3 material, released under CC BY-NC-SA 3.0. Not affiliated with or endorsed by Freenove.</p>
      <div class=\"src-links\">
        <a href=\"{REPO_URL}\">Official GitHub repo</a>
        <a href=\"{GITHUB_ZIP}\">Official ZIP archive</a>
        <a href=\"{ONLINE_BASE}\">Official online docs</a>
        <a href=\"mailto:support@freenove.com\">Freenove support</a>
      </div>
      <p class=\"gen mono\">Generated {html.escape(data['generatedAt'])}.</p>
    </footer>
  </div>

  <dialog id=\"codeDialog\" class=\"code-dialog\">
    <button id=\"closeDialog\" class=\"close\" aria-label=\"Close\">×</button>
    <h3 id=\"dialogTitle\"></h3>
    <p id=\"dialogMeta\" class=\"mono\"></p>
    <pre><code id=\"dialogCode\"></code></pre>
  </dialog>

  <script id=\"site-data\" type=\"application/json\">{payload}</script>
  <script id=\"landing-course\" type=\"application/json\">{course_payload}</script>
  <script src=\"./app.js\"></script>
</body>
</html>
"""


# Generated outputs this build owns. Everything else under docs/ (the committed
# docs/wayfinder/ planning docs) is preserved — the build no longer wipes the
# whole tree.
GENERATED_FILES = ["index.html", "data.json", "landing.css", "app.js"]
GENERATED_DIRS = ["assets", "course"]


def clean_generated() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name in GENERATED_FILES:
        (OUT / name).unlink(missing_ok=True)
    for name in GENERATED_DIRS:
        target = OUT / name
        if target.exists():
            shutil.rmtree(target)


def build_course(data: dict) -> tuple[dict, dict]:
    """Build /course/ from lessons; return (build-log summary, landing context).

    Also enriches Library sketch entries with the day that teaches them so the
    Library cards can render a "Taught in Day N" cross-link, and returns the
    context the course-forward landing needs: the voyage total, the published
    days and their slugs (for the shared progress instrument), the first day to
    start on, and the six arcs as preview "legs".
    """
    lessons = lesson_schema.collect_lessons()  # validates; raises on any problem
    glossary = lesson_schema.load_glossary()
    course = lesson_schema.load_course()
    order = course_build.course_day_order(course)

    course_out = OUT / "course"
    course_build.copy_course_assets(course_out)
    (course_out / "packets").mkdir(parents=True, exist_ok=True)

    # Only `published` days get a page + packet + prev/next entry. Draft/review
    # days are still validated (above) but not deployed, matching the status
    # contract in the authoring docs.
    published = [ls for ls in lessons if ls.data.get("status") == "published"]
    published_map = {
        ls.data["day"]: {"day": ls.data["day"], "slug": ls.data["slug"], "title": ls.data["title"]}
        for ls in published
    }

    for lesson in published:
        page = course_build.render_lesson(lesson.data, glossary, order, published_map)
        day_dir = course_out / lesson.data["slug"]
        day_dir.mkdir(parents=True, exist_ok=True)
        (day_dir / "index.html").write_text(page, encoding="utf-8")

        packet = course_build.emit_packet(lesson.data, glossary)
        packet_path = course_out / "packets" / f"{lesson.data['lessonCode']}.json"
        packet_path.write_text(json.dumps(packet, indent=2, ensure_ascii=False), encoding="utf-8")

    (course_out / "index.html").write_text(
        course_build.render_course_index(course, lessons), encoding="utf-8")

    backlinks = course_build.derive_backlinks(lessons)
    for sketch in data["projectsC"]:
        link = backlinks.get(sketch.get("folder"))
        if link:
            sketch["taughtInDay"] = link

    published_days = sorted(published_map)
    slugs = {str(n): published_map[n]["slug"] for n in published_days}
    # First day to start on: the first day of the voyage order that is published.
    first_day = next((d["day"] for d in order if d["day"] in published_map), None)
    day1_slug = published_map[first_day]["slug"] if first_day is not None else None

    legs = []
    for arc in course.get("arcs") or []:
        days = [d["day"] for d in (arc.get("days") or [])]
        if not days:
            continue
        published_in_arc = [n for n in days if n in published_map]
        legs.append({
            "name": arc.get("name", ""),
            "subtitle": arc.get("subtitle", ""),
            "dayFrom": min(days),
            "dayTo": max(days),
            "startSlug": published_map[published_in_arc[0]]["slug"] if published_in_arc else None,
        })

    summary = {
        "lessons": len(lessons),
        "published": len(published_map),
        "days_in_spine": len(order),
        "backlinks": len(backlinks),
    }
    ctx = {
        "total": course.get("totalDays", len(order)),
        "publishedDays": published_days,
        "slugs": slugs,
        "day1Slug": day1_slug,
        "legs": legs,
    }
    return summary, ctx


def main() -> None:
    if not SRC.exists():
        raise SystemExit(f"Missing source folder: {SRC}")
    clean_generated()
    copy_assets()
    data = {
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "projectsC": collect_c_sketches(),
        "projectsPython": collect_python_projects(),
        "libraries": collect_libraries(),
        "pdfs": collect_pdfs(),
    }
    course_summary, course_ctx = build_course(data)
    (OUT / "index.html").write_text(render_html(data, course_ctx), encoding="utf-8")
    (OUT / "data.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "out": str(OUT),
        "c_sketches": len(data["projectsC"]),
        "python_projects": len(data["projectsPython"]),
        "libraries": len(data["libraries"]),
        "pdfs": len(data["pdfs"]),
        "course": course_summary,
    }, indent=2))


if __name__ == "__main__":
    main()
