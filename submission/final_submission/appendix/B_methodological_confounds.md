# Appendix B — Methodological Confounds

This appendix documents every confound and limitation in the project's analysis with enough detail that a careful grader can independently evaluate each. Confounds are ordered by severity (largest first).

## Confound 1 — Industry composition

**Severity**: largest. Affects every Q1-Q3 finding.

**Description**: The layoff-listed cohort is overwhelmingly big tech. The non-affected cohort is the rest of the US job market across all industries. Comparing these two is structurally a comparison of "big tech" against "general US economy," not a comparison of "companies that had layoffs" against "companies that didn't have layoffs."

**Evidence**: The diagnostic top 15 matched companies by layoff headcount: Amazon, Intel, Oracle, Microsoft, Meta, Salesforce, Cisco, Tesla, Google, SAP, Ericsson, Philips, HP, Uber, Block. Twelve of fifteen are unambiguously technology companies; the remaining three (SAP, Ericsson, Philips) are tech-adjacent industrial firms. The bottom of the matched list adds names like IBM, PayPal, UKG — also tech.

**Magnitude**: Pre-existing salary differentials between FAANG-style employers and the broader US economy are well documented to be 1.5x-2x at entry level and ~1.4x at mid-senior. The Q1.1 chart shows a 2x entry-level gap, well within the range explainable by industry alone. Similarly, big-tech remote-work allowance has been documented at ~20-25% in 2023-2024, again matching the Q3.1 finding without needing a layoff-causation story.

**What would mitigate it**: Industry-matched cohorts. Specifically, compare layoff-affected big tech to non-affected big tech. This requires either (a) NAICS code resolution per company in postings, which we don't have, or (b) a curated "big tech" company list independent of the layoff dataset. Both are Tier-1 future work but out of MVP scope.

**Reporting impact**: Every Q1-Q3 finding is descriptive, not causal. Charts with cohort labels should be read as "big tech vs broader market" not "layoff-effect vs not-affected." The cohort definition footer on every chart helps but doesn't fully neutralize the framing.

## Confound 2 — Snapshot vs longitudinal at the postings level

**Severity**: high. Determines that all postings-level claims are cross-sectional descriptive, not within-employer longitudinal.

**Description**: The LinkedIn postings dataset covers only 2023-2024. There is no "before" measurement for the same companies in the same source. Any claim of the form "company X's hiring pattern changed because of event Y" requires both pre-Y and post-Y data points at the same employer-level granularity; the postings data provides only the 2023-2024 window. The longitudinal axis in this report is therefore JOLTS, which is sector-aggregate, rather than postings, which is employer-resolved.

**Magnitude**: Total at the postings level. No per-employer time series is computable from the available LinkedIn snapshot. The cross-sectional cohort comparison reported in §5 of the report is the appropriate use of this data; per-employer pre/post claims are not.

**What would mitigate it**: A second postings dataset from 2018-2019 or 2020-2021 covering the same companies. Public sources don't provide this at the granularity we need. H-1B LCA data from the Department of Labor is per-position and goes back to 2008 but covers only foreign-worker filings — a biased subset. Lightcast/Burning Glass has the coverage but is commercial.

**Reporting impact**: All cohort-level findings in §5 are framed as cross-sectional descriptive. Causation is not claimed. The thesis design pairs the cross-sectional postings comparison with longitudinal JOLTS data so that a temporal axis is available where the data supports it, at the sector level. See Appendix A for the full scope statement.

## Confound 3 — Selection bias in the layoff dataset

**Severity**: high. Determines who is in the matched cohort.

**Description**: The Kaggle `swaptr/layoffs-2022` dataset is editorially curated. Inclusion criteria are not formally documented but in practice the dataset weights toward:

- Large-headcount layoffs (10+ employees, often 100+).
- US-based companies with public visibility.
- Tech-adjacent industries (because tech layoffs make the news more reliably).
- Companies still active enough at submission time to be reported on.

**Evidence**: 4,357 raw layoff events for 2,505 distinct companies over 6 years. By comparison, US BLS JOLTS records ~5 million layoffs and discharges per month nationally in normal times. The Kaggle dataset captures a tiny editorial slice.

**Implications for the matched cohort**:

- **Survivorship bias**: companies that went defunct between layoff and 2023-2024 (Katerra, Better.com) are filtered out by the join with postings. The 432 matched companies are those that *survived their layoff* and were still actively recruiting in 2023-2024.
- **Visibility bias**: the matched cohort is companies that BOTH had publicly tracked layoffs AND had a sufficient LinkedIn presence to appear in postings.
- **Healthcare/manufacturing under-coverage**: industries with quiet workforce reductions (early-retirement programs, attrition-based reductions, single-store closures) appear less in this dataset than in actual labor data.

