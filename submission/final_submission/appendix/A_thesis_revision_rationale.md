# Appendix A — Thesis Scope and Boundaries

This appendix records, in detail, the empirical claims that the thesis stated in `FINAL_REPORT.md` §1 supports, the claims it explicitly does not extend to, and the data-driven reasons for the boundary. It is the analytical companion to §7 (Scope, confounds, limitations) and exists so that any reader extending or critiquing this work has a single page that fixes the contract between the data, the methods, and the conclusions.

## A.1 The thesis, restated

> In 2023-2024, do companies named in the public 2020-2026 layoffs record (the "layoff-listed" cohort) hire differently from the rest of the US LinkedIn job market along salary, experience level, skill composition, geography, and remote allowance — and how do those cross-sectional differences sit inside the 25-year longitudinal record of US hiring, openings, and separations captured in BLS JOLTS data for Total Nonfarm and the Information sector?

Two parts. The cross-sectional cohort comparison answers the first part using the LinkedIn 2023-2024 postings snapshot. The longitudinal JOLTS reading answers the second part using a sector-aggregate time series with monthly resolution from 2000-12 through 2026-02. The two parts are designed to inform each other; neither is sufficient on its own to support the report's headline interpretation.

## A.2 Claims this design supports

The design supports the following classes of empirical claim, each with one or more queries and charts in the deliverable.

**Cross-sectional descriptive claims about 2023-2024 LinkedIn hiring at named layoff-listed employers vs. the rest of the market.** Concretely: median USD salary by experience level per cohort (Q1.1), share of postings by experience level per cohort (Q1.2), top-10 skill-tag distribution per cohort (Q2.1), share of skill tags in a tech-leaning bucket per cohort (Q2.2), share of postings remote-allowed per cohort (Q3.1), and top-10 states by posting share per cohort (Q3.2). Every reported number is a direct group-by aggregation against `postings_tagged`, with sample sizes labeled on every chart.

**Longitudinal aggregate claims about US hiring, openings, and separations from 2000-12 through 2026-02 for two industries.** Concretely: monthly seasonally adjusted layoffs-and-discharges rate for Total Nonfarm and the Information sector (Q4.1), and monthly job openings rate and hires rate for the Information sector (Q4.2). Each reported median, peak, or annual average is computed from BLS-published monthly observations on a single SQL aggregation.

**Joint integrative claims about how the two parts of the thesis fit together.** Concretely: that named layoff-listed employers continued to post at elevated rates and at a senior-and-technical profile during the same window in which aggregate Information-sector openings and hires fell sharply while Information-sector separations stayed at long-run-median levels. This is the single most important interpretive claim in the report and the one that the dual-data design is built to support.

## A.3 Claims this design does not support

The design does not support — and the report does not extend to — the following.

**Causal claims that "having had layoffs" caused the cohort hiring profile differences.** The 2023-2024 LinkedIn snapshot has no pre-layoff "before" period for any of the matched companies, so any cohort difference observed in 2023-2024 cannot be attributed to a within-employer change attributable to layoffs. A causal study would require either an industry-matched control (layoff-listed big tech vs. non-listed big tech) or a longitudinal panel of postings per company across multiple years; neither is available in the chosen data.

**Industry-controlled cohort claims.** The matched cohort is dominated by the largest US tech-and-tech-adjacent employers because those are the names that produce public layoff coverage, which means the comparison set in this design ("the rest of the market") is the broader US economy rather than non-listed big-tech. Several of the differences in §5 of the report — particularly the geographic concentration in tech-hub states and the 1.78x tech-skill concentration — are partly a portrait of US industry composition. The report frames each finding consistent with this scope and §6's integrated interpretation reads the cohort profile as a continuation of a long-standing big-tech employer profile rather than as a layoff-induced shift.

**Per-company longitudinal claims.** Because the postings data is a single 2023-2024 snapshot, no claim about how a specific employer's hiring profile changed over time can be supported by the cohort data. Any such claim would require pre-2023 postings data at the same employer-level granularity, which the chosen data does not include.

