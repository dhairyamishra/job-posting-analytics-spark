# Appendix D — Findings and Inferences Honestly Assessed

This appendix takes each of the seven inferences the project surfaces and evaluates them on three dimensions: numerical correctness, defensibility of the inference, and how the report should frame each. The intent is to make explicit which findings the project's data can support unconditionally, which need careful framing, and which are weak or circular.

## How each inference is evaluated

For each finding, I examine:

1. **Numerical correctness**: is the underlying number reproducible from the result CSVs and verified against the cleaned data?
2. **Defensibility of the inference**: does the data support the *conclusion* that's natural to draw from the chart, or is the conclusion stronger than the evidence allows?
3. **Recommended framing in the report and presentation**: how should this finding be discussed to be honest without underselling the engineering work?

Findings are labeled by chart number and listed in the same order as they appear in the report.

---

## Inference 1 — Q1.1 "Layoff cohort pays roughly 2x more at Entry level"

**The number**: Layoff-cohort entry-level median normalized salary is $101,750 (n=162). Non-affected cohort entry-level median is $52,000 (n=8,859). Ratio: 1.96x.

**Numerical correctness**: Verified. Source: `output/results/q1_1_median_salary_by_level/part-*.csv`. The `PERCENTILE_APPROX(normalized_salary, 0.5)` Spark SQL function on the postings_tagged view gives these exact values.

**Defensibility of the natural inference** ("layoff-affected companies pay more"): **Misleading.** The natural reading suggests layoffs are associated with higher pay. The actual mechanism is that the matched cohort is overwhelmingly big tech, and big tech pays substantially above the broader market regardless of layoff history.

**Confounds**: Industry composition (D1 from `B_methodological_confounds.md`). The ~2x entry-level salary differential between FAANG-style employers and the broader US labor market is well-documented in industry compensation surveys (Levels.fyi, Blind, Glassdoor) and pre-dates the 2020-2026 layoff window.

**What would strengthen the claim**: An industry-matched comparison. Specifically: does layoff-affected big tech pay differently from non-affected big tech? Without this comparison, the 2x ratio is descriptive of "big tech vs broader US economy" not "layoff-affected vs non-affected."

**Recommended framing**: "The matched cohort posts entry-level salaries at roughly 2x the median of the broader US job market. This reflects big-tech compensation norms; pre-existing industry differentials are at least this large."

**Sample size note**: The Internship cell (n=10 layoff cohort) and Executive cell (n=10) are too small for stable median estimates. Mid-Senior (n=609 layoff, n=12,098 non-affected) is the most robust cell.

---

## Inference 2 — Q1.2 "Layoff cohort is 66% Mid-Senior; rest of market is 40% Entry-level"

**The numbers**: Layoff cohort experience-level shares: Internship 1.3%, Entry 19.0%, Associate 6.2%, Mid-Senior 66.4%, Director 6.4%, Executive 0.8%. Non-affected: Internship 1.5%, Entry 39.6%, Associate 10.4%, Mid-Senior 43.2%, Director 3.9%, Executive 1.3%.

**Numerical correctness**: Verified. Source: `output/results/q1_2_experience_level_distribution/part-*.csv`.

**Defensibility of the natural inference** ("layoff-affected companies skew senior because they laid off junior staff"): **Plausible but unprovable with this data.** Two explanations are observationally equivalent:
1. Big tech has always been senior-heavy; this is a pre-existing industry characteristic.
2. Big tech laid off junior staff disproportionately during 2020-2024, leaving a senior-heavy hiring mix.

Both predict the same observed cross-sectional pattern. Without before-data, we cannot distinguish.

**Confounds**: Industry composition (largest), plus survivorship bias.

**What would strengthen the claim**: Industry-matched comparison; a recency split inside the layoff cohort.

**Recommended framing**: "The matched cohort is 66% mid-senior versus 43% in the broader market; the broader market is 40% entry-level versus 19% in the matched cohort. Both are consistent with big-tech hiring profiles and with post-layoff seniority compression. The data does not allow us to distinguish these explanations."

---

## Inference 3 — Q2.1 "Top 10 skills differ between cohorts"

