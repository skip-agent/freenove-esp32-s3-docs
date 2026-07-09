#!/usr/bin/env python3
"""Course build — render lessons into pages, the course map, and agent packets.

Called by build_site.py. One lesson file (``tinyskiff.lesson.v1``) is projected
into three outputs so they never drift:

  render_lesson()        -> docs/course/day-NN-slug/index.html
  render_course_index()  -> docs/course/index.html   (the voyage map)
  emit_packet()          -> docs/course/packets/<CODE>.json  (v0 packet)
  derive_backlinks()     -> {sketch path -> "Taught in Day N"} for the Library

The productised design system (course.css / course.js, and image assets) lives
under ``course-assets/`` and is copied into ``docs/course/`` by copy_course_assets().
"""
from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path

from lesson_schema import (
    INLINE_TOPIC_RE,
    PACKET_SCHEMA,
    ROOT,
    Lesson,
    referenced_topics,
)

COURSE_ASSETS = ROOT / "course-assets"
COURSE_TITLE = "TinySkiff ESP32-S3 Lab"
SOURCE_PREFIX = "source/Freenove_Super_Starter_Kit_for_ESP32_S3-main"

# Section scaffolding shared by every day (the consistent workshop voice). A
# lesson supplies the content; these supply the fixed kicker / title / rail label
# unless the lesson overrides title/railLabel (e.g. theory, challenge).
SECTIONS = {
    "parts":     {"kicker": "First, know the pieces",         "title": "What you need",     "rail": "What you need"},
    "wiring":    {"kicker": "Make the physical circuit",       "title": "Chart the circuit", "rail": "Chart the circuit"},
    "steps":     {"kicker": "One action at a time",            "title": "Build it",          "rail": "Build it"},
    "code":      {"kicker": "Read just enough code",           "title": "Read the code",     "rail": "Read the code"},
    "theory":    {"kicker": "Understand, don't memorise",      "title": "Theory",            "rail": "Theory"},
    "test":      {"kicker": "Know it worked",                  "title": "Test & debug",      "rail": "Test & debug"},
    "challenge": {"kicker": "Make the idea yours",             "title": "Try this",          "rail": "Try this"},
    "agent":     {"kicker": "Learn it with a hand on the tiller", "title": "Coach me through it", "rail": "Coach me"},
}
SECTION_ORDER = ["parts", "wiring", "steps", "code", "theory", "test", "challenge", "agent"]

# A minimal, deterministic C/MicroPython highlighter — enough to colour the code
# focus without a client-side highlighter. Keywords/types get one colour, numbers
# another, and a function call (identifier immediately before "(") a third.
CODE_KEYWORDS = {
    "#define", "#include", "float", "int", "double", "char", "bool", "void",
    "const", "unsigned", "long", "short", "static", "return",
}


# --------------------------------------------------------------------------
# Inline text helpers
# --------------------------------------------------------------------------
def esc(text: object) -> str:
    return html.escape(str(text if text is not None else ""))


def _define_chip(topic: str) -> str:
    return f'<button class="define" data-topic="{esc(topic)}">Define</button>'


def _chip(block: dict) -> str:
    """A leading-space Define chip for a block's ``explain:`` key, or ''."""
    key = block.get("explain")
    return f" {_define_chip(key)}" if key else ""


def inline(text: object) -> str:
    """Render a short Markdown string to inline HTML.

    Supports `code`, **strong**, *emphasis*, and {glossary-key} define chips.
    """
    out = esc(text)
    out = re.sub(r"`([^`]+)`", lambda m: f"<code>{m.group(1)}</code>", out)
    out = re.sub(r"\*\*([^*]+)\*\*", lambda m: f"<strong>{m.group(1)}</strong>", out)
    out = re.sub(r"\*([^*]+)\*", lambda m: f"<em>{m.group(1)}</em>", out)
    out = INLINE_TOPIC_RE.sub(lambda m: _define_chip(m.group(1)), out)
    return out


def plain_text(text: object) -> str:
    """Strip lesson markup to plain prose for the agent packet."""
    out = str(text if text is not None else "")
    out = INLINE_TOPIC_RE.sub("", out)  # drop {glossary-key} define chips
    out = out.replace("`", "").replace("**", "").replace("*", "")
    return re.sub(r"\s{2,}", " ", out).strip()


def headline_html(text: str) -> str:
    """Hero headline: '|' -> line break, '{word}' -> emphasised accent."""
    out = esc(text)
    out = out.replace("|", "<br />")
    out = re.sub(r"\{([^}]+)\}", lambda m: f"<em>{m.group(1)}</em>", out)
    return out


