#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import nmpa_filing_route  # noqa: E402


class NmpaFilingRouteTest(unittest.TestCase):
    def test_domestic_ordinary_filing_number(self):
        route = nmpa_filing_route.classify_filing_number("浙G妆网备字2023001147")

        self.assertEqual(route.category, "国产普通化妆品备案信息")
        self.assertEqual(route.priority, "P0")

    def test_imported_ordinary_filing_number(self):
        route = nmpa_filing_route.classify_filing_number("国妆网备进字（浙）2023001147")

        self.assertEqual(route.category, "进口普通化妆品备案信息")

    def test_domestic_special_registration_number(self):
        route = nmpa_filing_route.classify_filing_number("国妆特字G20212302")

        self.assertEqual(route.category, "国产特殊化妆品注册信息")

    def test_imported_special_registration_number(self):
        route = nmpa_filing_route.classify_filing_number("国妆特进字J20212302")

        self.assertEqual(route.category, "进口特殊化妆品注册信息")


if __name__ == "__main__":
    unittest.main()