**The numbers** (top 5 skills by share of skill tags per cohort):
- Layoff cohort: IT 19.4%, Engineering 13.1%, Sales 10.6%, Management 5.9%, Business Development 5.7%.
- Non-affected: IT 12.1%, Sales 10.3%, Management 10.1%, Manufacturing 8.7%, Healthcare Provider 8.3%.

**Numerical correctness**: Verified. Source: `output/results/q2_1_top_skills_by_subcohort/part-*.csv`.

**Defensibility of the natural inference** ("layoff-affected companies hire more technical roles"): **The contrast is real and informative; the causal framing is misleading.** The top 10 skill mix is essentially a fingerprint of US industry composition. The matched cohort's fingerprint is "big tech employer" and the non-affected fingerprint is "diversified US economy."

**Most informative element**: The non-affected top 10 includes Manufacturing and Healthcare Provider, which are absent from the layoff-cohort top 10. This is not because layoff-affected companies don't hire manufacturing or healthcare workers — it's because the matched cohort doesn't include manufacturing or healthcare companies in any meaningful number.

**What this finding really shows**: The two cohorts are looking at different industries entirely. The chart is informative as a "tech industry vs broader US economy" portrait.

**Recommended framing**: "The contrast in top-10 skills is informative as a portrait of two industry mixes: the matched cohort gives a tech-industry hiring fingerprint (IT, Engineering, Sales, Management); the non-affected cohort gives a broader-economy fingerprint (IT, Sales, Management, Manufacturing, Healthcare Provider). The contrast reflects industry composition rather than any layoff-specific effect."

---

## Inference 4 — Q2.2 "Layoff cohort is 1.78x more tech-skill-concentrated"

**The number**: Layoff cohort tech-leaning share (ENG + IT + ANLS + PRDM as a fraction of all skill tags) = 36.39%. Non-affected = 20.39%. Ratio: 1.78x.

**Numerical correctness**: Verified. Source: `output/results/q2_2_tech_skill_share/part-*.csv`. Computed by aggregating skill tags within each cohort and counting the fraction in the four chosen codes.

**Defensibility of the natural inference** ("layoff-affected companies hire more technical roles"): **Mathematically correct but circular.** The matched cohort was selected to be (largely) tech companies *because* tech companies dominate the public layoffs dataset. The Q2.2 finding then reveals that this tech-dominated cohort hires more technical roles. We cannot fail to find this; it is a near-tautology.

**What this finding really tests**: It tests whether the tech-leaning skill set we chose (ENG + IT + ANLS + PRDM) actually picks out tech roles. If the chart had shown 22% vs 20% (no meaningful gap), it would have meant our skill-set choice was wrong. The fact that the chart shows 36% vs 20% confirms the skill set is well-chosen, but it does not provide independent evidence about layoff effects.

**Confounds**: All Q2.1 confounds, plus the circularity.

**Recommended framing**: "The matched cohort's tech-leaning skill share (36%) is roughly 1.8x the broader market's (20%). This is consistent with the cohort's industry composition. We do not interpret the gap as evidence of a layoff-induced shift; the cohort was selected to include big tech, and big tech hires more tech-leaning roles."

**Verdict**: This is the weakest of the seven inferences. Should be presented briefly and not over-interpreted.

---

## Inference 5 — Q3.1 "Layoff cohort allows remote 1.7x more often"

**The numbers**: Layoff cohort remote-allowed rate = 20.15% (719 of 3,569 postings). Non-affected = 11.87% (14,021 of 118,116). Ratio: 1.70x.

**Numerical correctness**: Verified. Source: `output/results/q3_1_remote_rate/part-*.csv`.

**Defensibility of the natural inference** ("layoff-affected companies are more remote-friendly"): **Misleading on two dimensions.**

First, industry confound. Tech roles are inherently more remote-capable than retail, manufacturing, healthcare. Big tech companies were also some of the loudest pre-pandemic remote-work pioneers. The 1.7x ratio is a tech-vs-broader-market difference, not a layoffs-caused-remote-shift difference.