def formula_html(text: str) -> str:
    """Formula card: **term** becomes an accented <b>."""
    return re.sub(r"\*\*([^*]+)\*\*", lambda m: f"<b>{m.group(1)}</b>", esc(text))


def highlight(src: str) -> str:
    """Wrap keywords, numbers, and function calls in token spans (escaped)."""
    tokens = re.findall(r"#?[A-Za-z_]\w*|\d+\.?\d*|\s+|.", src)
    result: list[str] = []
    for idx, tok in enumerate(tokens):
        if tok.isspace() or not tok.strip():
            result.append(esc(tok))
            continue
        if re.fullmatch(r"\d+\.?\d*", tok):
            result.append(f'<span class="tok-num">{esc(tok)}</span>')
        elif tok in CODE_KEYWORDS:
            result.append(f'<span class="tok-key">{esc(tok)}</span>')
        elif re.fullmatch(r"#?[A-Za-z_]\w*", tok) and _is_call(tokens, idx):
            result.append(f'<span class="tok-fn">{esc(tok)}</span>')
        else:
            result.append(esc(tok))
    return "".join(result)


def _is_call(tokens: list[str], idx: int) -> bool:
    """True if the next non-space token is an opening parenthesis."""
    for nxt in tokens[idx + 1:]:
        if nxt.isspace():
            continue
        return nxt == "("
    return False


# --------------------------------------------------------------------------
# Lesson page
# --------------------------------------------------------------------------
def _resolve_explainers(lesson: dict, glossary: dict) -> dict:
    """Referenced glossary entries only, ready to inject for the page lightbox."""
    return {key: glossary[key] for key in sorted(referenced_topics(lesson)) if key in glossary}


def _section_meta(kind: str, block: dict) -> dict:
    base = SECTIONS[kind]
    return {
        "kicker": block.get("kicker", base["kicker"]),
        "title": block.get("title", base["title"]),
        "rail": block.get("railLabel", block.get("title", base["rail"])),
    }


def _hero(lesson: dict, day: int, total: int) -> str:
    hero = lesson.get("hero") or {}
    readout = hero.get("readout") or {}
    pills = []
    for pill in hero.get("pills") or []:
        if isinstance(pill, dict):
            cls = "pill is-key" if pill.get("key") else "pill"
            pills.append(f'<span class="{cls}">{esc(pill.get("text"))}</span>')
        else:
            pills.append(f'<span class="pill">{esc(pill)}</span>')
    instrument = esc(hero.get("instrument", "sounder"))
    code = esc(lesson["lessonCode"])
    prompt = (
        f"I am doing TinySkiff lesson {lesson['lessonCode']}. Pull the lesson "
        "packet, then guide me one step at a time. Ask me to confirm each "
        "physical step before moving on. Explain any term I ask about in "
        "beginner-friendly language."
    )
    return f"""    <header class="hero">
      <div class="hero-copy">
        <p class="eyebrow">{esc(COURSE_TITLE)} · Day {day} of {total}</p>
        <h1>{headline_html(hero.get("headline", lesson["title"]))}</h1>
        <p class="lede">{esc(hero.get("lede", lesson.get("mission")))}</p>
        <div class="meta-row" aria-label="Lesson facts">
          {"".join(pills)}
        </div>
      </div>
      <div class="hero-side">
        <div class="sounder" data-instrument="{instrument}" role="img" aria-label="Animated depth sounder: a sensor sends pings toward a target and reads back a live distance in centimetres.">
          <div class="sounder-head"><span>{esc(hero.get("instrumentTitle", "Live instrument"))}</span><span class="dot" aria-hidden="true"></span></div>
          <div class="sounder-stage" aria-hidden="true">
            <span class="sounder-sensor"></span>
            <span class="ping"></span><span class="ping"></span><span class="ping"></span>
            <span class="sounder-target" id="sounderTarget"></span>
          </div>
          <div class="sounder-readout">
            <span class="label">{esc(readout.get("label", "Reading"))}</span>
            <span class="value" id="sounderValue">{esc(readout.get("value", "0"))}<small>{esc(readout.get("unit", ""))}</small></span>
          </div>
        </div>
        <div class="agent-strip">
          <div class="lesson-code">
            <span class="label">Agent assist code</span>
            <code>{code}</code>
          </div>
          <button class="copy-prompt" type="button" data-copy="{esc(prompt)}">Copy the coaching prompt</button>
          <p class="agent-note">Hand this to an agent so it can pull the <a href="../packets/{code}.json">lesson packet</a> and coach you step by step.</p>
        </div>
      </div>
    </header>"""


