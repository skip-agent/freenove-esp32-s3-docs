#!/usr/bin/env python3
"""Tests for the course machine: schema/validator, rendering, and the packet.

Run with the repo venv:  .venv/bin/python -m unittest discover -s scripts/tests
"""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import course_build  # noqa: E402
import lesson_schema  # noqa: E402


def load_day26() -> dict:
    lessons = lesson_schema.load_lessons()
    for ls in lessons:
        if ls.data.get("lessonCode") == "TSK-DAY26-ULTRASONIC":
            return copy.deepcopy(ls.data)
    raise AssertionError("Day 26 lesson not found")


GLOSSARY = lesson_schema.load_glossary()
GLOSSARY_KEYS = set(GLOSSARY)
COURSE = lesson_schema.load_course()
ORDER = course_build.course_day_order(COURSE)


class ValidationTests(unittest.TestCase):
    def test_day26_is_valid(self):
        errors = lesson_schema.validate_lesson(load_day26(), GLOSSARY_KEYS)
        self.assertEqual(errors, [], f"Day 26 should validate cleanly: {errors}")

    def test_over_length_day_fails(self):
        lesson = load_day26()
        lesson["estimatedTimeMinutes"] = 45
        errors = lesson_schema.validate_lesson(lesson, GLOSSARY_KEYS)
        self.assertTrue(any("estimatedTimeMinutes" in e for e in errors),
                        f"over-length day should fail: {errors}")

    def test_missing_part_alt_fails(self):
        lesson = load_day26()
        del lesson["parts"]["items"][0]["alt"]
        errors = lesson_schema.validate_lesson(lesson, GLOSSARY_KEYS)
        self.assertTrue(any("alt" in e for e in errors), errors)

    def test_missing_diagram_source_fails(self):
        lesson = load_day26()
        del lesson["wiring"]["diagram"]["source"]["page"]
        errors = lesson_schema.validate_lesson(lesson, GLOSSARY_KEYS)
        self.assertTrue(any("source.page" in e for e in errors), errors)

    def test_unresolved_glossary_key_fails(self):
        lesson = load_day26()
        lesson["parts"]["items"][0]["explain"] = "does-not-exist"
        errors = lesson_schema.validate_lesson(lesson, GLOSSARY_KEYS)
        self.assertTrue(any("does-not-exist" in e for e in errors), errors)

    def test_bad_track_fails(self):
        lesson = load_day26()
        lesson["tracks"]["main"] = "micropython"
        errors = lesson_schema.validate_lesson(lesson, GLOSSARY_KEYS)
        self.assertTrue(any("tracks.main" in e for e in errors), errors)

    def test_slug_must_match_day(self):
        lesson = load_day26()
        lesson["slug"] = "day-25-ultrasonic"
        errors = lesson_schema.validate_lesson(lesson, GLOSSARY_KEYS)
        self.assertTrue(any("does not match day" in e for e in errors), errors)

    def test_corpus_detects_duplicates(self):
        a = lesson_schema.Lesson(path=Path("a.yml"), data={"day": 1, "lessonCode": "X", "slug": "day-01-a"})
        b = lesson_schema.Lesson(path=Path("b.yml"), data={"day": 1, "lessonCode": "Y", "slug": "day-01-b"})
        errors = lesson_schema.validate_corpus([a, b])
        self.assertTrue(any("duplicate day" in e for e in errors), errors)

    def test_collect_lessons_passes(self):
        lessons = lesson_schema.collect_lessons()
        self.assertGreaterEqual(len(lessons), 1)

    def test_spine_slug_drift_detected(self):
        drifted = lesson_schema.Lesson(
            path=Path("day-26-ultrasonic.yml"),
            data={"day": 26, "lessonCode": "TSK-DAY26-ULTRASONIC", "slug": "day-26-wrong"},
        )
        errors = lesson_schema.validate_against_course([drifted], COURSE)
        self.assertTrue(any("does not match the spine slug" in e for e in errors), errors)

    def test_day_not_in_spine_detected(self):
        ghost = lesson_schema.Lesson(
            path=Path("day-31-x.yml"),
            data={"day": 31, "lessonCode": "TSK-DAY31-X", "slug": "day-31-x"},
        )
        errors = lesson_schema.validate_against_course([ghost], COURSE)
        self.assertTrue(any("not in the course spine" in e for e in errors), errors)


class ReferencedTopicsTests(unittest.TestCase):
    def test_inline_and_explain_topics_found(self):
        lesson = load_day26()
        topics = lesson_schema.referenced_topics(lesson)
        self.assertIn("serial", topics)   # inline {serial} in a step
        self.assertIn("hcsr04", topics)   # explain: on a part
        self.assertIn("pulsein", topics)  # explain: on a code note

    def test_headline_braces_not_topics(self):
        lesson = load_day26()
        topics = lesson_schema.referenced_topics(lesson)
        self.assertNotIn("sound", topics)  # {sound} in headline is emphasis

    def test_code_braces_not_topics(self):
        # brace syntax inside code excerpts / snippets is not a glossary key
        lesson = {
            "code": {
                "arduino": {
                    "excerpt": "server.on('/', [](){ String s = \"${streamUrl}\"; });",
                    "notes": [{"code": "loop() {}", "text": "runs forever. {serial}"}],
                },
            },
        }
        topics = lesson_schema.referenced_topics(lesson)
        self.assertNotIn("streamUrl", topics)
        self.assertIn("serial", topics)  # inline {serial} in prose text still counts


