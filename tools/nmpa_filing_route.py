#!/usr/bin/env python3
"""Classify China cosmetic filing/registration numbers for NMPA lookup."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass


NMPA_PORTAL_URL = "https://zwfw.nmpa.gov.cn/web/index"


@dataclass
class FilingRoute:
    filing_number: str
    category: str
    priority: str
    portal_url: str
    search_instruction: str


def normalize_filing_number(value: str) -> str:
    return re.sub(r"\s+", "", value or "").replace("(", "（").replace(")", "）")


def classify_filing_number(value: str) -> FilingRoute:
    filing_number = normalize_filing_number(value)
    if "国妆特进字" in filing_number:
        category = "进口特殊化妆品注册信息"
    elif "国妆特字" in filing_number:
        category = "国产特殊化妆品注册信息"
    elif "国妆网备进字" in filing_number:
        category = "进口普通化妆品备案信息"
    elif "妆网备字" in filing_number:
        category = "国产普通化妆品备案信息"
    else:
        category = "未知备案/注册编号类型"

    priority = "P0" if category != "未知备案/注册编号类型" else "needs_manual_classification"
    return FilingRoute(
        filing_number=filing_number,
        category=category,
        priority=priority,
        portal_url=NMPA_PORTAL_URL,
        search_instruction=f"进入国家药监局政务服务门户 -> 化妆品查询 -> {category}，用备案/注册编号检索。",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify cosmetic filing number for NMPA lookup.")
    parser.add_argument("filing_numbers", nargs="+")
    args = parser.parse_args()

    routes = [asdict(classify_filing_number(item)) for item in args.filing_numbers]
    json.dump(routes, fp=None if False else __import__("sys").stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