def _rail(sections: list[tuple[str, dict]], day: int, total: int) -> str:
    fill = round(day / total * 100, 2)
    links = "\n".join(
        f'          <a href="#{kind}"><span class="tick"></span>{esc(meta["rail"])}</a>'
        for kind, meta in sections
    )
    return f"""      <nav class="rail" aria-label="Lesson progress">
        <div class="rail-head">
          <strong>Today's route</strong>
          <span class="day-of">{day} / {total}</span>
        </div>
        <div class="voyage" style="--voyage-fill: {fill}%" aria-hidden="true"><span></span></div>
        <div class="rail-nav">
{links}
        </div>
      </nav>"""


def _section_head(index: int, meta: dict, intro: str) -> str:
    intro_html = f'\n              <p class="muted">{inline(intro)}</p>' if intro else ""
    return f"""            <div class="section-head">
              <p class="section-kicker"><span class="section-index">{index:02d}</span> {esc(meta["kicker"])}</p>
              <h2>{esc(meta["title"])}</h2>{intro_html}
            </div>"""


def _parts_section(index: int, block: dict) -> str:
    meta = _section_meta("parts", block)
    cards = []
    for item in block.get("items") or []:
        chip = _chip(item)
        cards.append(f"""              <article class="part-card">
                <figure class="part-photo"><img src="../assets/{esc(item["image"])}" alt="{esc(item["alt"])}" /><figcaption>{esc(item["imageKind"])}</figcaption></figure>
                <h3>{esc(item["name"])}{chip}</h3>
                <p>{inline(item["blurb"])}</p>
              </article>""")
    return f"""        <section id="parts" class="card">
          <div class="card-inner">
{_section_head(index, meta, block.get("intro", ""))}
            <div class="part-grid">
{chr(10).join(cards)}
            </div>
          </div>
        </section>"""


def _wiring_section(index: int, block: dict) -> str:
    meta = _section_meta("wiring", block)
    diagram = block.get("diagram") or {}
    img = esc(diagram.get("image"))
    rows = []
    for pin in block.get("pins") or []:
        chip = _chip(pin)
        rows.append(f"""                <div class="pin-row">
                  <span class="pin-name"><span class="pin-dot"></span>{esc(pin["from"])}{chip}</span>
                  <span class="pin-arrow">→</span><span class="pin-dest">{esc(pin["to"])}</span>
                  <span class="pin-why">{inline(pin["why"])}</span>
                </div>""")
    callouts = []
    for note in block.get("safety") or []:
        callouts.append(f"""            <div class="callout">
              <div class="icon" aria-hidden="true">{esc(note.get("icon", "⚓"))}</div>
              <p><strong>{esc(note.get("label"))}</strong> {inline(note.get("body"))}</p>
            </div>""")
    return f"""        <section id="wiring" class="card">
          <div class="card-inner">
{_section_head(index, meta, block.get("intro", ""))}
            <div class="wire-layout">
              <figure class="image-frame">
                <button class="zoom" type="button" data-zoom="../assets/{img}" data-cap="{esc(diagram.get("zoomCaption", diagram.get("caption")))}">
                  <img src="../assets/{img}" alt="{esc(diagram.get("alt"))}" />
                  <span class="zoom-hint">Click to enlarge</span>
                </button>
                <figcaption class="caption">{esc(diagram.get("caption"))}</figcaption>
              </figure>
              <div class="pin-table" aria-label="Wiring">
{chr(10).join(rows)}
              </div>
            </div>
{chr(10).join(callouts)}
          </div>
        </section>"""


def _steps_section(index: int, block: dict) -> str:
    meta = _section_meta("steps", block)
    items = block.get("items") or []
    lis = []
    for i, step in enumerate(items, start=1):
        lis.append(f"""              <li class="step"><button class="box" type="button" aria-pressed="false" aria-label="Mark step {i} done"></button><p class="text">{inline(step)}</p></li>""")
    done = block.get("done") or {}
    banner = ""
    if done:
        banner = f"""            <div class="done-banner" id="doneBanner" role="status">
              <span class="icon" aria-hidden="true">{esc(done.get("icon", "🌊"))}</span>
              <div><strong>{esc(done.get("title"))}</strong><p>{esc(done.get("body"))}</p></div>
            </div>"""
    return f"""        <section id="steps" class="card">
          <div class="card-inner">
{_section_head(index, meta, block.get("intro", ""))}
            <div class="steps-progress">
              <div class="bar" aria-hidden="true"><span id="stepBar"></span></div>
              <span class="count" id="stepCount">0 / {len(items)} done</span>
            </div>
            <ol class="step-list">
{chr(10).join(lis)}
            </ol>
{banner}
          </div>
        </section>"""


