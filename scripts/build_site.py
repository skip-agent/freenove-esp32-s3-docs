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


def render_html(data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    title = "TinySkiff ESP32-S3 Lab"
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <meta name=\"description\" content=\"A cleaner launchpad for Freenove Super Starter Kit for ESP32-S3 docs, code, libraries, and datasheets.\" />
  <title>{title}</title>
  <link rel=\"stylesheet\" href=\"./styles.css\" />
</head>
<body>
  <header class=\"hero\">
    <nav class=\"topbar\">
      <a class=\"brand\" href=\"#top\">TinySkiff ESP32-S3 Lab</a>
      <div class=\"navlinks\">
        <a href=\"./course/\">The 30-day course</a>
        <a href=\"#start\">Start</a>
        <a href=\"#projects\">Projects</a>
        <a href=\"#resources\">Resources</a>
        <a href=\"#source\">Source</a>
      </div>
    </nav>
    <section class=\"heroGrid\" id=\"top\">
      <div>
        <p class=\"eyebrow\">Freenove Super Starter Kit for ESP32-S3</p>
        <h1>One clean place to start tinkering without spelunking through a 200 MB ZIP.</h1>
        <p class=\"lede\">C/Arduino sketches, MicroPython examples, libraries, setup links, datasheets, and the official docs — organized as a fast searchable launchpad.</p>
        <div class=\"ctaRow\">
          <a class=\"button primary\" href=\"#projects\">Browse projects</a>
          <a class=\"button\" href=\"./course/\">Start the 30-day course</a>
          <a class=\"button\" href=\"{GITHUB_ZIP}\">Download official ZIP</a>
        </div>
      </div>
      <div class=\"heroCard\">
        <img src=\"./assets/Super.jpg\" alt=\"Freenove Super Starter Kit for ESP32-S3\" />
        <dl>
          <div><dt>C sketches</dt><dd>{len(data['projectsC'])}</dd></div>
          <div><dt>Python projects</dt><dd>{len(data['projectsPython'])}</dd></div>
          <div><dt>Libraries</dt><dd>{len(data['libraries'])}</dd></div>
          <div><dt>PDFs/datasheets</dt><dd>{len(data['pdfs'])}</dd></div>
        </dl>
      </div>
    </section>
  </header>

  <main>
    <section id=\"start\" class=\"section\">
      <p class=\"eyebrow\">Start here</p>
      <h2>Pick the track that matches what you want to learn.</h2>
      <div class=\"cards two\">
        <article class=\"card\">
          <h3>C / Arduino IDE</h3>
          <p>Use this if you want the broadest project coverage: audio, Bluetooth, Wi‑Fi, camera, USB HID, and the classic electronics lessons.</p>
          <ol>
            <li>Install Arduino IDE.</li>
            <li>Install/select the ESP32 board package for the ESP32-S3.</li>
            <li>Open a sketch from <code>C/Sketches</code>.</li>
            <li>Use the USB mode/configuration shown in the official tutorial.</li>
          </ol>
          <a href=\"{ONLINE_BASE}fnk0083/codes/C.html\">Open official C docs →</a>
        </article>
        <article class=\"card\">
          <h3>Python / MicroPython</h3>
          <p>Use this if you want a faster beginner loop in Thonny. It covers most core sensor/LED/motor lessons, but not every advanced C project.</p>
          <ol>
            <li>Install Thonny.</li>
            <li>Flash the kit’s MicroPython firmware.</li>
            <li>Upload needed helper libraries from <code>Python_Libraries</code>.</li>
            <li>Run projects from <code>Python_Codes</code>.</li>
          </ol>
          <a href=\"{ONLINE_BASE}fnk0083/codes/Python.html\">Open official Python docs →</a>
        </article>
      </div>
      <div class=\"pinout\">
        <div>
          <h3>Board pinout</h3>
          <p>Keep this open while wiring. ESP32-S3 pins are powerful and a little booby-trapped; the source docs call out strapping, PSRAM, SD card, USB, and camera pins.</p>
        </div>
        <img src=\"./assets/ESP32S3_Pinout.png\" alt=\"ESP32-S3 pinout\" />
      </div>
    </section>

    <section id=\"projects\" class=\"section\">
      <p class=\"eyebrow\">Project browser</p>
      <h2>Search the examples</h2>
      <div class=\"toolbar\">
        <input id=\"search\" type=\"search\" placeholder=\"Search blink, camera, servo, BLE, LCD…\" />
        <select id=\"trackFilter\">
          <option value=\"all\">All tracks</option>
          <option value=\"C / Arduino\">C / Arduino</option>
          <option value=\"Python / MicroPython\">Python / MicroPython</option>
        </select>
      </div>
      <div id=\"projectCount\" class=\"muted\"></div>
      <div id=\"projectGrid\" class=\"projectGrid\"></div>
    </section>

    <section id=\"resources\" class=\"section\">
      <p class=\"eyebrow\">Resources</p>
      <h2>Libraries and PDFs</h2>
      <div class=\"resourceGrid\">
        <article class=\"card\">
          <h3>Libraries</h3>
          <div id=\"libraries\" class=\"list\"></div>
        </article>
        <article class=\"card\">
          <h3>Docs and datasheets</h3>
          <div id=\"pdfs\" class=\"list compact\"></div>
        </article>
      </div>
    </section>

    <section id=\"source\" class=\"section source\">
      <p class=\"eyebrow\">Source + license</p>
      <h2>Built from Freenove’s official materials</h2>
      <p>This launchpad indexes the official Freenove repository and documentation. Freenove’s files are published under Creative Commons Attribution‑NonCommercial‑ShareAlike 3.0 Unported; this site links back to the official source for downloads and full files.</p>
      <div class=\"sourceLinks\">
        <a href=\"{REPO_URL}\">Official GitHub repo</a>
        <a href=\"{GITHUB_ZIP}\">Official ZIP archive</a>
        <a href=\"{ONLINE_BASE}\">Official online docs</a>
        <a href=\"mailto:support@freenove.com\">Freenove support</a>
      </div>
      <p class=\"muted\">Generated {html.escape(data['generatedAt'])}. Not affiliated with Freenove; just a less annoying front door.</p>
    </section>
  </main>

  <dialog id=\"codeDialog\">
    <button id=\"closeDialog\" class=\"close\">×</button>
    <h3 id=\"dialogTitle\"></h3>
    <p id=\"dialogMeta\" class=\"muted\"></p>
    <pre><code id=\"dialogCode\"></code></pre>
  </dialog>

  <script id=\"site-data\" type=\"application/json\">{payload}</script>
  <script src=\"./app.js\"></script>
</body>
</html>
"""


# Generated outputs this build owns. Everything else under docs/ (the committed
# docs/wayfinder/ planning docs) is preserved — the build no longer wipes the
# whole tree.
GENERATED_FILES = ["index.html", "data.json", "styles.css", "app.js"]
GENERATED_DIRS = ["assets", "course"]


def clean_generated() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name in GENERATED_FILES:
        (OUT / name).unlink(missing_ok=True)
    for name in GENERATED_DIRS:
        target = OUT / name
        if target.exists():
            shutil.rmtree(target)


def build_course(data: dict) -> dict:
    """Build /course/ from lessons and return a small summary for the build log.

    Also enriches Library sketch entries with the day that teaches them, so the
    derivation exists in the data (the Library UI cross-link is Phase D).
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

    return {
        "lessons": len(lessons),
        "published": sum(1 for ls in lessons if ls.data.get("status") == "published"),
        "days_in_spine": len(order),
        "backlinks": len(backlinks),
    }


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
    course_summary = build_course(data)
    (OUT / "index.html").write_text(render_html(data), encoding="utf-8")
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
