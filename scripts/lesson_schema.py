#!/usr/bin/env python3
"""tinyskiff.lesson.v1 — schema loading and validation.

Shared by build_site.py (to collect + render), validate_site.py (to fail the
build on a bad day), and the test suite. Keep validation here so there is one
definition of what a valid lesson is.

A lesson file is one YAML document per day under ``lessons/``. It is a superset
of the shipped ``tinyskiff.lessonPacket.v0``: the build projects it down to that
packet, so the packet is never hand-maintained. See
``docs/wayfinder/site-content-model.md`` §2 for the annotated model.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
LESSONS_DIR = ROOT / "lessons"
GLOSSARY_FILE = LESSONS_DIR / "_glossary.yml"
COURSE_FILE = LESSONS_DIR / "_course.yml"
# Where per-lesson image assets live (source of truth, copied into docs/course).
ASSET_ROOT = ROOT / "course-assets" / "assets"

LESSON_SCHEMA = "tinyskiff.lesson.v1"
PACKET_SCHEMA = "tinyskiff.lessonPacket.v0"
COURSE_SCHEMA = "tinyskiff.course.v1"

MAX_MINUTES = 30
STATUSES = {"draft", "review", "published"}
LESSON_CODE_RE = re.compile(r"^TSK-DAY\d{2}-[A-Z0-9]+$")
SLUG_RE = re.compile(r"^day-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*$")
# Inline explainer reference inside prose, e.g. "set the baud rate. {serial}".
INLINE_TOPIC_RE = re.compile(r"\{([a-zA-Z][a-zA-Z0-9]*)\}")


class LessonError(Exception):
    """Raised when lessons fail validation; message lists every problem."""


@dataclass
class Lesson:
    path: Path
    data: dict

    @property
    def code(self) -> str:
        return str(self.data.get("lessonCode", self.path.stem))


# --------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------
def _load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        loaded = yaml.safe_load(fh)
    if not isinstance(loaded, dict):
        raise LessonError(f"{path.name}: expected a YAML mapping at the top level")
    return loaded


def load_glossary() -> dict:
    if not GLOSSARY_FILE.exists():
        raise LessonError(f"missing glossary: {GLOSSARY_FILE}")
    return _load_yaml(GLOSSARY_FILE)


def load_course() -> dict:
    if not COURSE_FILE.exists():
        raise LessonError(f"missing course spine: {COURSE_FILE}")
    return _load_yaml(COURSE_FILE)


def load_lessons() -> list[Lesson]:
    """Load every day file (``day-*.yml``), skipping the ``_`` shared files."""
    lessons = []
    for path in sorted(LESSONS_DIR.glob("day-*.yml")):
        lessons.append(Lesson(path=path, data=_load_yaml(path)))
    return lessons


# --------------------------------------------------------------------------
# Referenced glossary keys (for validation and for inlining into the packet)
# --------------------------------------------------------------------------
def referenced_topics(lesson: dict) -> set[str]:
    """Every glossary key a lesson refers to, via ``explain:`` or inline ``{key}``."""
    topics: set[str] = set()

    # `headline` uses {word} for emphasis, not a glossary reference — skip it.
    skip_keys = {"headline"}

    def walk(node) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key in skip_keys:
                    continue
                if key == "explain" and isinstance(value, str):
                    topics.add(value)
                else:
                    walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)
        elif isinstance(node, str):
            topics.update(INLINE_TOPIC_RE.findall(node))

    walk(lesson)
    return topics


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------
def _require(errors: list[str], cond: bool, msg: str) -> None:
    if not cond:
        errors.append(msg)


def validate_lesson(lesson: dict, glossary_keys: set[str]) -> list[str]:
    """Return a list of human-readable problems for one lesson (empty = valid)."""
    errors: list[str] = []
    code = lesson.get("lessonCode", "<no lessonCode>")

    def err(msg: str) -> None:
        errors.append(f"{code}: {msg}")

    # Identity
    _require(errors, lesson.get("schema") == LESSON_SCHEMA,
             f"{code}: schema must be {LESSON_SCHEMA!r}")
    _require(errors, isinstance(lesson.get("lessonCode"), str)
             and bool(LESSON_CODE_RE.match(str(lesson.get("lessonCode")))),
             f"{code}: lessonCode must match TSK-DAYNN-CODE")
    day = lesson.get("day")
    _require(errors, isinstance(day, int) and 1 <= day <= 30,
             f"{code}: day must be an integer 1–30")
    slug = lesson.get("slug", "")
    _require(errors, isinstance(slug, str) and bool(SLUG_RE.match(slug)),
             f"{code}: slug must match day-NN-name")
    if isinstance(day, int) and isinstance(slug, str) and slug:
        _require(errors, slug.startswith(f"day-{day:02d}-"),
                 f"{code}: slug {slug!r} does not match day {day}")
    for field in ("title", "mission", "learnerProfile", "unlocks"):
        _require(errors, bool(str(lesson.get(field, "")).strip()),
                 f"{code}: {field} is required")
    _require(errors, lesson.get("status") in STATUSES,
             f"{code}: status must be one of {sorted(STATUSES)}")

    # Framing
    minutes = lesson.get("estimatedTimeMinutes")
    _require(errors, isinstance(minutes, int) and 0 < minutes <= MAX_MINUTES,
             f"{code}: estimatedTimeMinutes must be an integer ≤ {MAX_MINUTES}")
    tracks = lesson.get("tracks") or {}
    _require(errors, isinstance(tracks, dict) and tracks.get("main") == "arduino",
             f"{code}: tracks.main must be 'arduino'")

    # Parts — each needs an image + alt (provenance) + name
    parts = (lesson.get("parts") or {}).get("items") or []
    _require(errors, len(parts) > 0, f"{code}: parts.items must be non-empty")
    for i, part in enumerate(parts):
        where = f"parts.items[{i}]"
        for field in ("name", "image", "imageKind", "blurb", "alt"):
            _require(errors, bool(str(part.get(field, "")).strip()),
                     f"{code}: {where}.{field} is required")

    # Wiring — diagram carries alt + source; pins have from/to/why
    wiring = lesson.get("wiring") or {}
    diagram = wiring.get("diagram") or {}
    for field in ("image", "alt", "caption"):
        _require(errors, bool(str(diagram.get(field, "")).strip()),
                 f"{code}: wiring.diagram.{field} is required")
    src = diagram.get("source") or {}
    for field in ("pdf", "chapter", "page"):
        _require(errors, src.get(field) not in (None, ""),
                 f"{code}: wiring.diagram.source.{field} is required")
    pins = wiring.get("pins") or []
    _require(errors, len(pins) > 0, f"{code}: wiring.pins must be non-empty")
    for i, pin in enumerate(pins):
        for field in ("from", "to", "why"):
            _require(errors, bool(str(pin.get(field, "")).strip()),
                     f"{code}: wiring.pins[{i}].{field} is required")

    # Steps
    steps = (lesson.get("steps") or {}).get("items") or []
    _require(errors, len(steps) > 0, f"{code}: steps.items must be non-empty")

    # Code focus — Arduino is required; MicroPython optional
    code_focus = lesson.get("code") or {}
    arduino = code_focus.get("arduino") or {}
    for field in ("sketch", "excerpt"):
        _require(errors, bool(str(arduino.get(field, "")).strip()),
                 f"{code}: code.arduino.{field} is required")

    # Test
    test = lesson.get("test") or {}
    _require(errors, len(test.get("expected") or []) > 0,
             f"{code}: test.expected must be non-empty")
    _require(errors, len(test.get("checks") or []) > 0,
             f"{code}: test.checks must be non-empty")

    # Challenge + logbook
    challenge = lesson.get("challenge") or {}
    _require(errors, bool(str(challenge.get("title", "")).strip()),
             f"{code}: challenge.title is required")
    _require(errors, bool(str(challenge.get("summary", "")).strip()),
             f"{code}: challenge.summary is required (feeds the agent packet)")
    _require(errors, len(challenge.get("logbook") or []) > 0,
             f"{code}: challenge.logbook must be non-empty")

    # Agent packet
    agent = lesson.get("agent") or {}
    _require(errors, len(agent.get("coachInstructions") or []) > 0,
             f"{code}: agent.coachInstructions must be non-empty")

    # Provenance / license
    source = lesson.get("source") or {}
    _require(errors, bool(str(source.get("license", "")).strip()),
             f"{code}: source.license is required")

    # Every referenced glossary key must resolve
    for topic in sorted(referenced_topics(lesson)):
        _require(errors, topic in glossary_keys,
                 f"{code}: glossary key {topic!r} is not defined in _glossary.yml")

    # Referenced image assets must exist on disk
    for rel in _image_paths(lesson):
        _require(errors, (ASSET_ROOT / rel).exists(),
                 f"{code}: image asset not found: course-assets/assets/{rel}")

    return errors


def _image_paths(lesson: dict) -> list[str]:
    paths: list[str] = []
    for part in (lesson.get("parts") or {}).get("items") or []:
        if part.get("image"):
            paths.append(str(part["image"]))
    diagram = (lesson.get("wiring") or {}).get("diagram") or {}
    if diagram.get("image"):
        paths.append(str(diagram["image"]))
    return paths


def validate_corpus(lessons: list[Lesson]) -> list[str]:
    """Cross-lesson invariants: unique day, lessonCode, and slug."""
    errors: list[str] = []
    for field in ("day", "lessonCode", "slug"):
        seen: dict[object, str] = {}
        for lesson in lessons:
            value = lesson.data.get(field)
            if value is None:
                continue
            if value in seen:
                errors.append(
                    f"duplicate {field} {value!r}: {seen[value]} and {lesson.path.name}"
                )
            else:
                seen[value] = lesson.path.name
    return errors


def collect_lessons() -> list[Lesson]:
    """Load and fully validate every lesson; raise LessonError on any problem."""
    glossary = load_glossary()
    glossary_keys = set(glossary.keys())
    lessons = load_lessons()

    problems: list[str] = []
    for lesson in lessons:
        problems.extend(validate_lesson(lesson.data, glossary_keys))
    problems.extend(validate_corpus(lessons))

    if problems:
        raise LessonError(
            "lesson validation failed:\n  - " + "\n  - ".join(problems)
        )
    return lessons