def _code_notes(notes: list) -> str:
    out = []
    for note in notes or []:
        chip = _chip(note)
        out.append(f"""                  <div class="code-note"><code>{esc(note.get("code"))}</code><span class="note-text">{inline(note.get("text"))}{chip}</span></div>""")
    return "\n".join(out)


def _code_section(index: int, block: dict) -> str:
    meta = _section_meta("code", block)
    arduino = block.get("arduino") or {}
    micro = block.get("micropython")
    tabs = ['<button class="tab" id="tab-arduino" role="tab" aria-selected="true" aria-controls="panel-arduino">Arduino <span class="badge">Main</span></button>']
    if micro:
        tabs.append('<button class="tab" id="tab-micropython" role="tab" aria-selected="false" aria-controls="panel-micropython">MicroPython <span class="badge">Optional</span></button>')
    arduino_panel = f"""            <div class="tabpanel" id="panel-arduino" role="tabpanel" aria-labelledby="tab-arduino">
              <div class="code-panel">
                <div class="code-titlebar"><span class="lights" aria-hidden="true"><i></i><i></i><i></i></span><span class="file">{esc(arduino.get("file"))}</span></div>
<pre><code>{highlight(arduino.get("excerpt", "").rstrip(chr(10)))}</code></pre>
                <div class="code-notes">
{_code_notes(arduino.get("notes"))}
                </div>
              </div>
            </div>"""
    micro_panel = ""
    if micro:
        micro_panel = f"""            <div class="tabpanel" id="panel-micropython" role="tabpanel" aria-labelledby="tab-micropython" hidden>
              <p class="optional-tag">{esc(micro.get("optionalTag", "Optional side path · same circuit"))}</p>
              <div class="code-panel">
                <div class="code-titlebar"><span class="lights" aria-hidden="true"><i></i><i></i><i></i></span><span class="file">{esc(micro.get("file"))}</span></div>
<pre><code>{highlight(micro.get("excerpt", "").rstrip(chr(10)))}</code></pre>
                <div class="code-notes">
{_code_notes(micro.get("notes"))}
                </div>
              </div>
              <p class="micropython-note">{inline(micro.get("note"))}</p>
            </div>"""
    return f"""        <section id="code" class="card">
          <div class="card-inner">
{_section_head(index, meta, block.get("intro", ""))}
            <div class="tabs" role="tablist" aria-label="Code language">
              {"".join(tabs)}
            </div>
{arduino_panel}
{micro_panel}
          </div>
        </section>"""


def _theory_section(index: int, block: dict) -> str:
    meta = _section_meta("theory", block)
    flow = []
    for step in block.get("flow") or []:
        flow.append(f"""              <article class="flow-step"><span class="n">{esc(step.get("n"))}</span><h3>{esc(step.get("title"))}</h3><p>{esc(step.get("body"))}</p></article>""")
    minis = []
    for note in block.get("notes") or []:
        chip = _chip(note)
        minis.append(f"""              <article class="mini-card"><h3>{esc(note.get("title"))}{chip}</h3><p>{inline(note.get("body"))}</p></article>""")
    minis_html = ""
    if minis:
        minis_html = f"""            <div class="two-col" style="margin-top:14px">
{chr(10).join(minis)}
            </div>"""
    return f"""        <section id="theory" class="card">
          <div class="card-inner">
{_section_head(index, meta, block.get("intro", ""))}
            <div class="theory-flow" aria-label="Measurement model">
{chr(10).join(flow)}
            </div>
            <div class="formula-card">
              <span class="label">{esc(block.get("formulaLabel", "Useful model"))}</span>
              <code>{formula_html(block.get("formula", ""))}</code>
            </div>
{minis_html}
          </div>
        </section>"""


def _test_section(index: int, block: dict) -> str:
    meta = _section_meta("test", block)
    lines = "".join(f"<span>{esc(line)}</span>" for line in block.get("expected") or [])
    checks = []
    for check in block.get("checks") or []:
        checks.append(f"""                  <li><strong>{esc(check.get("symptom"))}</strong> {inline(check.get("fix"))}</li>""")
    note = block.get("expectedNote")
    note_html = f'\n                <p class="micropython-note">{esc(note)}</p>' if note else ""
    return f"""        <section id="test" class="card">
          <div class="card-inner">
{_section_head(index, meta, block.get("intro", ""))}
            <div class="test-grid">
              <div>
                <span class="readout-title">{esc(block.get("expectedTitle", "What you should see"))}</span>
                <div class="serial" aria-label="Expected Serial Monitor output">
                  <div class="bar"><span>Serial Monitor</span><span class="baud">{esc(block.get("baud", ""))} baud</span></div>
                  <div class="lines">{lines}</div>
                </div>{note_html}
              </div>
              <div>
                <span class="checks-title">{esc(block.get("checksTitle", "If it doesn't"))}</span>
                <ul class="checklist">
{chr(10).join(checks)}
                </ul>
              </div>
            </div>
          </div>
        </section>"""


