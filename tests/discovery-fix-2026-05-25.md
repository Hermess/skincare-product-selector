# Discovery Fix 2026-05-25

## Problem

The previous workflow allowed guessed article URLs to be sent directly to `source_probe.py`. The probe extracted those pages correctly, but some pages were unrelated to the target product, such as eye shadow or cushion foundation pages. That created a wrong-page hit.

## Root Cause

`source_probe.py` validates extraction quality for a known URL. It did not validate whether a discovered or guessed URL matched the intended brand/product.

## Fix

Added `tools/source_discover.py`.

The new workflow is:

1. Search public web results.
2. Score candidates by required brand/product terms.
3. Probe only accepted candidates.
4. Re-check probed page title, ingredient list, and sections.
5. Mark low-match extracted pages as `mismatch_rejected`.

## Price Source Fix

After user feedback, price evidence now has an additional source gate:

- Allowed: brand official malls, Tmall/Taobao, JD, Xiaohongshu, Douyin, Vipshop, official Youzan.
- Allowed with label: Taobao/Tmall creator, KOL, buyer, or high-volume shops. These are `large_platform_creator_or_high_volume`, not official formula sources.
- Rejected: small deal sites, guide sites, SEO price pages, content farms, unknown independent stores.

Regression test:

```bash
python3 tests/test_source_policy.py
```

Expected:

- `best.pconline.com.cn` is rejected as `rejected_small_site`.
- JD official/self-operated wording is accepted as `official_or_large_platform`.
- Taobao creator/high-volume wording is accepted as `large_platform_creator_or_high_volume`.

## Ingredient Position Fix

The formula probe now annotates each ingredient with:

- position number
- total ingredient count
- position band: `front`, `middle`, or `tail`
- region-specific label note

Regression test:

```bash
python3 tests/test_ingredient_positions.py
```

Expected:

- Earlier ingredients are marked as `higher_than_later`.
- China rule notes mention the `0.1%` trace-ingredient exception.
- US rule notes mention the `1%` flexible tail exception.

## NMPA Filing Route Fix

For mainland China products, the skill now treats NMPA/Cosmetic Supervision filing detail as the primary formula/version source when a filing or registration number is available.

Regression test:

```bash
python3 tests/test_nmpa_filing_route.py
```

Expected:

- `妆网备字` -> `国产普通化妆品备案信息`
- `国妆网备进字` -> `进口普通化妆品备案信息`
- `国妆特字` -> `国产特殊化妆品注册信息`
- `国妆特进字` -> `进口特殊化妆品注册信息`

## Smoke Tests

### 珀莱雅 双抗精华 3.0

Command:

```bash
python3 tools/source_discover.py '珀莱雅 双抗精华 3.0 成分表 价格 30ml' --must '珀莱雅,双抗,精华' --browser-fallback --insecure-retry
```

Result:

- Top candidates were JD, 可爱网, CosDNA, Zhihu, YesStyle, Taobao pages for 珀莱雅双抗精华.
- 可爱网 candidate probed as `medium_formula_support` with 63 ingredients.
- CosDNA was detected as blocked.
- No eye shadow/cushion pages were accepted.

### 珀莱雅 红宝石精华 3.0

Command:

```bash
python3 tools/source_discover.py '珀莱雅 红宝石精华 3.0 成分表 价格 30ml' --must '珀莱雅,红宝石,精华' --browser-fallback --insecure-retry
```

Result:

- Top candidates were JD, 可爱网, 百度健康, Sohu, Zhihu pages for 珀莱雅红宝石精华.
- 可爱网 candidate probed as `medium_formula_support` with 71 ingredients.

### OLAY 超红瓶精华

Command:

```bash
python3 tools/source_discover.py 'OLAY 超红瓶 精华 成分表 价格' --must 'OLAY,超红瓶,精华' --browser-fallback --insecure-retry
```

Result:

- Top candidates matched OLAY 超红瓶.
- Stable structured ingredient evidence was not found in the smoke test, so it should not be treated as a high-confidence formula source without another official/package/Chrome-visible source.
