#!/usr/bin/env python3
"""Discover and validate public skincare product source URLs.

This tool fixes the "wrong page, successful probe" failure mode by adding a
search-and-match gate before source_probe.py. It searches public web results,
scores candidates against required product terms, probes promising URLs, and
rejects low-match pages instead of treating them as evidence.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from html import unescape
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

import requests
from bs4 import BeautifulSoup

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from source_probe import HEADERS, probe  # noqa: E402


GENERIC_TERMS = {
    "成分",
    "成分表",
    "价格",
    "报价",
    "官方",
    "官网",
    "旗舰店",
    "多少钱",
    "怎么样",
    "分析",
    "功效",
    "配方",
    "查询",
    "产品",
    "护肤品",
    "化妆品",
    "ml",
    "g",
}

SOURCE_WEIGHTS = {
    "proya-group.com": 30,
    "winona.cn": 30,
    "kao.com": 30,
    "youzan.com": 24,
    "tmall.com": 22,
    "taobao.com": 20,
    "xiaohongshu.com": 20,
    "douyin.com": 20,
    "vip.com": 20,
    "jd.com": 20,
    "keai.com.cn": 14,
    "kqmmm.com": 12,
    "cosdna.com": 12,
    "checkcosmetic.cn": 12,
    "incidecoder.com": 12,
    "bevol.cn": 12,
}

CN_OFFICIAL_COMMERCE_DOMAINS = {
    "proya-group.com",
    "winona.cn",
    "kao.com",
    "youzan.com",
    "tmall.com",
    "tmall.hk",
    "taobao.com",
    "xiaohongshu.com",
    "xhslink.com",
    "douyin.com",
    "jinritemai.com",
    "vip.com",
    "vipshop.com",
    "jd.com",
    "jd.hk",
}

KNOWN_SMALL_PRICE_DOMAINS = {
    "best.pconline.com.cn",
    "zhizhizhi.com",
    "zol.com.cn",
    "smzdm.com",
    "maigoo.com",
    "chinapp.com",
    "beaut.taobao.com",
    "keai.com.cn",
    "kqmmm.com",
}

OFFICIAL_STORE_SIGNALS = {
    "官方旗舰店",
    "品牌旗舰店",
    "旗舰店",
    "官方商城",
    "官方店",
    "自营",
    "品牌官方",
    "官方正品",
}

CREATOR_OR_HIGH_VOLUME_SIGNALS = {
    "大v",
    "达人",
    "直播间",
    "买手店",
    "月销",
    "销量",
    "已售",
    "加购",
    "回购",
    "李佳琦",
    "所有女生",
    "蜜蜂惊喜社",
    "薇娅",
    "交个朋友",
    "烈儿宝贝",
    "香菇来了",
}


@dataclass
class PriceSourceVerdict:
    allowed: bool
    tier: str
    confidence_weight: float
    reason: str


@dataclass
class SearchCandidate:
    title: str
    url: str
    snippet: str
    search_rank: int
    source_class: str
    price_source_allowed: bool
    price_evidence_tier: str
    price_confidence_weight: float
    match_terms: list[str]
    missing_terms: list[str]
    score: int
    accepted_for_probe: bool


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", unescape(value or "")).strip()


def normalize(value: str) -> str:
    return re.sub(r"\s+", "", (value or "").lower())


def canonical_url(raw_url: str) -> str:
    if raw_url.startswith("//duckduckgo.com/l/") or raw_url.startswith("https://duckduckgo.com/l/"):
        parsed = urlparse(raw_url if raw_url.startswith("http") else "https:" + raw_url)
        uddg = parse_qs(parsed.query).get("uddg", [""])[0]
        if uddg:
            return unquote(uddg)
    return raw_url


def derive_terms(query: str, must_terms: list[str]) -> list[str]:
    explicit = [t.strip() for item in must_terms for t in item.split(",") if t.strip()]
    if explicit:
        return list(dict.fromkeys(explicit))

    chunks = re.split(r"[\s,，/|]+", query)
    terms = []
    for chunk in chunks:
        token = chunk.strip()
        if not token:
            continue
        token_norm = normalize(token)
        if token_norm in GENERIC_TERMS:
            continue
        if re.fullmatch(r"\d+(?:\.\d+)?(?:ml|g)?", token_norm):
            continue
        if len(token_norm) <= 1:
            continue
        terms.append(token)
    return list(dict.fromkeys(terms[:8]))


def host_weight(url: str) -> int:
    host = urlparse(url).netloc.lower()
    for domain, weight in SOURCE_WEIGHTS.items():
        if domain in host:
            return weight
    return 0


def host_matches(url: str, domains: set[str]) -> bool:
    host = urlparse(url).netloc.lower()
    return any(host == domain or host.endswith("." + domain) or domain in host for domain in domains)


def source_class(url: str) -> str:
    if host_matches(url, KNOWN_SMALL_PRICE_DOMAINS):
        return "small_site_rejected_for_price"
    if host_matches(url, CN_OFFICIAL_COMMERCE_DOMAINS):
        return "cn_official_or_large_commerce"
    if host_matches(url, {"cosdna.com", "incidecoder.com", "bevol.cn", "skinsort.com"}):
        return "ingredient_database"
    return "other"


def classify_price_source(url: str, title: str = "", snippet: str = "") -> PriceSourceVerdict:
    """Return whether a URL can be cited as price evidence."""
    text = normalize(f"{title} {snippet} {url}")
    if host_matches(url, KNOWN_SMALL_PRICE_DOMAINS):
        return PriceSourceVerdict(
            allowed=False,
            tier="rejected_small_site",
            confidence_weight=0.0,
            reason="小导购/内容站不作为价格依据",
        )
    if host_matches(url, {"cosdna.com", "incidecoder.com", "bevol.cn", "skinsort.com", "checkcosmetic.cn"}):
        return PriceSourceVerdict(
            allowed=False,
            tier="ingredient_database_no_price",
            confidence_weight=0.0,
            reason="成分库只做配方辅助，不做价格依据",
        )
    if not host_matches(url, CN_OFFICIAL_COMMERCE_DOMAINS):
        return PriceSourceVerdict(
            allowed=False,
            tier="other_rejected_for_price",
            confidence_weight=0.0,
            reason="非官方或非大平台电商，不做价格依据",
        )

    if host_matches(url, {"proya-group.com", "winona.cn", "kao.com", "youzan.com", "vip.com", "vipshop.com"}):
        return PriceSourceVerdict(
            allowed=True,
            tier="official_or_large_platform",
            confidence_weight=1.0,
            reason="品牌官方/官方商城或大平台官方渠道",
        )
    if any(normalize(signal) in text for signal in OFFICIAL_STORE_SIGNALS):
        return PriceSourceVerdict(
            allowed=True,
            tier="official_or_large_platform",
            confidence_weight=1.0,
            reason="页面标题或摘要显示官方/旗舰/自营信号",
        )
    if any(normalize(signal) in text for signal in CREATOR_OR_HIGH_VOLUME_SIGNALS):
        return PriceSourceVerdict(
            allowed=True,
            tier="large_platform_creator_or_high_volume",
            confidence_weight=0.7,
            reason="大平台达人店/高销量店可做价格参考，但不能当官方配方来源",
        )
    return PriceSourceVerdict(
        allowed=False,
        tier="large_platform_unclear_shop_needs_manual_evidence",
        confidence_weight=0.0,
        reason="大平台普通店铺缺少官方/高销量证据，需补截图或店铺证据",
    )


def score_candidate(title: str, url: str, snippet: str, terms: list[str], rank: int) -> tuple[int, list[str], list[str]]:
    haystack = normalize(f"{title} {snippet} {url}")
    matched = [term for term in terms if normalize(term) in haystack]
    missing = [term for term in terms if term not in matched]
    score = len(matched) * 25 + host_weight(url) - rank

    if any(bad in haystack for bad in ["眼影", "气垫", "口红", "粉底", "洗面奶"]) and not any(
        good in haystack for good in ["面霜", "精华", "乳", "霜"]
    ):
        score -= 30
    if "成分" in normalize(f"{title} {snippet}"):
        score += 8
    if "价格" in normalize(f"{title} {snippet}") or "报价" in normalize(f"{title} {snippet}"):
        score += 4
    return score, matched, missing


def search_duckduckgo(query: str, terms: list[str], limit: int, timeout: int) -> list[SearchCandidate]:
    response = requests.get(
        "https://duckduckgo.com/html/",
        params={"q": query},
        headers=HEADERS,
        timeout=timeout,
        verify=False,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")
    candidates: list[SearchCandidate] = []
    seen: set[str] = set()
    for rank, result in enumerate(soup.select(".result"), start=1):
        link = result.select_one(".result__a")
        if not link:
            continue
        url = canonical_url(link.get("href", ""))
        if not url.startswith(("http://", "https://")) or url in seen:
            continue
        seen.add(url)
        title = clean_text(link.get_text(" ", strip=True))
        snippet_el = result.select_one(".result__snippet")
        snippet = clean_text(snippet_el.get_text(" ", strip=True)) if snippet_el else ""
        score, matched, missing = score_candidate(title, url, snippet, terms, rank)
        price_verdict = classify_price_source(url, title, snippet)
        candidates.append(
            SearchCandidate(
                title=title,
                url=url,
                snippet=snippet,
                search_rank=rank,
                source_class=source_class(url),
                price_source_allowed=price_verdict.allowed,
                price_evidence_tier=price_verdict.tier,
                price_confidence_weight=price_verdict.confidence_weight,
                match_terms=matched,
                missing_terms=missing,
                score=score,
                accepted_for_probe=False,
            )
        )
        if len(candidates) >= limit:
            break
    return candidates


def required_match_ok(matched: list[str], terms: list[str]) -> bool:
    if not terms:
        return bool(matched)
    return len(matched) == len(terms) or len(matched) >= max(1, min(2, len(terms)))


def main() -> int:
    parser = argparse.ArgumentParser(description="Search, score, and probe skincare product source URLs.")
    parser.add_argument("query", help="Product/source query, e.g. '珀莱雅 双抗精华 3.0 成分表 价格 30ml'")
    parser.add_argument("--must", action="append", default=[], help="Required product terms, comma-separated. Example: --must 珀莱雅,双抗,精华")
    parser.add_argument("--search-limit", type=int, default=12)
    parser.add_argument("--probe-limit", type=int, default=5)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--browser-fallback", action="store_true")
    parser.add_argument("--insecure-retry", action="store_true")
    parser.add_argument("--min-score", type=int, default=35)
    parser.add_argument(
        "--cn-official-commerce-only",
        action="store_true",
        help="Only probe brand official stores or major China official commerce platforms for price evidence.",
    )
    args = parser.parse_args()

    terms = derive_terms(args.query, args.must)
    raw_candidates = search_duckduckgo(args.query, terms, args.search_limit, args.timeout)

    rescored = []
    for candidate in raw_candidates:
        score, matched, missing = score_candidate(candidate.title, candidate.url, candidate.snippet, terms, candidate.search_rank)
        candidate.score = score
        candidate.match_terms = matched
        candidate.missing_terms = missing
        allowed_by_source = True
        if args.cn_official_commerce_only:
            allowed_by_source = candidate.price_source_allowed
            if not allowed_by_source:
                candidate.score -= 100
        candidate.accepted_for_probe = allowed_by_source and score >= args.min_score and required_match_ok(matched, terms)
        rescored.append(candidate)

    sorted_candidates = sorted(rescored, key=lambda c: c.score, reverse=True)
    probe_targets = [c for c in sorted_candidates if c.accepted_for_probe][: args.probe_limit]

    probed: list[dict[str, Any]] = []
    for candidate in probe_targets:
        result = probe(candidate.url, args.timeout, 900, args.insecure_retry, args.browser_fallback)
        result_dict = asdict(result)
        page_text = normalize(
            " ".join(
                [
                    result.title or "",
                    " ".join(result.ingredients[:20]),
                    " ".join(result.keyword_sections.values())[:1200],
                    " ".join(str(v) for v in result.product_attributes.values())[:800],
                ]
            )
        )
        evidence_matches = [term for term in terms if normalize(term) in page_text]
        result_dict["candidate"] = asdict(candidate)
        result_dict["evidence_match_terms"] = evidence_matches
        result_dict["evidence_match_ok"] = required_match_ok(evidence_matches, terms)
        if not result_dict["evidence_match_ok"] and result_dict["confidence_hint"] != "blocked":
            result_dict["confidence_hint"] = "mismatch_rejected"
        probed.append(result_dict)

    output = {
        "query": args.query,
        "required_terms": terms,
        "candidates": [asdict(c) for c in sorted_candidates],
        "probed": probed,
    }
    json.dump(output, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