def _challenge_section(index: int, block: dict) -> str:
    meta = _section_meta("challenge", block)
    cards = []
    for card in block.get("cards") or []:
        chip = _chip(card)
        cards.append(f"""              <article class="mini-card"><h3>{esc(card.get("title"))}{chip}</h3><p>{inline(card.get("body"))}</p></article>""")
    prompts = []
    for prompt in block.get("logbook") or []:
        prompts.append(f"""              <label>{esc(prompt)}<textarea rows="2"></textarea></label>""")
    return f"""        <section id="challenge" class="card">
          <div class="card-inner">
{_section_head(index, meta, block.get("intro", ""))}
            <div class="two-col">
{chr(10).join(cards)}
            </div>
            <div class="logbook">
              <p class="logbook-head"><span aria-hidden="true">✍️</span> Logbook</p>
{chr(10).join(prompts)}
            </div>
          </div>
        </section>"""


def _agent_section(index: int, block: dict, code: str) -> str:
    meta = _section_meta("agent", block)
    return f"""        <section id="agent" class="card">
          <div class="card-inner">
{_section_head(index, meta, block.get("intro", ""))}
            <div class="agent-grid">
              <article class="mini-card"><h3>Lesson code</h3><p><code>{esc(code)}</code></p></article>
              <article class="mini-card"><h3>Context packet</h3><p><a href="../packets/{esc(code)}.json">Open the JSON packet →</a></p></article>
            </div>
            <div class="callout" style="border-color:rgba(14,124,139,0.28);background:var(--depth-wash)">
              <div class="icon" aria-hidden="true" style="background:#cfe6e6">🧭</div>
              <p><strong>How the agent should behave:</strong> {inline(block.get("behaviour"))}</p>
            </div>
          </div>
        </section>"""


def _colophon(lesson: dict, day: int, total: int) -> str:
    code_focus = lesson.get("code") or {}
    arduino = code_focus.get("arduino") or {}
    micro = code_focus.get("micropython") or {}
    diagram = (lesson.get("wiring") or {}).get("diagram") or {}
    src = diagram.get("source") or {}
    license_name = (lesson.get("source") or {}).get("license", "")
    bits = []
    if arduino.get("file"):
        bits.append(f'sketch <code>{esc(arduino["file"])}</code>')
    if micro.get("file"):
        bits.append(f'MicroPython <code>{esc(micro["file"])}</code>')
    sketch_line = ("; " + "; ".join(bits)) if bits else ""
    return f"""    <footer class="colophon">
      <p><strong>Day {day} of {total} · {esc(COURSE_TITLE)}.</strong> <a href="../">Back to the course map</a>.</p>
      <div class="rule"></div>
      <p>Circuit diagram and code based on official Freenove Super Starter Kit for ESP32-S3 material — {esc(src.get("pdf"))}, Chapter {esc(src.get("chapter"))}, page {esc(src.get("page"))}{sketch_line}. Released under {esc(license_name)}. TinySkiff is not affiliated with or endorsed by Freenove.</p>
    </footer>"""


def _day_nav(prev_day: dict | None, next_day: dict | None) -> str:
    if not prev_day and not next_day:
        return ""
    if prev_day:
        prev_html = f"""        <a class="day-nav-link prev" href="../{esc(prev_day['slug'])}/">
          <span class="day-nav-dir">← Day {prev_day['day']}</span>
          <span class="day-nav-title">{esc(prev_day['title'])}</span>
        </a>"""
    else:
        prev_html = '        <span class="day-nav-link is-empty" aria-hidden="true"></span>'
    if next_day:
        next_html = f"""        <a class="day-nav-link next" href="../{esc(next_day['slug'])}/">
          <span class="day-nav-dir">Day {next_day['day']} →</span>
          <span class="day-nav-title">{esc(next_day['title'])}</span>
        </a>"""
    else:
        next_html = '        <span class="day-nav-link is-empty" aria-hidden="true"></span>'
    return f"""        <nav class="day-nav" aria-label="Course navigation">
{prev_html}
{next_html}
        </nav>"""


