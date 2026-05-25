---
name: skincare-product-selector
description: Use when the user asks to compare skincare or cosmetic products, analyze ingredient lists, choose between two products, rank a shortlist, or select a product by skin type, budget, concern, INCI, 成分表, 配料表, 护肤品, 化妆品, 美白, 抗老, 修护, 油痘肌, or 敏感肌.
---

# Skincare Product Selector

## Core Principle

Treat skincare selection as an evidence-backed fit decision, not an ingredient popularity contest. Product formulas, prices, regions, and listings change, so verify current sources before recommending.

## First Moves

1. Classify the task mode:
   - `二选一`: compare product A vs product B and choose one.
   - `多候选排序`: rank 3+ products and assign buy priority.
   - `按需求挑选`: build a candidate pool from the user's skin type, concern, category, budget, and constraints.
   - `成分表审查`: audit one ingredient list for benefits, risks, and fit.
2. Collect or infer the user profile: skin type, concerns, category, budget, region/version, current routine, hard exclusions, and usage scenario.
3. For mainland China products, get the filing/registration number first from packaging, official product detail pages, flagship-store detail pages, or customer-service text. Then route it to NMPA/Cosmetic Supervision lookup before treating any formula as final.
4. Refresh current formula and price data. Use NMPA/packaging/official brand sources for formula; use official/major commerce sources for price.
5. Normalize each product by exact version: country/region, product name, filing/registration number, SKU/size, formula source, formula capture date, price source, and price date.
6. Interpret ingredient order before scoring: earlier ingredients usually signal higher proportion than later ingredients. For mainland China products, ingredients at or below 0.1% may be separately marked and can be unordered; for US products, ingredients at or below 1% may be unordered in the tail.
7. Compare fit using the scoring model below, then give a direct verdict.

Read `references/source-policy.md` when choosing data sources. Read `references/ingredient-risk-taxonomy.md` when mapping ingredients to functions and risks.
Read `references/crawl-playbook.md` before relying on web data.

## Crawl Verification Gate

Before giving a current purchase recommendation, prove the data path works:

```bash
python3 /Users/caifeiya/.codex/skills/skincare-product-selector/tools/source_discover.py "产品名 成分表 价格" --must 品牌,产品关键词 --browser-fallback
```

Never guess article IDs or product URLs. First discover candidate pages, match them against brand/product terms, then probe only accepted candidates. Use `source_probe.py` directly only when the user provides a URL or an official URL is already known. Record whether each source is `官方可抓`, `官方半可抓`, `第三方可抓`, `Chrome 可见`, `受阻`, `错页拒绝`, or `需人工证据`. If a key formula cannot be fetched from public pages, try a normal Chrome user-session handoff when the user can view or log into the page. If that still fails, search GitHub for a maintained crawler or dataset and run a one-product smoke test before relying on it. Do not bypass login walls, paywalls, or bot challenges.

## Data Source Rule

Use this order:

1. Physical packaging and NMPA/Cosmetic Supervision filing/registration detail for mainland China products. If a filing number is available, NMPA is the primary formula/version source.
2. For China price evidence, use only brand official malls and major commerce platforms: Tmall/Taobao, JD, Xiaohongshu, Douyin, Vipshop, or official Youzan stores. Prefer official flagship/self-operated pages. Taobao creator/KOL/high-volume shops can be used as non-official price references only when the page or user evidence shows creator/high-volume signals.
3. Ingredient interpretation tools such as INCIdecoder, 美丽修行, SkinSort, CosDNA, Paula's Choice, CosmeticsInfo, EU CosIng, CIR, and FDA references.
4. User reviews and social platforms only for experience signals such as pilling, irritation reports, finish, scent, and repurchase patterns.

Never let a third-party ingredient score override a current official formula.
Never cite small deal sites, content farms, SEO shopping pages, or unknown stores as price evidence. They may only be used as search clues, and should not appear in final recommendations.

## NMPA Filing Route

When a filing/registration number is available, classify it first:

```bash
python3 /Users/caifeiya/.codex/skills/skincare-product-selector/tools/nmpa_filing_route.py "浙G妆网备字2023001147"
```

Use the route:

- `妆网备字` -> `国产普通化妆品备案信息`
- `国妆网备进字` -> `进口普通化妆品备案信息`
- `国妆特字` -> `国产特殊化妆品注册信息`
- `国妆特进字` -> `进口特殊化妆品注册信息`

Then open NMPA政务服务门户 `https://zwfw.nmpa.gov.cn/web/index` and search under 化妆品查询. If direct automation cannot read the portal, ask for or use a normal browser screenshot instead of falling back to third-party formula as final truth.

## Scoring Model

Use 100 points as a decision aid, then explain the verdict in plain language:

| Module | Weight |
| --- | ---: |
| Need match | 30 |
| Formula completeness | 20 |
| Risk fit | 20 |
| Skin type fit | 15 |
| Value for money | 10 |
| Data confidence | 5 |

Risk fit is contextual. Alcohol, fragrance, acids, retinoids, heavy emollients, essential oils, and preservative systems are not automatically "bad"; judge them against skin type, use scenario, formula position, and user exclusions.

## Output Contracts

For `二选一`, use `templates/two-product-comparison.md`.

For `按需求挑选`, use `templates/need-based-selection.md`.

For all modes, include:

- source confidence and formula version notes
- top functional ingredients and their approximate position/band (`front`, `middle`, `tail`)
- risk notes tied to the user's profile
- price/volume/unit price when available
- final answer: `优先买`, `可买但有条件`, `不优先`, or `避开`

## Safety And Limits

Do not diagnose skin disease or promise medical outcomes. For pregnancy, severe acne, rosacea, eczema, allergy history, damaged barrier, prescription actives, or post-procedure skin, add a clinician/patch-test caveat and prefer conservative recommendations.

## Common Mistakes

- Choosing by marketing claim instead of the actual formula version.
- Treating "contains a star ingredient" as proof of effective concentration.
- Ignoring region differences, reformulations, and outdated screenshots.
- Comparing safety scores without considering the user's skin type.
- Giving a vague "both are fine" answer when the user asked for a purchase choice.
