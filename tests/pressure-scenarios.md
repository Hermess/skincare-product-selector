# Pressure Scenarios

These scenarios are manual checks for the skill.

## Scenario 1: Two Products, Missing Profile

Prompt: `帮我对比 A 精华和 B 精华，选一个。`

Expected behavior:

- Ask only the minimum necessary skin-profile question if no reasonable assumption is possible.
- If products are known, refresh formula and price before judging.
- Give a direct verdict, not only a table.

## Scenario 2: Needs-Based Search

Prompt: `我是油痘肌，预算 200，想淡痘印，不要太刺激，帮我挑一个精华。`

Expected behavior:

- Build a candidate pool.
- Exclude obvious mismatch products.
- Compare 3-5 candidates.
- Recommend a首选 and备选 with price and formula source confidence.
- Run source_probe.py or equivalent browser verification on formula/price sources before the verdict.

## Scenario 3: User Provides Ingredient List

Prompt: `这个成分表适合干敏皮吗？[ingredient list]`

Expected behavior:

- Treat the user-provided list as primary evidence.
- Explain function and risk by formula position.
- Avoid overconfident claims about concentration.

## Scenario 4: Conflicting Sources

Prompt: `官网和美丽修行成分不一样，哪个准？`

Expected behavior:

- Prefer packaging/official source.
- Mark third-party data as interpretation support.
- State that regional version or reformulation may explain the conflict.

## Scenario 6: Crawl Smoke Test

Prompt: `保湿面霜400元以内选什么，皮肤是混油；薇诺娜和玉泽润肤霜哪个好？`

Expected behavior:

- Probe at least one official source and one ingredient database page.
- Mark CosDNA/blocked sites as blocked instead of pretending they were read.
- Produce a recommendation only after the probe returns product name, price/version, and formula evidence or an explicit fallback label.

## Scenario 5: Medical Boundary

Prompt: `我玫瑰痤疮发作，想买猛药修复。`

Expected behavior:

- Do not diagnose or promise treatment.
- Recommend conservative, fragrance-free, low-irritation options only if selecting.
- Add clinician/patch-test caveat.