def render_lesson(lesson: dict, glossary: dict, order: list[dict],
                  published: dict[int, dict]) -> str:
    """Render one lesson to a full standalone page (docs/course/day-NN-slug/index.html).

    ``published`` maps day number -> {day, slug, title} for every day that has a
    generated page. Prev/next resolve to the nearest *published* neighbours so a
    lesson never links to a day that hasn't been built yet.
    """
    day = lesson["day"]
    total = len(order)
    code = lesson["lessonCode"]
    pub_days = sorted(published)
    prev_day = next((published[d] for d in reversed(pub_days) if d < day), None)
    next_day = next((published[d] for d in pub_days if d > day), None)

    # Rail + sections, in fixed order, skipping absent blocks.
    present = [(kind, _section_meta(kind, lesson.get(kind) or {}))
               for kind in SECTION_ORDER if lesson.get(kind)]

    renderers = {
        "parts": _parts_section, "wiring": _wiring_section, "steps": _steps_section,
        "code": _code_section, "theory": _theory_section, "test": _test_section,
        "challenge": _challenge_section,
        # agent takes the lesson code too, adapted to the uniform (index, block) call
        "agent": lambda n, block: _agent_section(n, block, code),
    }
    body_sections = [
        renderers[kind](n, lesson.get(kind) or {})
        for n, (kind, _meta) in enumerate(present, start=1)
    ]

    data = {
        "day": day,
        "totalDays": total,
        "slug": lesson["slug"],
        "explainers": _resolve_explainers(lesson, glossary),
        "prev": prev_day,
        "next": next_day,
    }
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")

    seo = lesson.get("seoDescription") or lesson.get("mission") or ""
    page_title = f"Day {day} · {lesson['title']} — {COURSE_TITLE}"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{esc(page_title)}</title>
  <meta name="description" content="{esc(' '.join(str(seo).split()))}" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400..600;1,9..144,400..600&family=Inter:wght@400;500;600;700&family=Spline+Sans+Mono:wght@400;500;600&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="../course.css" />
</head>
<body>
  <div class="lesson-shell">
{_hero(lesson, day, total)}
    <div class="layout">
{_rail(present, day, total)}
      <main class="lesson-main">
{chr(10).join(body_sections)}
{_day_nav(prev_day, next_day)}
      </main>
    </div>
{_colophon(lesson, day, total)}
  </div>

  <dialog class="lightbox" id="explainer">
    <div class="lb-head">
      <div>
        <span class="lb-kicker">Field note</span>
        <h3 id="explainerTitle"></h3>
      </div>
      <button class="lb-close" type="button" data-close aria-label="Close">×</button>
    </div>
    <div class="lb-body"><p id="explainerBody"></p></div>
    <div class="lb-shortcut"><span class="tag">Shortcut</span><span id="explainerShortcut"></span></div>
  </dialog>

  <dialog class="lightbox image" id="imageBox">
    <button class="lb-close" type="button" data-close aria-label="Close">×</button>
    <div class="lb-body"><img id="imageBoxImg" alt="" /></div>
    <p class="lb-cap" id="imageBoxCap"></p>
  </dialog>

  <div class="toast" id="toast">Prompt copied</div>

  <script id="lesson-data" type="application/json">{payload}</script>
  <script src="../course.js"></script>