**Sector-equivalent "tech" claims.** BLS NAICS 51 (Information) is the closest publicly-available sector proxy for "tech" but excludes Amazon (NAICS 4541, electronic shopping), Tesla (NAICS 33611, motor-vehicle manufacturing), and large segments of fintech (NAICS 522/523). JOLTS findings in §5.4 are framed as "tech-adjacent sector" findings, not "all-tech" findings, and the Total Nonfarm series is reported alongside Information to provide a baseline.

**Inferential claims about uncertainty.** The report uses point-estimate language throughout and does not compute confidence intervals or perform formal significance tests. Sample sizes for the headline cells are large enough that the reported gaps are not plausibly noise, but a formal noise-baseline (bootstrap resampling) is listed as a natural extension in §9 and `appendix/E_action_items.md` rather than included here.

## A.4 Why the data sets the scope this way

Three structural features of the chosen data sources determine the boundary above. They are not weaknesses of the analysis; they are properties of the public datasets that shape what can be defensibly concluded.

First, the **LinkedIn postings dataset is a 2023-2024 snapshot**. Kaggle's `arshkon/linkedin-job-postings` covers postings with `original_listed_time` falling in 2023-2024; no 2018-2022 snapshot is available at comparable granularity from the same scraping methodology. Per-company longitudinal hiring claims at the LinkedIn level are therefore unavailable.

Second, the **layoffs dataset is editorially curated and biased toward large, public events**. The cohort it produces, after the company-name normalization and the cleaned-postings join, is dominated by the largest US tech-and-tech-adjacent employers. The cohort is therefore best read as "publicly named layoff events at companies still actively posting on LinkedIn in 2023-2024," and the comparison set is "all other 2023-2024 US LinkedIn postings," which is the broader economy rather than an industry-controlled control.

Third, the **JOLTS time series is sector-aggregate, not employer-specific**. JOLTS provides 25 years of monthly resolution at the (industry, metric) level — exactly the longitudinal axis the postings data lacks — but cannot answer per-employer questions. The two data sources therefore complement each other on resolution: postings is high-resolution at the employer level and zero-resolution in time before 2023; JOLTS is high-resolution in time and zero-resolution at the employer level. The report's design uses each at the resolution it supports.

## A.5 What follows from these boundaries

Two interpretive consequences follow.

**The report's headline interpretation is the single statement most consistent with what the cohort comparison and the JOLTS macro data jointly show.** That interpretation, repeated from `FINAL_REPORT.md` §6: in 2023-2024 the most visible US tech-and-tech-adjacent employers continued posting at premium senior-and-technical profiles while the aggregate Information-sector underwent a hiring slowdown rather than a separation surge. The visible-layoffs and continuing-hiring observations are both true; the JOLTS data explains how both can be true simultaneously.

**The popular "2023 tech layoff wave" narrative is decisively challenged by the JOLTS reading.** The aggregate Information-sector layoffs-and-discharges rate during 2023-2024 sat at the 25-year median; openings fell 38-46% (annual or monthly basis); hires fell 28% — these are the empirical signatures of a hiring freeze, not a layoff wave. This single claim is the analytic contribution of the report best supported by the data.

## A.6 What an extended design would add

Three extensions, prioritized in `appendix/E_action_items.md` and §9 of the report, would each lift specific scope boundaries.

1. **Industry-matched cohorts** (T2.1 in `E_action_items.md`) would isolate any layoff-specific effect from the industry-composition effect that dominates the current cohort comparison. Implementation requires a NAICS resolver applied to the 24,315 postings companies.

2. **Recency stratification within the cohort** (T2.2) would split the layoff-listed cohort by whether the most recent layoff was in or before 2023, producing a three-cohort split that is the closest the available data gets to a quasi-temporal natural experiment.

3. **Bootstrap noise baselines** (T2.3) would convert the report's point-estimate language into ratio-vs-noise-distribution language for each cohort metric, producing a formal noise-adjusted reading of the headline gaps.

None of these extensions invalidate the conclusions of the current report. Each extends the empirical reach of a future revision while leaving the present scope intact.