class InlineRenderTests(unittest.TestCase):
    def test_code_and_emphasis(self):
        self.assertEqual(course_build.inline("say `x`"), "say <code>x</code>")
        self.assertEqual(course_build.inline("**bold**"), "<strong>bold</strong>")
        self.assertEqual(course_build.inline("*it*"), "<em>it</em>")

    def test_define_chip(self):
        out = course_build.inline("baud. {serial}")
        self.assertIn('class="define"', out)
        self.assertIn('data-topic="serial"', out)

    def test_escaping(self):
        self.assertIn("&lt;script&gt;", course_build.inline("<script>"))

    def test_plain_text_strips_markup(self):
        out = course_build.plain_text("Set baud to `115200`. {serial}")
        self.assertNotIn("`", out)
        self.assertNotIn("{serial}", out)
        self.assertEqual(out, "Set baud to 115200.")

    def test_headline_html(self):
        out = course_build.headline_html("a|b {c}")
        self.assertIn("<br />", out)
        self.assertIn("<em>c</em>", out)

    def test_highlight_tokens(self):
        out = course_build.highlight("#define trigPin 13\npulseIn(x, HIGH)")
        self.assertIn('class="tok-key">#define', out)
        self.assertIn('class="tok-num">13', out)
        self.assertIn('class="tok-fn">pulseIn', out)
        self.assertNotIn('tok-', out.split("HIGH")[0].rsplit(">", 1)[-1] + "HIGH")  # HIGH stays plain


class RenderLessonTests(unittest.TestCase):
    def setUp(self):
        # Realistic corpus: only Day 26 is published.
        self.published = {26: {"day": 26, "slug": "day-26-ultrasonic", "title": "Measure the room with sound"}}
        self.html = course_build.render_lesson(load_day26(), GLOSSARY, ORDER, self.published)

    def test_key_markers(self):
        for needle in ["Measure the room", "Live echo sounder", "TSK-DAY26-ULTRASONIC",
                       'id="parts"', 'id="wiring"', 'id="steps"', 'id="code"',
                       'id="theory"', 'id="test"', 'id="challenge"', 'id="agent"',
                       "../course.css", "../course.js", "lesson-data"]:
            self.assertIn(needle, self.html, f"missing {needle!r}")

    def test_no_nav_to_unpublished_neighbours(self):
        # Day 26 is the only published day, so no prev/next links are emitted.
        self.assertNotIn("day-25", self.html)
        self.assertNotIn("day-27", self.html)
        self.assertNotIn('class="day-nav"', self.html)

    def test_prev_next_resolve_to_published_neighbours(self):
        published = {
            24: {"day": 24, "slug": "day-24-servo-knob", "title": "Servo knob"},
            26: {"day": 26, "slug": "day-26-ultrasonic", "title": "Measure the room with sound"},
            29: {"day": 29, "slug": "day-29-wifi", "title": "Wi-Fi modes"},
        }
        html = course_build.render_lesson(load_day26(), GLOSSARY, ORDER, published)
        # nearest published below is 24, nearest above is 29 (skips unpublished 25/27)
        self.assertIn("../day-24-servo-knob/", html)
        self.assertIn("../day-29-wifi/", html)
        self.assertNotIn("day-25", html)
        self.assertNotIn("day-27", html)

    def test_packet_link(self):
        self.assertIn("../packets/TSK-DAY26-ULTRASONIC.json", self.html)

    def test_voyage_fill(self):
        self.assertIn("--voyage-fill", self.html)

    def test_micropython_tab_present(self):
        self.assertIn('id="tab-micropython"', self.html)


class CourseIndexTests(unittest.TestCase):
    def setUp(self):
        self.lessons = lesson_schema.collect_lessons()
        self.html = course_build.render_course_index(COURSE, self.lessons)

    def test_all_days_present(self):
        for n in range(1, 31):
            self.assertIn(f'data-day="{n}"', self.html, f"day {n} missing from map")

    def test_published_day_is_linked(self):
        self.assertIn('href="day-26-ultrasonic/"', self.html)

    def test_upcoming_day_not_linked(self):
        self.assertIn("is-upcoming", self.html)


class PacketTests(unittest.TestCase):
    def setUp(self):
        self.packet = course_build.emit_packet(load_day26(), GLOSSARY)

    def test_schema_and_shape(self):
        self.assertEqual(self.packet["schema"], lesson_schema.PACKET_SCHEMA)
        self.assertEqual(self.packet["day"], 26)
        self.assertEqual(len(self.packet["parts"]), 6)
        self.assertEqual(len(self.packet["wiring"]), 4)
        self.assertEqual(len(self.packet["steps"]), 7)

    def test_steps_are_plain_text(self):
        for step in self.packet["steps"]:
            self.assertNotIn("`", step)
            self.assertNotIn("{", step)

    def test_troubleshooting_shape(self):
        first = self.packet["troubleshooting"][0]
        self.assertIn("symptom", first)
        self.assertIsInstance(first["firstChecks"], list)

    def test_source_metadata(self):
        meta = self.packet["sourceMetadata"]
        self.assertTrue(meta["arduinoSketch"].endswith("Sketch_19.1_Ultrasonic_Ranging.ino"))
        self.assertEqual(meta["page"], 172)


class BacklinkTests(unittest.TestCase):
    def test_backlink_keyed_by_sketch_folder(self):
        lessons = lesson_schema.collect_lessons()
        links = course_build.derive_backlinks(lessons)
        self.assertIn("C/Sketches/Sketch_19.1_Ultrasonic_Ranging", links)
        self.assertEqual(links["C/Sketches/Sketch_19.1_Ultrasonic_Ranging"]["day"], 26)


if __name__ == "__main__":
    unittest.main()