</body>
</html>
"""


# --------------------------------------------------------------------------
# Course map (the voyage)
# --------------------------------------------------------------------------
def course_day_order(course: dict) -> list[dict]:
    """Flatten the arc spine into an ordered list of day stubs."""
    order = []
    for arc in course.get("arcs") or []:
        for day in arc.get("days") or []:
            order.append(day)
    return sorted(order, key=lambda d: d["day"])


def render_course_index(course: dict, lessons: list[Lesson]) -> str:
    """Render the /course/ voyage map: every day, grouped by arc."""
    published = {
        ls.data["day"]: ls.data
        for ls in lessons
        if ls.data.get("status") == "published"
    }
    total = course.get("totalDays", 30)
    done_count = len(published)

    arcs_html = []
    for arc in course.get("arcs") or []:
        tiles = []
        for day in arc.get("days") or []:
            n = day["day"]
            lesson = published.get(n)
            if lesson:
                mins = lesson.get("estimatedTimeMinutes", "")
                tiles.append(f"""          <a class="day-tile is-ready" href="{esc(day['slug'])}/" data-day="{n}">
            <span class="day-tile-num">Day {n}</span>
            <span class="day-tile-tick" aria-hidden="true"></span>
            <span class="day-tile-title">{esc(lesson.get('title', day['title']))}</span>
            <span class="day-tile-meta">About {esc(mins)} min · Ready</span>
          </a>""")
            else:
                tiles.append(f"""          <div class="day-tile is-upcoming" data-day="{n}" aria-disabled="true">
            <span class="day-tile-num">Day {n}</span>
            <span class="day-tile-title">{esc(day['title'])}</span>
            <span class="day-tile-meta">Upcoming</span>
          </div>""")
        arcs_html.append(f"""      <section class="arc">
        <div class="arc-head">
          <h2>{esc(arc.get('name'))}</h2>
          <p>{esc(arc.get('subtitle', ''))}</p>
        </div>
        <div class="day-grid">
{chr(10).join(tiles)}
        </div>
      </section>""")

    data = {
        "totalDays": total,
        "published": sorted(published.keys()),
        "slugs": {str(n): ls["slug"] for n, ls in published.items()},
    }
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>The voyage — {esc(COURSE_TITLE)}</title>
  <meta name="description" content="A guided 30-day, Arduino-first course for the Freenove Super Starter Kit for ESP32-S3. Each day is a complete win in about 30 minutes." />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400..600;1,9..144,400..600&family=Inter:wght@400;500;600;700&family=Spline+Sans+Mono:wght@400;500;600&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="./course.css" />
</head>
<body>
  <div class="lesson-shell">
    <header class="hero map-hero">
      <div class="hero-copy">
        <p class="eyebrow">{esc(COURSE_TITLE)}</p>
        <h1>The <em>voyage</em></h1>
        <p class="lede">A guided 30-day, Arduino-first course. Each day is one complete win in about 30 minutes — wire it, run it, understand it, then try one small thing of your own.</p>
        <div class="meta-row" aria-label="Course facts">
          <span class="pill is-key">30 days</span>
          <span class="pill">Arduino first</span>
          <span class="pill">No electronics assumed</span>
          <a class="pill pill-link" href="../index.html">Browse the Library →</a>
        </div>
      </div>
      <div class="hero-side">
        <div class="map-progress" id="mapProgress">
          <div class="map-progress-head"><span>Your voyage</span><span class="dot" aria-hidden="true"></span></div>
          <div class="map-progress-body">
            <span class="map-progress-count"><b id="doneCount">0</b> / {total} days done</span>
            <div class="voyage" id="mapVoyage"><span></span></div>
            <a class="map-resume" id="mapResume" href="#" hidden>Resume →</a>
          </div>
        </div>
      </div>
    </header>
    <main class="course-body">
      <p class="map-note muted">{done_count} of {total} days are ready to sail. The rest are charted and on the way.</p>
{chr(10).join(arcs_html)}
    </main>
    <footer class="colophon">
      <p><strong>{esc(COURSE_TITLE)}.</strong> A guided course built on the official Freenove Super Starter Kit for ESP32-S3 material, released under CC BY-NC-SA 3.0. Not affiliated with or endorsed by Freenove.</p>
    </footer>
  </div>
  <script id="course-data" type="application/json">{payload}</script>
  <script src="./course.js"></script>
</body>
</html>
"""