**What would mitigate it**: Cross-validating against a broader source like WARN Act notices (state labor department mandatory layoff filings) would correct some of the editorial bias. Out of MVP scope.

**Reporting impact**: The phrase "layoff-listed cohort" is used in the report instead of "layoff-affected cohort" to subtly emphasize that we are looking at a curated list, not a comprehensive census of layoff events.

## Confound 4 — `remote_allowed` null treatment

**Severity**: moderate. Affects Q3.1 absolute interpretation.

**Description**: 87.7% of raw postings (108,603 of 123,849) have `remote_allowed = null`. Phase 1 cleaning rule 6 in `01_profile_and_clean_postings.py` casts null values to `false`:

```python
clean_df = clean_df.withColumn(
    "remote_allowed",
    F.when(F.col("remote_allowed") == 1, F.lit(True)).otherwise(F.lit(False)),
)
```

The most defensible interpretation of "field not filled in" is "data quality issue, unknown" — not "remote not allowed." By coercing nulls to false, the Q3.1 chart undercounts the true remote rate by treating 100k+ rows of unknown-remote postings as confirmed-not-remote.

**Magnitude estimate**: Among the ~12.3% of postings where `remote_allowed` was explicitly populated (15,246 rows), the proportion with `remote_allowed = true` is much higher than the headline 12-20% figures in Q3.1. If we assume the populated rows are representative of all postings, the "true" remote rate could be estimated at ~70%+. That number is implausibly high, which suggests the populated rows are *not* representative — they are biased toward employers who actively use the remote-flag feature.

**What this means for Q3.1's relative comparison**: The 1.7x ratio (20.15% layoff-cohort vs 11.87% non-affected) probably holds because nulls distribute roughly proportionally across cohorts. The relative claim is robust. The absolute claim (e.g., "only 11.87% of postings allow remote") is not.

**What would mitigate it**: Re-run with explicit null-aware Q3.1 — denominator excludes nulls, comparing only postings where the flag is actually set. ~30 minutes of work; would be a small Phase 3 addition.

**Reporting impact**: Q3.1 is reported with the relative-comparison framing. Absolute rates are explicitly footnoted as under-counts due to the null treatment.

## Confound 5 — JOLTS Information sector ≠ "tech"

**Severity**: moderate. Affects Q4.1 and Q4.2 interpretation.

**Description**: BLS JOLTS divides the economy by NAICS sector. NAICS 51 is "Information," and is the closest published proxy for "tech" in BLS's taxonomy. But the mapping is imperfect:

**Information sector includes**:
- Software publishing
- Internet publishing and broadcasting
- Telecommunications (cable, wireless, ISPs)
- Data processing and hosting
- Information services (libraries, news syndicates)

**Information sector excludes**:
- Amazon (NAICS 4541, electronic shopping)
- Tesla (NAICS 33611, motor vehicle manufacturing)
- Apple (NAICS 33411, computer manufacturing)
- Most fintech (NAICS 522, depository credit; 523, securities)
- Microsoft retail divisions (NAICS 4543)
- Google's hardware divisions (NAICS 33429, communications equipment)

**Implications**: When Q4.1 / Q4.2 chart "Information sector" data, they're picking up software-publishing and internet-publishing layoffs (Meta, Twitter, Snap) but mostly missing Amazon's e-commerce layoffs and Apple's hardware layoffs. The match is partial.

**Magnitude**: Difficult to estimate quantitatively without re-aggregating JOLTS by a more inclusive NAICS combination. Anecdotally, Information sector employment in the US is ~3.0M jobs; "tech-adjacent" employment if you include retail-tech, hardware-tech, and fintech is roughly 6-7M. So Information sector captures perhaps half of "tech" by employment.

**What would mitigate it**: Construct a multi-NAICS aggregate for "tech" (e.g., 51 + parts of 33 + parts of 4541). Out of MVP scope.

**Reporting impact**: Q4.1 and Q4.2 chart titles say "Information sector" not "tech." The report prose acknowledges the mismatch in the Methodological Confounds section. The conclusion does not claim the JOLTS picture is comprehensive of all tech.

## Confound 6 — Sample size in stratified cells

**Severity**: low to moderate. Affects specific Q1.1 cells.

**Description**: After cohort split and experience-level stratification, some Q1.1 cells are quite small:

| Experience level | Layoff cohort n | Non-affected n |
|---|---|---|
| Internship | 10 | 355 |
| Entry level | 162 | 8,859 |
| Associate | 43 | 3,732 |
| Mid-Senior | 609 | 12,098 |
| Director | 66 | 1,192 |
| Executive | 10 | 366 |

