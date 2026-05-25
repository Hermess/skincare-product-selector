# Verification 2026-05-25

## Command

```bash
python3 /Users/caifeiya/.codex/skills/skincare-product-selector/tools/source_probe.py --browser-fallback --insecure-retry \
  'https://www.winona.cn/product/110009.html' \
  'https://www.keai.com.cn/article-6328-1.html' \
  'https://detail.youzan.com/show/goods?alias=2ogsp4r3m4yvwl6&from_source=gbox_seo' \
  'https://www.keai.com.cn/portal.php?aid=5905&mod=view' \
  'https://www.keai.com.cn/article-1057-1.html' \
  'https://www.kqmmm.com/cosmetic/105611.html' \
  'https://www.kao.com/cn/products/curel/crl_facecream_00/' \
  'https://www.keai.com.cn/article-216-1.html' \
  'https://www.cosdna.com/chs/cosmetic_1049612623.html'
```

## Source Probe Result

| Source | Result |
| --- | --- |
| Winona official product page | HTTP 200, official price `￥268.00`, 15 ingredients, filing attribute `云G妆网备字2017000520`, confidence `high` |
| Keai Winona ingredient page | HTTP 200, 15 ingredients, filing `云G妆网备字2017000520`, confidence `medium_formula_support` |
| Yuze Youzan official product page | HTTP 200, title and price `￥279.00`, formula not visible in text, confidence `medium_official_partial` |
| Keai Yuze clear/oily-skin cream page | HTTP 200, 26 ingredients, filing `沪G妆网备字2023000899`, confidence `medium_formula_support` |
| Keai Yuze classic barrier cream page | HTTP 200, 44 ingredients, confidence `medium_formula_support` |
| KQMMM Yuze classic barrier cream page | HTTP 200, price snippet `¥198`, 36 ingredients, confidence `medium_formula_support` |
| Kao Curel official page | HTTP 200, official ingredient text captured, no price captured, confidence `medium_official_partial` |
| Keai Curel ingredient page | HTTP 200, 18 ingredients, confidence `medium_formula_support` |
| CosDNA Winona page | HTTP requests returned Cloudflare `403`; isolated browser fallback returned security verification in repeatable test; user Chrome session successfully displayed and extracted visible ingredient text, title `薇诺娜舒敏保湿特护霜 成分分析 | CosDNA`, text length 944 |

## GitHub Fallback Check

GitHub API repository searches were run for `cosdna scraper`, `incidecoder scraper skincare`, `美丽修行 爬虫 成分表`, and `NMPA 化妆品备案 爬虫`. No maintained Chinese-product crawler was needed for these test cases because official/third-party public pages already produced usable fields, and CosDNA was readable through the normal user Chrome session after opening the page.

## Test 1: 保湿面霜 400 元以内, 混油

Recommended first choice: 玉泽皮肤屏障修护专研清透保湿霜 50g.

Evidence: Yuze official Youzan page captured the current product and `￥279.00`; Keai captured a formula with humectants early in the list, lighter emollients/silicones, no fragrance flag, and an oily/sensitive positioning. It is a better fit for mixed-oily skin than richer barrier creams.

Backup: 薇诺娜舒敏保湿特护霜 50g.

Evidence: Winona official page captured `￥268.00`, full 15-ingredient formula, and filing. It is stronger when the user is sensitive/redness-prone, but the shea butter/ester/silicone structure is less targeted to T-zone oiliness than Yuze clear/oily-skin cream.

Not first choice for mixed-oily: 玉泽经典皮肤屏障修护保湿霜 and 珂润润浸保湿滋润乳霜.

Reason: both are solid barrier-moisturizing formulas, but they read richer/more lipid-focused and are less specifically matched to mixed-oily skin.

## Test 2: 薇诺娜 vs 玉泽润肤霜

If comparing Winona `舒敏保湿特护霜 50g` against Yuze classic `皮肤屏障修护保湿霜`, mixed-oily skin should choose Winona.

Reason: Winona has a shorter official-captured formula, no fragrance/preservative flags in the checked ingredient page, and a lighter-feeling repair profile. Yuze classic has stronger lipid/barrier repair but a richer oil-heavy structure, so it is better for dry/sensitive or winter barrier repair than for mixed-oily daily all-face use.

If the Yuze product meant is the newer `皮肤屏障修护专研清透保湿霜`, choose Yuze clear/oily-skin cream instead.