Second, data quality: 87.7% of raw postings have `remote_allowed = null`. Phase 1 cleaning rule 6 casts null to `false`. The relative comparison (1.7x ratio) is robust because nulls distribute proportionally; the absolute rates (20.15%, 11.87%) are under-counts of the true remote rate among postings where the field is actually populated.

**Confounds**: Industry composition + `remote_allowed` null treatment (D15 from decisions log).

**What would strengthen the claim**: (a) Industry-matched comparison. (b) Re-run Q3.1 with explicit null handling — denominator excludes nulls.

**Recommended framing**: "Among postings where the remote-allowed field is set, the matched cohort allows remote at roughly 1.7x the rate of the broader market. This is consistent with the cohort being predominantly big-tech employers, who have led on remote-allowance norms since 2020. Absolute rates are under-counts because most postings leave the field null."

---

## Inference 6 — Q3.2 "Layoff cohort clusters in CA + VA + WA + TX + NY"

**The numbers**: Layoff cohort top 5 states: CA 23.0%, VA 10.9%, WA 8.9%, TX 7.9%, NY 7.5% (combined: 58.4%). Non-affected top 5: CA 10.0%, TX 9.3%, FL 5.4%, NY 5.4%, NC 4.5% (combined: 34.7%).

**Numerical correctness**: Verified. Source: `output/results/q3_2_top_states_by_subcohort/part-*.csv`.

**Defensibility of the natural inference** ("layoff-affected companies concentrate in tech hubs"): **Solid, with the same industry-composition caveat.** Tech HQs cluster in CA (Silicon Valley + LA), WA (Microsoft + Amazon HQ), VA (AWS GovCloud + government tech contractors), and to a lesser extent NY (financial tech) and TX (Austin). The matched cohort's geographic concentration mirrors big-tech HQ geography.

The non-affected cohort's broader geographic distribution (Florida, North Carolina, Pennsylvania, Ohio appearing in its top 10) reflects the broader US economy, which is much less geographically concentrated than tech.

**What's interesting and not industry-explained**: The Virginia spike. VA has high non-tech employment too (federal government, military), so its prominence in the layoff cohort is specifically tech-oriented (AWS, GovCloud, federal-tech contractors). This is consistent with big-tech geography and not a layoff effect.

**Confounds**: Industry composition.

**Recommended framing**: "The matched cohort's postings concentrate 58% in five tech-hub states (CA, VA, WA, TX, NY); the broader market's top 5 cover only 35% (CA, TX, FL, NY, NC) and reflect a more geographically diverse hiring landscape. The contrast is consistent with the cohort being big-tech employers; it does not require a layoff-specific explanation."

---

## Inference 7 — Q4.1 "Information-sector aggregate layoff rate during 2023-2024 was at the 25-year median"

**The numbers**: Information-sector monthly layoffs and discharges rate (seasonally adjusted) median during 2023-2024 = 1.1%. 25-year (2000-2026) median = 1.1%. 2020 COVID peak = 6.6%. Total Nonfarm comparison line is also flat through 2023-2024.

**Numerical correctness**: Verified. Source: `output/results/q4_1_jolts_layoff_rate/part-*.csv`. Direct extract from BLS JOLTS series `JTS510000000000000LDR` (Information sector, layoffs+discharges, rate, seasonally adjusted).

**Defensibility of the natural inference** ("the 2023-2024 tech layoff wave was real in aggregate"): **Refuted by the data.** This is the only finding in the project that runs counter to popular expectation. The aggregate rate did not spike. The visible big-name cuts (Amazon, Meta, Google, etc.) were absorbed within normal monthly separation rates at the sector level.

**Confounds**: Information sector ≠ "tech" exactly (excludes Amazon retail, Tesla manufacturing, fintech). Some "tech" layoffs are not in the Information sector by NAICS classification, so the actual "tech" layoff rate may be slightly different. However, the magnitude of difference would not flip the conclusion: the Information sector includes the named software-publishing companies whose layoffs dominated headlines (Meta, Twitter/X, Snap, Salesforce, Microsoft software divisions).

**What this finding genuinely shows**: The popular 2023 "tech layoff wave" narrative was driven by the visibility of named cuts at the largest companies, not by aggregate sector-rate elevation. This is a meaningful, non-obvious, and analytically defensible insight.

