#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import source_probe  # noqa: E402


class IngredientPositionTest(unittest.TestCase):
    def test_annotates_position_and_order_signal(self):
        ingredients = ["水", "甘油", "烟酰胺", "透明质酸钠", "香精"]

        annotations = source_probe.annotate_ingredient_positions(ingredients, region="CN")

        self.assertEqual(annotations[0]["ingredient"], "水")
        self.assertEqual(annotations[0]["position"], 1)
        self.assertEqual(annotations[0]["position_band"], "front")
        self.assertEqual(annotations[2]["ingredient"], "烟酰胺")
        self.assertEqual(annotations[2]["relative_amount_signal"], "higher_than_later")
        self.assertIn("0.1%", annotations[-1]["label_rule_note"])

    def test_us_rule_note_mentions_one_percent_flexibility(self):
        annotations = source_probe.annotate_ingredient_positions(["water", "glycerin"], region="US")

        self.assertIn("1%", annotations[-1]["label_rule_note"])


if __name__ == "__main__":
    unittest.main()
