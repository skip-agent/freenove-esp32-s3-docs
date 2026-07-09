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
    # Code fields may legitimately contain brace syntax (f-strings, `loop(){}`),
    # which is not a glossary reference — don't scan those string values.
    code_string_keys = {"excerpt", "code"}

    def walk(node) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key in skip_keys:
                    continue
                if key == "explain" and isinstance(value, str):
                    topics.add(value)
                elif key in code_string_keys and isinstance(value, str):
                    continue  # a code snippet, not prose
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


def _as_dict(node) -> dict:
    """A block coerced to a mapping (non-mappings validate as missing fields)."""
    return node if isinstance(node, dict) else {}


def _as_list(node) -> list:
    """A block coerced to a list (non-lists validate as empty)."""
    return node if isinstance(node, list) else []


def _nonempty(value) -> bool:
    """True only for a real, non-blank string.

    A blank YAML field (``alt:``) loads as None; ``str(None).strip()`` would be
    the truthy ``"None"``, so required-text checks must go through this helper.
    """
    return isinstance(value, str) and bool(value.strip())


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
    code_match = re.match(r"^TSK-DAY(\d{2})-", str(lesson.get("lessonCode", "")))
    if code_match and isinstance(day, int):
        _require(errors, code_match.group(1) == f"{day:02d}",
                 f"{code}: lessonCode day {code_match.group(1)} does not match day {day}")
    for field in ("title", "mission", "learnerProfile", "unlocks"):
        _require(errors, _nonempty(lesson.get(field)),
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

    def _require_mapping(node, where: str) -> bool:
        """Guard that a list item is a mapping before .get is used on it."""
        if isinstance(node, dict):
            return True
        err(f"{where} must be a mapping")
        return False

    # Parts — each needs an image + alt (provenance) + name
    parts = _as_list(_as_dict(lesson.get("parts")).get("items"))
    _require(errors, len(parts) > 0, f"{code}: parts.items must be non-empty")
    for i, part in enumerate(parts):
        where = f"parts.items[{i}]"
        if not _require_mapping(part, where):
            continue
        for field in ("name", "image", "imageKind", "blurb", "alt"):
            _require(errors, _nonempty(part.get(field)),
                     f"{code}: {where}.{field} is required")

    # Wiring — diagram carries alt + source; pins have from/to/why
    wiring = _as_dict(lesson.get("wiring"))
    diagram = _as_dict(wiring.get("diagram"))
    for field in ("image", "alt", "caption"):
        _require(errors, _nonempty(diagram.get(field)),
                 f"{code}: wiring.diagram.{field} is required")
    src = _as_dict(diagram.get("source"))
    for field in ("pdf", "chapter", "page"):
        _require(errors, src.get(field) not in (None, ""),
                 f"{code}: wiring.diagram.source.{field} is required")
    pins = _as_list(wiring.get("pins"))
    _require(errors, len(pins) > 0, f"{code}: wiring.pins must be non-empty")
    for i, pin in enumerate(pins):
        if not _require_mapping(pin, f"wiring.pins[{i}]"):
            continue
        for field in ("from", "to", "why"):
            _require(errors, _nonempty(pin.get(field)),
                     f"{code}: wiring.pins[{i}].{field} is required")

    # Steps
    steps = _as_list(_as_dict(lesson.get("steps")).get("items"))
    _require(errors, len(steps) > 0, f"{code}: steps.items must be non-empty")

    # Code focus — Arduino is required; MicroPython optional
    arduino = _as_dict(_as_dict(lesson.get("code")).get("arduino"))
    for field in ("sketch", "excerpt"):
        _require(errors, _nonempty(arduino.get(field)),
                 f"{code}: code.arduino.{field} is required")

    # Theory is optional (setup days may have none), but must be complete if present
    theory = lesson.get("theory")
    if theory is not None:
        theory = _as_dict(theory)
        _require(errors, len(_as_list(theory.get("flow"))) > 0,
                 f"{code}: theory.flow must be non-empty when theory is present")
        _require(errors, _nonempty(theory.get("formula")),
                 f"{code}: theory.formula is required when theory is present")

    # Test
    test = _as_dict(lesson.get("test"))
    _require(errors, len(_as_list(test.get("expected"))) > 0,
             f"{code}: test.expected must be non-empty")
    _require(errors, len(_as_list(test.get("checks"))) > 0,
             f"{code}: test.checks must be non-empty")

    # Challenge + logbook
    challenge = _as_dict(lesson.get("challenge"))
    _require(errors, _nonempty(challenge.get("title")),
             f"{code}: challenge.title is required")
    _require(errors, _nonempty(challenge.get("summary")),
             f"{code}: challenge.summary is required (feeds the agent packet)")
    _require(errors, len(_as_list(challenge.get("logbook"))) > 0,
             f"{code}: challenge.logbook must be non-empty")

    # Agent packet
    agent = _as_dict(lesson.get("agent"))
    _require(errors, len(_as_list(agent.get("coachInstructions"))) > 0,
             f"{code}: agent.coachInstructions must be non-empty")

    # Provenance / license
    source = _as_dict(lesson.get("source"))
    _require(errors, _nonempty(source.get("license")),
             f"{code}: source.license is required")

    # Shape guard — every list/sub-block the renderer dereferences with .get must
    # hold mappings, so a malformed authoring shape fails here with a clear error
    # rather than crashing render (the build aborts on any error before rendering).
    micro = _as_dict(_as_dict(lesson.get("code")).get("micropython"))
    for name, sub in (("hero", lesson.get("hero")),
                      ("hero.readout", _as_dict(lesson.get("hero")).get("readout")),
                      ("steps.done", _as_dict(lesson.get("steps")).get("done")),
                      ("code.micropython", lesson.get("code", {}).get("micropython")
                          if isinstance(lesson.get("code"), dict) else None)):
        if sub is not None and not isinstance(sub, dict):
            err(f"{name} must be a mapping")
    mapping_lists = {
        "wiring.safety": _as_list(wiring.get("safety")),
        "code.arduino.notes": _as_list(arduino.get("notes")),
        "code.micropython.notes": _as_list(micro.get("notes")),
        "test.checks": _as_list(test.get("checks")),
        "challenge.cards": _as_list(challenge.get("cards")),
        "hero.pills": [p for p in _as_list(_as_dict(lesson.get("hero")).get("pills"))
                       if not isinstance(p, str)],  # strings are allowed here
    }
    if theory is not None:
        theory_d = _as_dict(theory)
        mapping_lists["theory.flow"] = _as_list(theory_d.get("flow"))
        mapping_lists["theory.notes"] = _as_list(theory_d.get("notes"))
    for name, items in mapping_lists.items():
        for i, item in enumerate(items):
            _require_mapping(item, f"{name}[{i}]")

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
    for part in _as_list(_as_dict(lesson.get("parts")).get("items")):
        if isinstance(part, dict) and part.get("image"):
            paths.append(str(part["image"]))
    diagram = _as_dict(_as_dict(lesson.get("wiring")).get("diagram"))
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


def validate_against_course(lessons: list[Lesson], course: dict) -> list[str]:
    """Every lesson's (day, slug) must match its entry in the course spine.

    The course map links tiles by spine day; the page is written at the lesson
    slug. If they drift, the map would 404 — catch it at build time.
    """
    errors: list[str] = []
    spine: dict[int, str] = {}
    for arc in course.get("arcs") or []:
        for day in arc.get("days") or []:
            spine[day.get("day")] = day.get("slug")
    for lesson in lessons:
        day = lesson.data.get("day")
        slug = lesson.data.get("slug")
        code = lesson.data.get("lessonCode", lesson.path.name)
        if day not in spine:
            errors.append(f"{code}: day {day} is not in the course spine (_course.yml)")
        elif spine[day] != slug:
            errors.append(
                f"{code}: slug {slug!r} does not match the spine slug {spine[day]!r} for day {day}"
            )
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
    problems.extend(validate_against_course(lessons, load_course()))

    if problems:
        raise LessonError(
            "lesson validation failed:\n  - " + "\n  - ".join(problems)
        )
    return lessons