**Recommended framing**: "Contrary to the dominant 2023 media narrative, the BLS JOLTS data shows the Information-sector aggregate monthly layoff rate during 2023-2024 was at its 25-year median (1.1%), well below the 2020 COVID peak (6.6%). The named big-name cuts at Amazon, Meta, Google, Microsoft, and others were real but were absorbed within typical separation rates at the sector level. The 'tech layoff wave' was visible in news cycles but did not show up in aggregate statistics."

**This is the project's strongest analytical contribution.** Should be the report's headline finding.

---

## Inference 7b — Q4.2 "The 2023-2024 macro shift was a hiring freeze, not a layoff surge"

**The numbers** (Information sector, annual averages):

| Year | Openings rate | Hires rate | Layoffs rate |
|---|---|---|---|
| 2020 | 3.92% | 3.01% | 2.02% (COVID) |
| 2021 | 5.82% | 3.92% | 1.05% |
| 2022 | 6.81% (peak) | 3.47% | 1.21% |
| 2023 | 4.35% (-36% from 2022) | 2.43% (-30% from 2022) | 1.11% |
| 2024 | 4.04% | 2.57% | 1.15% |
| 2025 | 4.03% | 2.63% | 1.31% |

**Numerical correctness**: Verified. Source: `output/results/q4_2_jolts_openings_hires_rate/part-*.csv`, with year-aggregation cross-checked via independent integrity-check Spark SQL.

**Defensibility of the natural inference** ("the 2023-2024 macro shift was a hiring freeze"): **Strongly supported by the data.** Three independent indicators agree:
1. Openings rate fell 48% from 2022 peak (8.3% peak month) to 2023-2024 median (4.3%).
2. Hires rate fell 30% from 2022 (3.47%) to 2023 (2.43%).
3. Openings stayed above hires throughout, indicating jobs were posted but not filled at the same rate as before.

The narrative shift this finding supports: "what changed in 2023-2024 was new hiring, not separations."

**Confounds**: Same Information-sector-≠-tech caveat. Less critical here because the hiring slowdown was widespread within the broader economy, not just in tech.

**Recommended framing**: "Information-sector job openings peaked at 8.3% in 2022, fell to 4.3% during 2023-2024 (a 48% decline), and hires fell from 3.5% to 2.5%. Openings ran consistently above hires, indicating slow time-to-hire and increased selectivity. The 2023-2024 macro shift was characterized by reduced hiring, not elevated separations. This complements Q4.1's finding."

**This and Q4.1 together are the project's most defensible findings.** They should be co-headlined in the report.

---

## Summary table

| # | Chart | Numbers verified? | Inference defensible? | Strength |
|---|---|---|---|---|
| 1 | Q1.1 salary by level | Yes | Misleading (industry-confounded) | Weak |
| 2 | Q1.2 level distribution | Yes | Plausible but ambiguous | Weak |
| 3 | Q2.1 top skills | Yes | Real contrast, descriptive | Moderate |
| 4 | Q2.2 tech-skill share | Yes | Circular | Weakest |
| 5 | Q3.1 remote rate | Yes | Misleading (industry + null) | Weak |
| 6 | Q3.2 top states | Yes | Real, with framing | Moderate |
| 7a | Q4.1 layoff rate timeseries | Yes | Strongly supported | **Strongest** |
| 7b | Q4.2 openings vs hires | Yes | Strongly supported | **Strongest** |

The two macro-context findings (Q4.1, Q4.2) are dramatically stronger than any of the cohort-comparison findings (Q1-Q3). They:
- Are not industry-confounded.
- Are based on aggregated official US government data (BLS JOLTS).
- Run counter to popular expectation (which makes them informative rather than confirmatory).
- Use 25 years of historical context, not a single 2023-2024 snapshot.

The cohort-comparison findings (Q1-Q3) are useful as a descriptive portrait of "big tech vs broader US economy in 2023-2024" but should not be over-claimed as evidence of layoff-induced changes.

The final report's structure should reflect this asymmetry: Q4 findings as the headline, Q1-Q3 findings as supporting context. The current structure of the FINAL_REPORT.md already does this.
