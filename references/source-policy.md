# Source Policy

## Source Priority

| Priority | Source | Use |
| --- | --- | --- |
| P0 | User-provided packaging photo or box text plus NMPA/Cosmetic Supervision filing detail for mainland China products | Best evidence for the exact product/version and official formula |
| P1 | Brand official site and official flagship store | Filing number discovery, current listing, brand claims, product name, version |
| P2 | Major official commerce pages: Tmall/Taobao, JD, Xiaohongshu, Douyin, Vipshop, official Youzan stores | Price, size, current listing, secondary ingredient copy |
| P2.5 | Taobao/Tmall creator, KOL, buyer, or high-volume shops with visible sales/popularity evidence | Non-official price reference only; never formula authority |
| P3 | Ingredient databases: INCIdecoder, 美丽修行, SkinSort, CosDNA | Ingredient interpretation and comparison hints |
| P4 | Professional references: EU CosIng, FDA labeling references, CIR, CosmeticsInfo, Paula's Choice | Regulatory/function/safety context |
| P5 | Reviews and social posts | Texture, scent, pilling, irritation anecdotes, repurchase trend |

Use the highest available source for the ingredient list. For mainland China products, if a filing/registration number exists, NMPA/Cosmetic Supervision detail is the target source for formula/version validation. Use lower-priority sources only as fallback or interpretation support.

Before using a source in a recommendation, run `tools/source_probe.py` or equivalent browser inspection and record the result. If the page is blocked or image-only, mark it as such instead of silently treating it as verified.

## Recommended Public References

- EU CosIng: https://single-market-economy.ec.europa.eu/sectors/cosmetics/cosmetic-ingredient-database_en
- FDA cosmetics labeling summary: https://www.fda.gov/cosmetics/labeling-regulations/summary-labeling-requirements
- FDA cosmetic ingredient names: https://www.fda.gov/cosmetics/cosmetics-labeling/cosmetic-ingredient-names
- Cosmetic Ingredient Review: https://www.cir-safety.org/
- CosmeticsInfo: https://www.cosmeticsinfo.org/
- INCIdecoder: https://incidecoder.com/
- 美丽修行: https://www.bevol.cn/
- SkinSort: https://skinsort.com/
- CosDNA: https://www.cosdna.com/
- NMPA: https://www.nmpa.gov.cn/
- NMPA政务服务门户: https://zwfw.nmpa.gov.cn/web/index

## Verification Rules

1. Always record formula source, source type, capture date, region/version, filing/registration number when available, and price date.
2. For current recommendations, browse or otherwise refresh product formula, price, and availability.
3. If sources disagree, prefer packaging or official brand/NMPA evidence and mark the conflict.
4. If only third-party data is available, state `成分表可信度: 中/低` and avoid overconfident verdicts.
5. If the product has regional variants, compare only the version the user can buy.
6. If the user provides photos, use them as primary evidence and use websites for interpretation.
7. Do not scrape around paywalls, login walls, or anti-bot restrictions; use accessible public pages or ask the user for screenshots.

## NMPA Lookup For Mainland China Products

Preferred path:

1. Get the filing/registration number from packaging, official product page, official flagship-store product detail, or customer-service reply.
2. Classify the number with:

```bash
python3 tools/nmpa_filing_route.py "浙G妆网备字2023001147"
```

3. Open `https://zwfw.nmpa.gov.cn/web/index`, choose `化妆品查询`, then choose the matching database:

| Number pattern | Database |
| --- | --- |
| `妆网备字` | 国产普通化妆品备案信息 |
| `国妆网备进字` | 进口普通化妆品备案信息 |
| `国妆特字` | 国产特殊化妆品注册信息 |
| `国妆特进字` | 进口特殊化妆品注册信息 |

4. Use the NMPA detail as the formula/version source. Use brand pages for claims and commerce pages for current price.
5. If the portal is dynamic or requires manual interaction, use normal browser/computer-use flow or ask for screenshots. Do not silently replace NMPA with a third-party database when a filing number exists.

## Price Evidence Rules For China Buying Advice

Allowed price sources:

- Brand official site or official mall.
- Tmall/Taobao official flagship store, JD official/self-operated store, Xiaohongshu official store, Douyin official store, Vipshop official/self-operated channel, official Youzan store.
- Taobao/Tmall creator/KOL/high-volume shops only when the page title, snippet, screenshot, or user-provided evidence clearly shows signals such as `直播间`, `达人`, `买手店`, `月销`, `已售`, `李佳琦`, `所有女生`, or similar.

Rejected as price sources:

- Small deal sites, guide sites, SEO shopping pages, scraped price pages, content farms, and unknown independent stores.
- Ingredient databases such as CosDNA/INCIdecoder/美丽修行: useful for formulas, not prices.
- Reviews or social posts without a directly purchasable official/major-platform listing.

If only a small site has a visible price, mark `价格可信度: 低/不可采信` and do not use that price to decide whether a product is under budget. Ask for a platform screenshot/link or continue searching official/major-platform sources.

## Capture Checklist

For each product, capture:

- product name and brand
- product category
- country/region/version
- size, price, unit price
- full ingredient list
- top 10 ingredients
- key active ingredients and their list position
- risk flags and why they matter for this user
- source URL or user-provided evidence
- source date
- confidence level

## Conflict Labels

Use these labels:

- `高`: packaging or official source confirms the formula, current price available.
- `中`: official source missing but multiple reputable retailers/databases agree; for price, major-platform non-official high-volume shops are at most `中`.
- `低`: only one third-party source, old screenshots, or unclear regional version.
- `冲突`: sources disagree; do not make a hard recommendation without caveat.
