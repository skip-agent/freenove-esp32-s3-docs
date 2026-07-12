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


class CourseCssTests(unittest.TestCase):
    def setUp(self):
        root = SCRIPTS.parent
        self.source = (root / "course-assets" / "course.css").read_text()
        self.generated = (root / "docs" / "course" / "course.css").read_text()

    def test_generated_course_css_matches_source(self):
        self.assertEqual(self.generated, self.source)

    def test_narrow_layout_can_shrink_below_long_inline_code(self):
        self.assertIn(".layout { grid-template-columns: minmax(0, 1fr); }", self.source)
        self.assertIn("overflow-wrap: anywhere;", self.source)


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

    def test_blank_yaml_null_alt_fails(self):
        # a present-but-blank YAML field loads as None and must still fail
        lesson = load_day26()
        lesson["parts"]["items"][0]["alt"] = None
        errors = lesson_schema.validate_lesson(lesson, GLOSSARY_KEYS)
        self.assertTrue(any("alt is required" in e for e in errors), errors)

    def test_nonempty_helper(self):
        self.assertFalse(lesson_schema._nonempty(None))
        self.assertFalse(lesson_schema._nonempty(""))
        self.assertFalse(lesson_schema._nonempty("   "))
        self.assertFalse(lesson_schema._nonempty(19))
        self.assertTrue(lesson_schema._nonempty("x"))

    def test_missing_diagram_source_fails(self):
        lesson = load_day26()
        del lesson["wiring"]["diagram"]["source"]["page"]
        errors = lesson_schema.validate_lesson(lesson, GLOSSARY_KEYS)
        self.assertTrue(any("source.page" in e for e in errors), errors)

    def test_wiring_is_optional(self):
        # Setup and onboard-LED days have no circuit; a day with no wiring
        # block must validate (the renderer skips the section and its rail entry).
        lesson = load_day26()
        del lesson["wiring"]
        errors = lesson_schema.validate_lesson(lesson, GLOSSARY_KEYS)
        self.assertEqual([e for e in errors if "wiring" in e], [],
                         f"a diagram-less day should not raise wiring errors: {errors}")

    def test_partial_wiring_still_validated(self):
        # But a wiring block that IS present must still be complete.
        lesson = load_day26()
        del lesson["wiring"]["pins"]
        errors = lesson_schema.validate_lesson(lesson, GLOSSARY_KEYS)
        self.assertTrue(any("wiring.pins" in e for e in errors), errors)

    def test_code_is_optional(self):
        # Setup days (unbox, install IDE) write no code.
        lesson = load_day26()
        del lesson["code"]
        errors = lesson_schema.validate_lesson(lesson, GLOSSARY_KEYS)
        self.assertEqual([e for e in errors if "code." in e], [],
                         f"a code-less day should not raise code errors: {errors}")

    def test_test_is_optional(self):
        # Setup days prove nothing to run.
        lesson = load_day26()
        del lesson["test"]
        errors = lesson_schema.validate_lesson(lesson, GLOSSARY_KEYS)
        self.assertEqual([e for e in errors if "test." in e], [],
                         f"a test-less day should not raise test errors: {errors}")

    def test_test_mode_validated(self):
        lesson = load_day26()
        lesson["test"]["mode"] = "hologram"
        errors = lesson_schema.validate_lesson(lesson, GLOSSARY_KEYS)
        self.assertTrue(any("test.mode" in e for e in errors), errors)
        lesson["test"]["mode"] = "visual"   # a valid mode passes
        errors = lesson_schema.validate_lesson(lesson, GLOSSARY_KEYS)
        self.assertEqual([e for e in errors if "test.mode" in e], [], errors)

    def test_unresolved_glossary_key_fails(self):
        lesson = load_day26()
        lesson["parts"]["items"][0]["explain"] = "does-not-exist"
        errors = lesson_schema.validate_lesson(lesson, GLOSSARY_KEYS)
        self.assertTrue(any("does-not-exist" in e for e in errors), errors)

    def test_incomplete_theory_fails(self):
        lesson = load_day26()
        del lesson["theory"]["formula"]
        errors = lesson_schema.validate_lesson(lesson, GLOSSARY_KEYS)
        self.assertTrue(any("theory.formula" in e for e in errors), errors)

    def test_absent_theory_is_ok(self):
        lesson = load_day26()
        del lesson["theory"]
        errors = lesson_schema.validate_lesson(lesson, GLOSSARY_KEYS)
        self.assertEqual(errors, [], f"theory is optional: {errors}")

    def test_incomplete_micropython_fails(self):
        lesson = load_day26()
        del lesson["code"]["micropython"]["excerpt"]
        errors = lesson_schema.validate_lesson(lesson, GLOSSARY_KEYS)
        self.assertTrue(any("code.micropython.excerpt" in e for e in errors), errors)

    def test_absent_micropython_is_ok(self):
        lesson = load_day26()
        del lesson["code"]["micropython"]
        errors = lesson_schema.validate_lesson(lesson, GLOSSARY_KEYS)
        self.assertEqual(errors, [], f"micropython is optional: {errors}")

    def test_bad_track_fails(self):
        lesson = load_day26()
        lesson["tracks"]["main"] = "micropython"
        errors = lesson_schema.validate_lesson(lesson, GLOSSARY_KEYS)
        self.assertTrue(any("tracks.main" in e for e in errors), errors)

    def test_lessoncode_day_must_match_day(self):
        lesson = load_day26()
        lesson["lessonCode"] = "TSK-DAY25-ULTRASONIC"  # day is 26
        errors = lesson_schema.validate_lesson(lesson, GLOSSARY_KEYS)
        self.assertTrue(any("lessonCode day" in e for e in errors), errors)

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

    def test_malformed_blocks_report_not_crash(self):
        # Wrong types must produce validation errors, never an AttributeError.
        lesson = load_day26()
        lesson["parts"] = ["oops"]            # should be a mapping with items
        lesson["steps"] = {"items": ["wire"]}  # items should be strings (ok) — keep valid
        lesson["wiring"] = "nope"             # should be a mapping
        try:
            errors = lesson_schema.validate_lesson(lesson, GLOSSARY_KEYS)
        except AttributeError as exc:  # pragma: no cover
            self.fail(f"validator crashed on malformed input: {exc}")
        self.assertTrue(any("parts.items" in e for e in errors), errors)
        self.assertTrue(any("wiring.diagram" in e for e in errors), errors)

    def test_malformed_item_type_reported(self):
        lesson = load_day26()
        lesson["parts"]["items"] = ["not-a-mapping"]
        errors = lesson_schema.validate_lesson(lesson, GLOSSARY_KEYS)
        self.assertTrue(any("must be a mapping" in e for e in errors), errors)

    def test_malformed_nested_lists_reported(self):
        # every render-dereferenced list is guarded, so a string where a
        # {symptom, fix} / note / card mapping is expected is caught, not crashed.
        for path, bad in (
            (("test", "checks"), ["oops"]),
            (("challenge", "cards"), ["oops"]),
            (("theory", "notes"), ["oops"]),
        ):
            lesson = load_day26()
            lesson[path[0]][path[1]] = bad
            try:
                errors = lesson_schema.validate_lesson(lesson, GLOSSARY_KEYS)
            except AttributeError as exc:  # pragma: no cover
                self.fail(f"validator crashed on {path}: {exc}")
            self.assertTrue(any("must be a mapping" in e for e in errors),
                            f"{path}: {errors}")

    def test_malformed_subblock_reported(self):
        lesson = load_day26()
        lesson["hero"]["readout"] = "nope"
        errors = lesson_schema.validate_lesson(lesson, GLOSSARY_KEYS)
        self.assertTrue(any("hero.readout must be a mapping" in e for e in errors), errors)

    def test_blank_step_string_fails(self):
        lesson = load_day26()
        lesson["steps"]["items"][0] = None  # blank YAML step
        errors = lesson_schema.validate_lesson(lesson, GLOSSARY_KEYS)
        self.assertTrue(any("steps.items[0] must be a non-empty string" in e for e in errors), errors)

    def test_nested_mapping_required_field_fails(self):
        lesson = load_day26()
        lesson["test"]["checks"][0]["fix"] = ""  # blank fix
        errors = lesson_schema.validate_lesson(lesson, GLOSSARY_KEYS)
        self.assertTrue(any("test.checks[0].fix is required" in e for e in errors), errors)

    def test_logbook_is_not_required(self):
        # The logbook (reflection prompts) was removed from the course; a lesson
        # with no logbook key must still validate.
        lesson = load_day26()
        lesson.get("challenge", {}).pop("logbook", None)
        errors = lesson_schema.validate_lesson(lesson, GLOSSARY_KEYS)
        self.assertFalse(any("logbook" in e for e in errors), errors)

    def test_optional_list_wrong_type_fails(self):
        # an optional list written as a mapping/string must be caught, not coerced
        for path in (("wiring", "safety"), ("challenge", "cards")):
            lesson = load_day26()
            lesson[path[0]][path[1]] = {"oops": "mapping-not-list"}
            errors = lesson_schema.validate_lesson(lesson, GLOSSARY_KEYS)
            self.assertTrue(any(f"{path[0]}.{path[1]} must be a list" in e for e in errors),
                            f"{path}: {errors}")

    def test_code_notes_wrong_type_fails(self):
        lesson = load_day26()
        lesson["code"]["arduino"]["notes"] = "not-a-list"
        errors = lesson_schema.validate_lesson(lesson, GLOSSARY_KEYS)
        self.assertTrue(any("code.arduino.notes must be a list" in e for e in errors), errors)

    def test_collect_lessons_passes(self):
        lessons = lesson_schema.collect_lessons()
        self.assertGreaterEqual(len(lessons), 1)

    def test_real_glossary_is_valid(self):
        self.assertEqual(lesson_schema.validate_glossary(GLOSSARY), [])

    def test_malformed_glossary_entry_fails(self):
        errors = lesson_schema.validate_glossary({"foo": None, "bar": "x",
                                                  "baz": {"title": "T", "body": "B"}})
        self.assertTrue(any("foo" in e and "mapping" in e for e in errors), errors)
        self.assertTrue(any("bar" in e and "mapping" in e for e in errors), errors)
        self.assertTrue(any("baz" in e and "shortcut" in e for e in errors), errors)

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

    def test_link_renders_as_compact_anchor(self):
        out = course_build.inline("Install the [CH343 driver](https://example.com/driver).")
        self.assertIn('href="https://example.com/driver"', out)
        self.assertIn('target="_blank"', out)
        self.assertIn(">CH343 driver</a>", out)
        self.assertNotIn("](", out)

    def test_plain_text_link_keeps_destination(self):
        out = course_build.plain_text("Install the [CH343 driver](https://example.com/driver).")
        self.assertEqual(out, "Install the CH343 driver (https://example.com/driver).")

    def test_link_renders_external_anchor(self):
        out = course_build.inline("Get the [Arduino IDE](https://www.arduino.cc/en/software/).")
        self.assertIn('href="https://www.arduino.cc/en/software/"', out)
        self.assertIn('target="_blank"', out)
        self.assertIn('rel="noopener noreferrer"', out)
        self.assertIn(">Arduino IDE</a>", out)
        self.assertNotIn("](", out)  # no leftover raw Markdown

    def test_link_label_still_formats(self):
        # A URL's own characters survive; the label keeps its inline formatting.
        out = course_build.inline("[the `boards` URL](https://espressif.github.io/x_y.json)")
        self.assertIn('href="https://espressif.github.io/x_y.json"', out)
        self.assertIn("<code>boards</code>", out)

    def test_plain_text_keeps_url(self):
        out = course_build.plain_text("Install [Processing](https://processing.org/download).")
        self.assertEqual(out, "Install Processing (https://processing.org/download).")

    def test_link_url_with_parens_not_truncated(self):
        # A destination with balanced parens must stay whole in href and packet.
        url = "https://example.com/OV2640_DS(1.6).pdf"
        out = course_build.inline(f"See [datasheet]({url}).")
        self.assertIn(f'href="{url}"', out)
        self.assertIn(">datasheet</a>", out)
        self.assertNotIn(".pdf)", out.split("</a>")[1])  # remainder not spilled outside
        self.assertEqual(course_build.plain_text(f"See [datasheet]({url})."),
                         f"See datasheet ({url}).")

    def test_plain_text_url_with_markup_chars_not_mangled(self):
        # The packet path must preserve a URL's * ` {} just like the HTML path.
        for url in ("https://example.com/a*b*c",
                    "https://example.com/x`y`z",
                    "https://example.com/{foo}"):
            self.assertEqual(course_build.plain_text(f"[x]({url})"), f"x ({url})")

    def test_link_url_with_markup_chars_not_mangled(self):
        # A URL containing *, `, or {} must survive the formatting passes intact.
        for url in ("https://example.com/a*b*c",
                    "https://example.com/a**b**c",
                    "https://example.com/{foo}",
                    "https://example.com/x`y`z"):
            out = course_build.inline(f"[x]({url})")
            self.assertIn(f'href="{url}"', out)
            self.assertNotIn("<em>", out)
            self.assertNotIn("<strong>", out)
            self.assertNotIn("<code>", out)
            self.assertNotIn("define", out)

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

    def test_coaching_prompt_invokes_self_improving_skill(self):
        self.assertIn("Use $tinyskiff-coach for TinySkiff lesson TSK-DAY26-ULTRASONIC", self.html)
        self.assertIn("Keep helping me interactively while a background sub-agent", self.html)
        self.assertIn("improves the lesson for the next learner", self.html)

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
        # While any charted day is unpublished the map must show it as an
        # unlinked upcoming tile; once all 30 are published there is nothing
        # upcoming and the map's note must switch to the full-fleet form.
        published = self.html.count('class="day-tile is-ready"')
        if published < 30:
            self.assertIn("is-upcoming", self.html)
        else:
            self.assertNotIn("is-upcoming", self.html)
            self.assertIn("All 30 days are ready to sail", self.html)


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
        self.assertEqual(meta["chapter"], "Chapter 19 Ultrasonic Ranging")

    def test_theory_model_present_when_theory_present(self):
        self.assertIn("theoryModel", self.packet)
        self.assertTrue(self.packet["theoryModel"]["plainLanguage"])

    def test_theory_model_omitted_when_absent(self):
        lesson = load_day26()
        del lesson["theory"]
        packet = course_build.emit_packet(lesson, GLOSSARY)
        self.assertNotIn("theoryModel", packet)


class BacklinkTests(unittest.TestCase):
    def test_backlink_keyed_by_sketch_folder(self):
        lessons = lesson_schema.collect_lessons()
        links = course_build.derive_backlinks(lessons)
        self.assertIn("C/Sketches/Sketch_19.1_Ultrasonic_Ranging", links)
        self.assertEqual(links["C/Sketches/Sketch_19.1_Ultrasonic_Ranging"]["day"], 26)


if __name__ == "__main__":
    unittest.main()