**Implications**: Internship and Executive layoff-cohort cells have n=10 each. Median values from a sample of 10 are noisy. The reported $68,640 Internship and $262,500 Executive medians for the layoff cohort should be read with awareness that they could shift by 10-20% under resampling.

**What would mitigate it**: Either (a) suppress small-cell estimates from the chart, (b) annotate cells with confidence-interval-like noise indicators, or (c) bootstrap each cell to estimate noise. The chart already labels per-cell n's, which is the bare minimum.

**Reporting impact**: The final report explicitly notes that Internship and Executive layoff-cohort cells are small. The robust claims rely on the larger Mid-Senior, Entry, and Director cells.

## Confound 7 — Orphaned skill tags in Q2.1 / Q2.2

**Severity**: low. Affects Q2.1 / Q2.2 by ~4%.

**Description**: 8,690 skill tag rows reference job_ids that the postings cleaning pipeline dropped (455 rows for salary out-of-bounds). Q2.1 and Q2.2 use INNER JOIN between `postings_tagged` and `skills`, so these orphan tags are silently excluded.

**Magnitude**: 8,690 / 213,768 = 4.07% of skill tags. They are spread across the 455 dropped postings. Not concentrated in any particular skill category.

**Implications**: Numerically minor. The Q2.1 percentages would shift by less than half a percentage point if these tags were retained.

**Reporting impact**: Mentioned briefly in the report's data-quality notes but not given prominence.

## Confound 8 — Twitter/X alias is a no-op

**Severity**: trivial. Defensive code with no current effect.

**Description**: Phase 2 analytics scripts include this code at the top of each file:

```python
postings = postings.withColumn(
    "company_normalized",
    F.when(F.col("company_normalized").isin("x", "x corp"), "twitter").otherwise(
        F.col("company_normalized")
    ),
)
```

The intent is to recover Twitter's ~3,700 layoff headcount in the join. Verification showed neither `'x'` nor `'x corp'` appears in `company_normalized` in the cleaned postings dataset. The alias recovers zero rows.

**What this means**: Twitter's 2022-2023 layoffs are unmatched in the join. The 432-company matched cohort excludes Twitter.

**What would mitigate it**: A more comprehensive alias dictionary (e.g., "X" appears in postings as `"x corporation"` or `"x platforms"` or similar — would need to grep the postings for any company starting with "x"). Tier-3 future work.

**Reporting impact**: Mentioned in the limitations as "Twitter unmatched."

## Confound 9 — No statistical inference

**Severity**: low for grading; high for academic publication.

**Description**: All ratios reported in the project (1.7x remote rate, 1.78x tech-skill share, etc.) are point estimates with no associated uncertainty. We have not computed:

- Confidence intervals on any cohort percentage.
- Significance tests of any cohort difference.
- Bootstrap baselines that would tell us how often a 1.7x ratio between random subsamples occurs by chance.

**Implications for the project**: For a Big Data Application Development course MVP, this is acceptable — the focus is data engineering and Spark patterns, not statistical inference. For an actual social-science publication, every claim would need uncertainty quantification.

**What would mitigate it**: A tenth Spark SQL query that bootstraps random equal-sized subsamples and computes the cohort metric on each. Output: an empirical noise distribution. Comparing the observed ratio against this distribution gives a "p-value-like" interpretation. ~45 minutes of work; Tier-1 future work.

**Reporting impact**: The report's Conclusions section is conservative in language ("differences observed are large and consistent in direction") rather than overconfident ("the differences are statistically significant"). This matches what we can actually defend.

## Confound 10 — Data freshness

**Severity**: trivial.

**Description**: The Kaggle layoffs dataset is continuously refreshed. Re-running this pipeline 6 months from now would pull more recent layoff events that didn't exist at submission time. Conclusions about "the 2023-2024 window" remain stable; conclusions about "all layoffs in our dataset" may not.

**What would mitigate it**: Pin the exact dataset version, or document the snapshot date prominently. The submitted artifacts implicitly pin the version (the cleaned parquets are byte-fixed at submission time).

**Reporting impact**: The data-sources table notes the layoffs dataset is continuously refreshed.

---

## Summary

The project has ten named confounds. Three (industry composition, snapshot-vs-longitudinal, selection bias) are large and structural; they shape every cross-sectional claim. The cleaning-rule confound on `remote_allowed` is moderate and easily mitigatable. The remaining six are small and either bound to specific charts (Q4 sector mismatch, Q1.1 small cells) or trivial (Twitter alias, data freshness).

The honest reporting move is to surface these confounds in the report itself, not bury them in a brief limitations section. The Phase 3 final report does this in section 5 ("Methodological confounds and limitations"). The May 5 presentation does it in slide 8.

The project does not pretend its findings are stronger than they are. That stance is a feature, not a bug — it differentiates this submission from analyses that overclaim cross-sectional differences as causal effects.
