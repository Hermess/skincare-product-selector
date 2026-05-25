# Crawl Playbook

## Goal

Before recommending products, prove that the current data path works. A valid run should capture at least:

- product title
- formula or ingredient section
- price/size or a separate price source
- source type and confidence
- failure reason for blocked pages

## Primary Tools

For NMPA filing/registration routing, run:

```bash
python3 /Users/caifeiya/.codex/skills/skincare-product-selector/tools/nmpa_filing_route.py "备案编号或注册编号"
```

For product discovery, run:

```bash
python3 /Users/caifeiya/.codex/skills/skincare-product-selector/tools/source_discover.py "产品名 成分表 价格" --must 品牌,产品关键词 --browser-fallback
```

For user-provided or known URLs, run:

```bash
python3 /Users/caifeiya/.codex/skills/skincare-product-selector/tools/source_probe.py --browser-fallback URL...
```

Useful flags:

```bash
--insecure-retry
--max-section-chars 1200
--browser-fallback
```

## What The Probe Handles

- Static HTML pages.
- Embedded `var product = {...}` product JSON, including Winona official product pages.
- JSON-LD product metadata, including Youzan product title/images/date.
- Visible price text such as `￥268.00`.
- NMPA-style filing numbers such as `云G妆网备字...`.
- HTML ingredient tables from pages such as 可爱网/海淘族-style ingredient pages.
- Image URLs for pages whose details are in product images.
- Playwright rendering for normal JavaScript pages when direct HTTP is incomplete.
- Bot-challenge detection so a security page is not mistaken for product evidence.

## Discovery And Matching Rule

Do not guess article IDs, product IDs, or search-result URLs. The correct order is:

1. For mainland China products, first obtain the filing/registration number from packaging, official product pages, official flagship store pages, or customer-service text.
2. Route the number with `nmpa_filing_route.py`, then use the matching NMPA/Cosmetic Supervision query page as the target formula/version evidence.
3. If no filing number is available yet, search with `source_discover.py`.
4. Require brand/product keywords with `--must`.
5. Probe only candidates whose title/snippet/URL match the target.
6. After probing, re-check the extracted page title/ingredients/sections.
7. Reject pages marked `mismatch_rejected`; they are wrong-page hits even if HTTP extraction succeeded.

Example:

```bash
python3 tools/source_discover.py "珀莱雅 双抗精华 3.0 成分表 价格 30ml" --must 珀莱雅,双抗,精华 --browser-fallback
```

## Known Failure Modes

| Symptom | Meaning | Fallback |
| --- | --- | --- |
| HTTP 403 / Cloudflare page | Bot challenge, common on CosDNA | Try `--browser-fallback`; if it still shows a verification page, use another public ingredient page, official source, or user screenshot |
| Official page has price but no formula text | Details may be in images or hidden API | Use official page for price/version and a third-party formula page for ingredients |
| Search result exists but page blocks direct fetch | Search snippet can guide source choice but should not be the only evidence | Find another accessible page or ask for packaging photo |
| Chinese official filing portal requires dynamic/session access | Direct script may fail | Use browser/app/manual screenshot as primary evidence |
| Product has no visible filing number on commerce page | Formula cannot be finalized from price page alone | Ask for package/detail screenshot, consult official customer service, or mark NMPA evidence missing |

## Chrome User-Session Channel

Use this when a source is required and direct probing says `blocked`, but the page can be opened normally by the user in Chrome.

Workflow:

1. Open the page in the user's Chrome profile.
2. If the page asks for login or a human verification step, ask the user to complete it in Chrome.
3. Claim the visible Chrome tab through the Chrome connector.
4. Read only the visible page content needed for the product comparison.
5. Record the source as `Chrome 用户会话可见页`, with the page URL, title, and capture time.

This is appropriate for pages such as CosDNA when the normal browser can display the ingredient table. It is not a license to bypass CAPTCHA or security checks; the user or normal browser session must be able to view the page.

## Anti-Bot Boundary

Allowed:

- normal HTTP fetching
- public search discovery
- Playwright rendering of pages a normal browser can view
- parsing embedded JSON, JSON-LD, tables, visible text, and public images
- switching to official pages, retailer pages, public ingredient databases, packaging photos, or user screenshots

Not allowed:

- bypassing CAPTCHA or Cloudflare verification
- proxy-pool evasion
- credential or session theft
- scraping behind login/paywall/private APIs
- disguising blocked pages as successful evidence

## GitHub Fallback Policy

If direct public pages fail for a required product class, search GitHub for current crawlers or datasets using:

- `cosdna scraper`
- `incidecoder scraper`
- `美丽修行 爬虫`
- `化妆品 成分表 爬虫`
- `NMPA 化妆品备案 爬虫`

Prefer maintained tools with clear install steps and non-invasive scraping. Do not use tools that bypass authentication, violate site controls, or require private credentials. If a GitHub tool is used, run it on one test product and record the command, output, and limitations before relying on it.

## Evidence Labeling

Use these labels in recommendations:

- `官方可抓`: official product page gives formula and price.
- `官方半可抓`: official source gives product/price/version, but formula needs another source.
- `第三方可抓`: ingredient database page gives a structured formula.
- `受阻`: page blocks direct script access.
- `Chrome 可见`: direct script is blocked but the user Chrome page is visible and readable.
- `错页拒绝`: search result or probed page does not match required product terms.
- `需人工证据`: user packaging photo, app screenshot, or browser screenshot needed.
