#!/usr/bin/env python3
"""Tests for the course-forward landing (build_site).

Run with the repo venv:  .venv/bin/python -m unittest discover -s scripts/tests
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import build_site  # noqa: E402


def make_ctx() -> dict:
    return {
        "total": 30,
        "publishedDays": [1, 2, 3],
        "slugs": {"1": "day-01-unbox", "2": "day-02-setup", "3": "day-03-blink"},
        "day1Slug": "day-01-unbox",
        "legs": [
            {"name": "First light", "subtitle": "Set up the board.",
             "dayFrom": 1, "dayTo": 5, "startSlug": "day-01-unbox"},
            {"name": "Onto the network", "subtitle": "Go wireless.",
             "dayFrom": 27, "dayTo": 30, "startSlug": None},
        ],
    }


def make_data() -> dict:
    return {
        "generatedAt": "2026-07-09T00:00:00+00:00",
        "projectsC": [{
            "track": "C / Arduino", "title": "Blink",
            "folder": "C/Sketches/Sketch_01.1_Blink", "file": "Blink.ino",
            "number": "01.1", "language": "Arduino C++",
            "code": "void loop(){}", "docsUrl": "https://d", "sourceUrl": "https://s",
            "taughtInDay": {"day": 3, "slug": "day-03-blink", "title": "Make an LED blink"},
        }],
        "projectsPython": [],
        "libraries": [],
        "pdfs": [],
    }


class LandingRenderTests(unittest.TestCase):
    def setUp(self):
        self.html = build_site.render_html(make_data(), make_ctx())

    def test_hero_is_course_forward(self):
        self.assertIn("Start Day 1", self.html)
        self.assertIn('href="./course/day-01-unbox/"', self.html)
        # the retired library-first hero must not come back
        self.assertNotIn("Browse projects", self.html)
        self.assertNotIn("less annoying front door", self.html)

    def test_voyage_instrument_present(self):
        for hook in ('id="mapProgress"', 'id="doneCount"', 'id="mapVoyage"', 'id="mapResume"'):
            self.assertIn(hook, self.html)

    def test_landing_course_data_injected(self):
        self.assertIn('id="landing-course"', self.html)
        self.assertIn('"day1Slug"', self.html)
        self.assertIn("day-01-unbox", self.html)

    def test_legs_render_with_ranges(self):
        self.assertEqual(self.html.count('class="leg"'), 2)
        self.assertIn("Two legs, thirty days", self.html)
        self.assertIn("First light", self.html)
        self.assertIn("Days 1–5", self.html)
        self.assertIn("Days 27–30", self.html)
        # a leg with no published start day falls back to the map
        self.assertIn('class="leg" href="./course/"', self.html)

    def test_library_is_demoted_secondary(self):
        self.assertIn("reference library", self.html.lower())
        self.assertIn('id="library"', self.html)
        # the "Taught in Day N" cross-link data rides along in the site payload
        self.assertIn('"taughtInDay"', self.html)
        self.assertIn("day-03-blink", self.html)

    def test_uses_course_design_system(self):
        self.assertIn("./course/course.css", self.html)
        self.assertIn("./landing.css", self.html)
        self.assertNotIn("styles.css", self.html)


class BuildCourseCtxTests(unittest.TestCase):
    """Integration: the real build derives the landing context correctly."""

    def test_ctx_and_backlink_enrichment(self):
        data = {"projectsC": build_site.collect_c_sketches(), "projectsPython": []}
        tmp = Path(tempfile.mkdtemp())
        original_out = build_site.OUT
        try:
            build_site.OUT = tmp
            summary, ctx = build_site.build_course(data)
        finally:
            build_site.OUT = original_out
            shutil.rmtree(tmp, ignore_errors=True)

        self.assertEqual(ctx["day1Slug"], "day-01-unbox")
        self.assertEqual(len(ctx["legs"]), 7)
        self.assertEqual(len(ctx["publishedDays"]), 30)
        self.assertEqual(ctx["total"], 30)
        # every backlink lands on exactly one enriched sketch card
        taught = [p for p in data["projectsC"] if p.get("taughtInDay")]
        self.assertEqual(len(taught), summary["backlinks"])
        blink = next(p for p in data["projectsC"]
                     if p["folder"] == "C/Sketches/Sketch_01.1_Blink")
        self.assertEqual(blink["taughtInDay"]["day"], 3)


if __name__ == "__main__":
    unittest.main()