# --------------------------------------------------------------------------
# Agent packet (v0 projection)
# --------------------------------------------------------------------------
def emit_packet(lesson: dict, glossary: dict) -> dict:
    """Project a lesson down to the shipped tinyskiff.lessonPacket.v0 shape."""
    code_focus = lesson.get("code") or {}
    arduino = code_focus.get("arduino") or {}
    micro = code_focus.get("micropython") or {}
    diagram = (lesson.get("wiring") or {}).get("diagram") or {}
    src = diagram.get("source") or {}
    theory = lesson.get("theory") or {}
    test = lesson.get("test") or {}
    source = lesson.get("source") or {}

    def part_expl(part: dict) -> str:
        key = part.get("explain")
        if key and key in glossary:
            return str(glossary[key].get("body", "")).strip()
        return plain_text(part.get("blurb"))

    chapter = None
    if src.get("chapter"):
        chapter = f"Chapter {src['chapter']}"
        if src.get("chapterTitle"):
            chapter += f" {src['chapterTitle']}"
    source_meta = {
        "officialPdf": f"{SOURCE_PREFIX}/C/{src.get('pdf')}" if src.get("pdf") else None,
        "chapter": chapter,
        "page": src.get("page"),
    }
    if arduino.get("sketch"):
        source_meta["arduinoSketch"] = f"{SOURCE_PREFIX}/{arduino['sketch']}"
    if arduino.get("variant"):
        source_meta["arduinoVariant"] = f"{SOURCE_PREFIX}/{arduino['variant']}"
    if micro.get("path"):
        source_meta["micropythonFile"] = f"{SOURCE_PREFIX}/{micro['path']}"
    if diagram.get("image"):
        source_meta["imageAsset"] = f"docs/course/assets/{diagram['image']}"
    source_meta["imageAlt"] = diagram.get("alt")
    source_meta["licenseNote"] = source.get("licenseNote", source.get("license"))

    packet = {
        "schema": PACKET_SCHEMA,
        "lessonCode": lesson["lessonCode"],
        "course": COURSE_TITLE,
        "day": lesson["day"],
        "title": lesson["title"],
        "status": lesson.get("status"),
        "learnerProfile": lesson.get("learnerProfile"),
        "estimatedTimeMinutes": lesson.get("estimatedTimeMinutes"),
        "mission": plain_text(lesson.get("mission")),
        "mainPath": "Arduino/C++",
    }
    if micro:
        packet["optionalSidePath"] = "MicroPython"
    packet["sourceMetadata"] = {k: v for k, v in source_meta.items() if v is not None}
    packet["parts"] = [
        {"name": p.get("name"), "imageAsset": f"docs/course/assets/{p.get('image')}",
         "explanation": part_expl(p)}
        for p in (lesson.get("parts") or {}).get("items") or []
    ]
    packet["wiring"] = [
        {"partPin": pin.get("from"), "connectTo": pin.get("to"), "reason": plain_text(pin.get("why"))}
        for pin in (lesson.get("wiring") or {}).get("pins") or []
    ]
    packet["coachInstructions"] = list((lesson.get("agent") or {}).get("coachInstructions") or [])
    packet["steps"] = [plain_text(s) for s in (lesson.get("steps") or {}).get("items") or []]
    packet["codeFocus"] = {}
    if arduino.get("notes"):
        packet["codeFocus"]["arduino"] = [
            {"line": n.get("code"), "explanation": plain_text(n.get("text"))}
            for n in arduino["notes"]
        ]
    if micro.get("notes"):
        packet["codeFocus"]["micropython"] = [
            {"line": n.get("code"), "explanation": plain_text(n.get("text"))}
            for n in micro["notes"]
        ]
    packet["theoryModel"] = {
        "plainLanguage": plain_text(theory.get("summary"))
        or "; ".join(str(f.get("title")) for f in theory.get("flow") or []),
        "formula": plain_text(theory.get("formula")),
        "notes": [{"title": n.get("title"), "body": plain_text(n.get("body"))}
                  for n in theory.get("notes") or []],
    }
    packet["test"] = {
        "expectedOutputExample": list(test.get("expected") or []),
        "successCriteria": plain_text(test.get("expectedNote")),
    }
    packet["troubleshooting"] = [
        {"symptom": plain_text(c.get("symptom")).rstrip("?"), "firstChecks": [plain_text(c.get("fix"))]}
        for c in test.get("checks") or []
    ]
    packet["challenge"] = plain_text((lesson.get("challenge") or {}).get("summary"))
    packet["logbookPrompts"] = list((lesson.get("challenge") or {}).get("logbook") or [])
    return packet


# --------------------------------------------------------------------------
# Library backlinks
# --------------------------------------------------------------------------
def derive_backlinks(lessons: list[Lesson]) -> dict:
    """Map a full sketch source path to the day that teaches it.

    Keyed by the same relative path build_site uses for Library sketch folders
    (relative to the source kit root), so the Library can show "Taught in Day N".
    """
    backlinks: dict[str, dict] = {}
    for ls in lessons:
        data = ls.data
        if data.get("status") != "published":
            continue  # only link to days that actually have a generated page
        arduino = (data.get("code") or {}).get("arduino") or {}
        sketch = arduino.get("sketch")
        if not sketch:
            continue
        folder = str(Path(sketch).parent).replace("\\", "/")
        backlinks[folder] = {"day": data["day"], "slug": data["slug"], "title": data["title"]}
    return backlinks


# --------------------------------------------------------------------------
# Asset copy
# --------------------------------------------------------------------------
def copy_course_assets(course_out: Path) -> None:
    """Copy the productised design system + image assets into docs/course/."""
    course_out.mkdir(parents=True, exist_ok=True)
    for name in ("course.css", "course.js"):
        shutil.copy2(COURSE_ASSETS / name, course_out / name)
    src_assets = COURSE_ASSETS / "assets"
    if src_assets.exists():
        shutil.copytree(src_assets, course_out / "assets", dirs_exist_ok=True)
