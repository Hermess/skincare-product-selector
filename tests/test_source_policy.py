#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import source_discover  # noqa: E402


class SourcePolicyTest(unittest.TestCase):
    def test_small_deal_sites_are_rejected_for_price(self):
        verdict = source_discover.classify_price_source(
            "https://best.pconline.com.cn/youhui/15472892.html",
            "珀莱雅双抗精华好价",
            "导购优惠信息",
        )

        self.assertFalse(verdict.allowed)
        self.assertEqual(verdict.tier, "rejected_small_site")
        self.assertEqual(
            source_discover.source_class("https://beaut.taobao.com/topic/ruye_13/example.html"),
            "small_site_rejected_for_price",
        )

    def test_major_platform_official_store_is_high_confidence_price_source(self):
        verdict = source_discover.classify_price_source(
            "https://item.jd.com/100046452794.html",
            "珀莱雅官方旗舰店 双抗精华3.0 30ml",
            "京东自营官方旗舰店",
        )

        self.assertTrue(verdict.allowed)
        self.assertEqual(verdict.tier, "official_or_large_platform")

    def test_taobao_influencer_or_high_volume_shop_is_allowed_but_not_official(self):
        verdict = source_discover.classify_price_source(
            "https://item.taobao.com/item.htm?id=123456",
            "李佳琦直播间 珀莱雅双抗精华3.0",
            "淘宝大V店 月销10万+",
        )

        self.assertTrue(verdict.allowed)
        self.assertEqual(verdict.tier, "large_platform_creator_or_high_volume")
        self.assertLess(verdict.confidence_weight, 1.0)


if __name__ == "__main__":
    unittest.main()
