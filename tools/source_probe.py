#!/usr/bin/env python3
"""Probe public skincare product pages for formula and price evidence.

This helper is intentionally conservative: it fetches public URLs, extracts
visible text, embedded product JSON, JSON-LD, prices, filing numbers, and
ingredient-like tables. It does not bypass login walls, paywalls, or bot
challenges.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from typing import Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}

KEYWORDS = ["成分", "配方", "备案", "价格", "参考价", "适合肤质", "功效", "香精", "防腐剂", "致痘"]
FILING_RE = re.compile(r"[\u4e00-\u9fa5]G妆网备字\d{10,}|国妆[^\s，。；;、]{4,}")
PRICE_RE = re.compile(r"(?:￥|¥)\s*\d+(?:\.\d+)?")


@dataclass
class ProbeResult:
    url: str
    status_code: int | None
    content_type: str | None
    title: str | None
    source_kind: str
    prices: list[str]
    filing_numbers: list[str]
    product_attributes: dict[str, Any]
    ingredients: list[str]
    ingredient_positions: list[dict[str, Any]]
    keyword_sections: dict[str, str]
    image_urls: list[str]
    table_count: int
    table_samples: list[list[str]]
    confidence_hint: str
    fetch_mode: str
    final_url: str | None = None
    blocked_reason: str | None = None
    error: str | None = None


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def extract_prices(text: str) -> list[str]:
    prices = []
    for raw in PRICE_RE.findall(text):
        number = re.sub(r"[^\d.]", "", raw)
        try:
            if float(number) <= 0:
                continue
        except ValueError:
            continue
        prices.append(clean_text(raw))
    return list(dict.fromkeys(prices))


def source_kind(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if "winona.cn" in host or "youzan.com" in host or "kao.com" in host:
        return "official_or_brand_channel"
    if "keai.com.cn" in host or "kqmmm.com" in host or "cosdna" in host:
        return "third_party_ingredient_database"
    if any(x in host for x in ["tmall", "jd.com", "sephora", "ulta", "amazon"]):
        return "retailer"
    return "unknown_public_page"


def parse_var_product(html: str) -> dict[str, Any]:
    match = re.search(r"var\s+product\s*=\s*(\{.*?\});", html, re.S)
    if not match:
        return {}
    try:
        product = json.loads(match.group(1))
    except json.JSONDecodeError:
        return {}

    attrs: dict[str, Any] = {}
    for item in product.get("attributeList", []):
        name = item.get("attributeName")
        value: Any = item.get("attributeValue")
        if isinstance(value, str) and value.startswith("["):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                pass
        if name:
            attrs[name] = value
    for key in ["originalPrice", "currentPrice", "productName", "name"]:
        if key in product:
            attrs[key] = product[key]
    return attrs


def parse_json_ld(soup: BeautifulSoup) -> tuple[list[str], list[str]]:
    titles: list[str] = []
    images: list[str] = []
    for script in soup.find_all("script", {"type": "application/ld+json"}):
        raw = script.string or script.get_text()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            title = data.get("title") or data.get("name")
            if title:
                titles.append(str(title))
            for image in data.get("images") or data.get("image") or []:
                if isinstance(image, str):
                    images.append(image)
    return titles, images


def extract_tables(soup: BeautifulSoup) -> tuple[list[list[str]], list[str]]:
    rows: list[list[str]] = []
    ingredients: list[str] = []
    for table in soup.find_all("table"):
        local_rows = []
        for tr in table.find_all("tr"):
            cells = [clean_text(c.get_text(" ", strip=True)) for c in tr.find_all(["th", "td"])]
            cells = [c for c in cells if c]
            if cells:
                rows.append(cells)
                local_rows.append(cells)
        if local_rows:
            header = " ".join(local_rows[0])
            if "成分" in header or any(len(r) >= 3 and "风险" in " ".join(r) for r in local_rows[:3]):
                for row in local_rows[1:]:
                    first = row[0].strip()
                    if first and first not in {"成分名称", "成分"}:
                        ingredients.append(first)
    return rows, list(dict.fromkeys(ingredients))


def extract_sections(text: str, max_chars: int) -> dict[str, str]:
    sections: dict[str, str] = {}
    for keyword in KEYWORDS:
        idx = text.find(keyword)
        if idx >= 0:
            start = max(0, idx - 80)
            end = min(len(text), idx + max_chars)
            sections[keyword] = text[start:end]
    return sections


def extract_inline_ingredients(text: str) -> list[str]:
    markers = ["标识所有成分", "全成分", "成分：", "成分:"]
    stops = ["注意事项", "使用方法", "产品安全测评", "相关选购", "更多精彩", "如果成分表有误"]
    for marker in markers:
        idx = text.find(marker)
        if idx < 0:
            continue
        start = idx + len(marker)
        end = len(text)
        for stop in stops:
            stop_idx = text.find(stop, start)
            if stop_idx >= 0:
                end = min(end, stop_idx)
        chunk = text[start:end].strip(" ：:，,。")
        if "、" in chunk or "," in chunk or "，" in chunk:
            parts = re.split(r"[、,，]\s*", chunk)
            parts = [clean_text(p) for p in parts]
            parts = [p for p in parts if 0 < len(p) <= 60 and not p.startswith("http")]
            if len(parts) >= 5:
                return list(dict.fromkeys(parts))
    return []


def label_rule_note(region: str) -> str:
    region_norm = (region or "").upper()
    if region_norm in {"CN", "CHINA", "MAINLAND", "中国", "大陆"}:
        return "中国大陆化妆品全成分通常按含量降序；含量不超过0.1%的成分可作为其他微量成分另列且不按降序。"
    if region_norm in {"US", "USA", "UNITED STATES", "美国"}:
        return "美国化妆品成分通常按含量降序；含量不超过1%的成分可在后段不按降序排列。"
    return "多数市场按含量降序列出主要成分；低含量成分的排序弹性取决于当地法规。"


def ingredient_position_band(position: int, total: int) -> str:
    if position <= min(10, max(1, total)):
        return "front"
    if position <= max(10, int(total * 0.6)):
        return "middle"
    return "tail"


def annotate_ingredient_positions(ingredients: list[str], region: str = "CN") -> list[dict[str, Any]]:
    total = len(ingredients)
    note = label_rule_note(region)
    annotations = []
    for index, ingredient in enumerate(ingredients, start=1):
        annotations.append(
            {
                "ingredient": ingredient,
                "position": index,
                "total": total,
                "position_band": ingredient_position_band(index, total),
                "relative_amount_signal": "higher_than_later" if index < total else "lowest_or_flexible_tail",
                "label_rule_note": note,
            }
        )
    return annotations


def looks_like_bot_challenge(title: str | None, text: str) -> str | None:
    challenge_markers = [
        "Just a moment",
        "请稍候",
        "正在进行安全验证",
        "Cloudflare",
        "验证您不是自动程序",
        "captcha",
    ]
    combined = f"{title or ''}\n{text[:1200]}"
    for marker in challenge_markers:
        if marker.lower() in combined.lower():
            return marker
    return None


def confidence_hint(result: ProbeResult) -> str:
    if result.error:
        return "failed"
    if result.blocked_reason:
        return "blocked"
    has_formula = bool(result.ingredients) or any("成分" in k for k in result.product_attributes)
    has_price = bool(result.prices) or any("Price" in k or "价格" in k for k in result.product_attributes)
    if result.source_kind == "official_or_brand_channel" and has_formula and has_price:
        return "high"
    if result.source_kind == "official_or_brand_channel" and (has_formula or has_price):
        return "medium_official_partial"
    if result.source_kind == "third_party_ingredient_database" and has_formula:
        return "medium_formula_support"
    if result.status_code == 403:
        return "blocked"
    return "low_needs_fallback"


def build_result(
    url: str,
    html: str,
    status_code: int | None,
    content_type: str | None,
    max_section_chars: int,
    fetch_mode: str,
    final_url: str | None = None,
) -> ProbeResult:
    soup = BeautifulSoup(html, "lxml")
    visible_text = soup.get_text("\n", strip=True)
    compact_text = clean_text(visible_text)
    json_ld_titles, json_ld_images = parse_json_ld(soup)
    product_attrs = parse_var_product(html)
    rows, table_ingredients = extract_tables(soup)
    inline_ingredients = [] if table_ingredients else extract_inline_ingredients(compact_text)

    attr_ingredients: list[str] = []
    for key, value in product_attrs.items():
        if "成分" in key and isinstance(value, list):
            attr_ingredients.extend(str(item) for item in value)

    image_urls = []
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src")
        if src:
            image_urls.append(src)
    image_urls.extend(json_ld_images)

    ingredients = list(dict.fromkeys(attr_ingredients + table_ingredients + inline_ingredients))
    result = ProbeResult(
        url=url,
        status_code=status_code,
        content_type=content_type,
        title=clean_text(soup.title.get_text()) if soup.title else (json_ld_titles[0] if json_ld_titles else None),
        source_kind=source_kind(url),
        prices=extract_prices(compact_text),
        filing_numbers=list(dict.fromkeys(FILING_RE.findall(compact_text))),
        product_attributes=product_attrs,
        ingredients=ingredients,
        ingredient_positions=annotate_ingredient_positions(ingredients),
        keyword_sections=extract_sections(compact_text, max_section_chars),
        image_urls=list(dict.fromkeys(image_urls))[:20],
        table_count=len(rows),
        table_samples=rows[:20],
        confidence_hint="",
        fetch_mode=fetch_mode,
        final_url=final_url,
        blocked_reason=looks_like_bot_challenge(soup.title.get_text() if soup.title else None, compact_text),
    )
    result.confidence_hint = confidence_hint(result)
    return result


def probe_with_requests(url: str, timeout: int, max_section_chars: int, insecure_retry: bool) -> ProbeResult:
    kwargs = {"headers": HEADERS, "timeout": timeout}
    try:
        response = requests.get(url, **kwargs)
    except requests.exceptions.SSLError:
        if not insecure_retry:
            raise
        response = requests.get(url, verify=False, **kwargs)
    if response.apparent_encoding and response.encoding and response.encoding.lower() in {"iso-8859-1", "latin-1"}:
        response.encoding = response.apparent_encoding
    return build_result(
        url=url,
        html=response.text,
        status_code=response.status_code,
        content_type=response.headers.get("content-type"),
        max_section_chars=max_section_chars,
        fetch_mode="requests",
        final_url=response.url,
    )


def probe_with_browser(url: str, timeout: int, max_section_chars: int) -> ProbeResult:
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        raise RuntimeError(f"playwright unavailable: {exc}") from exc

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=HEADERS["User-Agent"],
            locale="zh-CN",
            viewport={"width": 1366, "height": 900},
        )
        page = context.new_page()
        response = page.goto(url, wait_until="domcontentloaded", timeout=timeout * 1000)
        page.wait_for_timeout(5000)
        html = page.content()
        final_url = page.url
        status = response.status if response else None
        browser.close()
    return build_result(
        url=url,
        html=html,
        status_code=status,
        content_type="text/html; rendered=playwright",
        max_section_chars=max_section_chars,
        fetch_mode="browser",
        final_url=final_url,
    )


def probe(url: str, timeout: int, max_section_chars: int, insecure_retry: bool, browser_fallback: bool) -> ProbeResult:
    result = probe_with_requests(url, timeout, max_section_chars, insecure_retry)
    if not browser_fallback:
        return result
    should_try_browser = result.confidence_hint in {"blocked", "low_needs_fallback"} or (
        result.status_code in {401, 403} and not result.ingredients
    )
    if not should_try_browser:
        return result
    browser_result = probe_with_browser(url, timeout, max_section_chars)
    if browser_result.ingredients or (
        len(browser_result.keyword_sections) > len(result.keyword_sections) and not browser_result.blocked_reason
    ):
        return browser_result
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe public skincare product pages for ingredient evidence.")
    parser.add_argument("urls", nargs="+")
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--max-section-chars", type=int, default=900)
    parser.add_argument("--insecure-retry", action="store_true", help="Retry TLS failures with certificate verification disabled.")
    parser.add_argument("--browser-fallback", action="store_true", help="Use Playwright rendering when direct HTTP is blocked or incomplete.")
    args = parser.parse_args()

    results = []
    for url in args.urls:
        try:
            results.append(asdict(probe(url, args.timeout, args.max_section_chars, args.insecure_retry, args.browser_fallback)))
        except Exception as exc:  # Keep batch probes useful when one URL fails.
            results.append(
                asdict(
                    ProbeResult(
                        url=url,
                        status_code=None,
                        content_type=None,
                        title=None,
                        source_kind=source_kind(url),
                        prices=[],
                        filing_numbers=[],
                        product_attributes={},
                        ingredients=[],
                        ingredient_positions=[],
                        keyword_sections={},
                        image_urls=[],
                        table_count=0,
                        table_samples=[],
                        confidence_hint="failed",
                        fetch_mode="failed",
                        final_url=None,
                        blocked_reason=None,
                        error=repr(exc),
                    )
                )
            )
    json.dump(results, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
