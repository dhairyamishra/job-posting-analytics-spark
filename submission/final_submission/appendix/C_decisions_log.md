# Appendix C — Decisions Log

This appendix documents the fifteen major engineering and analytical decisions made during the project, with the merit and demerit of each. The intent is to make the project's reasoning auditable: a grader or reviewer should be able to read this and understand both *what* was decided and *why*, including where decisions had real costs.

Decisions are ordered roughly by phase: data and source decisions first, then engineering decisions, then analytical decisions, then late-stage decisions.

---

## D1 — Solo team with four data sources

**Decision**: Pursue the project as a solo team (professor-approved per `IMPLEMENTATION_PLAN.md`), starting with two primary Kaggle datasets and adding a third (skills mapping) and fourth (BLS JOLTS) as the project matured.

**Merit**:
- Course rubric requires "at least one data source per team member"; solo means at least one. Three (later four) is over-delivery.
- Cross-source joins (postings ↔ layoffs ↔ skills, postings ↔ JOLTS) demonstrate real Spark application beyond single-table profiling.
- The fourth source (JOLTS) ended up producing the project's strongest finding.

**Demerit**:
- More sources to profile, clean, and document. Each additional source adds ~30-60 minutes of report-writing overhead.
- Solo deadline pressure left less time for analytical depth (statistical inference, industry-matching).

**Net verdict**: Net merit. JOLTS in particular was a high-ROI late add.

---

## D2 — Spark-only architecture, no notebooks, scripts via spark-submit

**Decision**: Implement everything as Python scripts (`scripts/01_*.py` through `scripts/10_*.py`), invoked via `spark-submit` inside a Docker container. No Zeppelin, Jupyter, or interactive shells.

**Merit**:
- Reproducible end-to-end: a single Docker command runs the entire pipeline.
- Logs are first-class deliverables (`output/logs/*.log`) — every script's stdout is the audit trail.
- No Jupyter session state to lose.
- Easier for a grader to re-execute on their machine.

**Demerit**:
- Less interactive than a notebook would be. A grader skimming on a phone has to dig through `.log` files instead of seeing rendered cells.
- The course explicitly accepts notebooks (Zeppelin, with .ipynb + PDF). We did not use them.
- Cell-by-cell exploratory work happened locally but isn't preserved for review.

**Net verdict**: Net merit for engineering hygiene. Slight cost in grader-friendliness, mitigated by clean profile CSVs and structured run logs.

---

## D3 — Long-form profile CSV schema (`dataset, column, metric, value`)

**Decision**: Every profiling script writes output as a uniform long-form CSV with four columns. All four sources produce profile CSVs in the same shape.

**Merit**:
- Uniform shape across all four sources. A grader can open any of them in any tool with the same expectations.
- Self-describing: each row identifies which dataset, which column, what metric, and what value.
- Easy to merge or filter across sources for cross-source comparisons.
- Schema is stable as we added new metrics (no column changes when we added top-10 counts, for example).

**Demerit**:
- Slightly verbose vs a wide-form summary that has one row per column with all metrics as separate columns.
- Some metrics that don't fit the long-form pattern (e.g., `describe()` output with multi-row min/max/mean/stddev) are not captured in the CSV — they're in the stdout logs only.
- Categorical "top-10 value counts" are also not in the profile CSV; only in stdout logs.

**Net verdict**: Net merit. The discipline of uniform shape was the right call. Missing categorical/numeric describe in the CSV is a gap but acceptable given they live in the logs.

---

## D4 — `company_normalized` regex for the join key

**Decision**: Both `01_profile_and_clean_postings.py` and `03_profile_and_clean_layoffs.py` derive a `company_normalized` column from raw company names using identical regex:

```python
F.lower(F.trim(F.regexp_replace(F.col("company_name"),
    r"(?i)\s*(inc|corp|corporation|llc|ltd|limited)\.?$", "")))
```

**Merit**:
- Simple and deterministic. Same regex on both sides means the join is well-defined.
- Handles the most common corporate-name variations: Inc, Corp, Corporation, LLC, Ltd, Limited, with optional period.
- One line of code per script. Easy to read and audit.

**Demerit**:
- Leaky. 17.25% company-level join hit rate (verified by Step 0 diagnostic).
- Does not handle:
  - Renames (Twitter → X). Verified to be a real loss; X corp is unmatched.
  - "Meta Platforms" vs "Meta" (likely caught by the regex but not verified).
  - Subsidiaries (Whole Foods → Amazon, GitHub → Microsoft). Unmatched.
  - Punctuation, accents, non-Latin characters in international company names.
  - Company names with multiple normalizations (e.g. "Apple Inc." vs "Apple, Inc.").

**Net verdict**: Acceptable for MVP. A more complete approach would be (a) a curated alias dictionary for the top 50 layoff companies by headcount, plus (b) fuzzy-match (Levenshtein) for the rest. Both out of MVP scope. Listed as future work.

---

## D5 — Step 0 diagnostic gate before Phase 2

**Decision**: Build a small diagnostic script (`04_diagnostic_join_check.py`) to measure the postings-layoffs join hit rate *before* writing any analytics queries. Treat the result as a go/rescope decision point.

**Merit**:
- This was the smartest decision in the project.
- Surfaced the headcount-weighted-vs-company-count distinction (~60-70% by headcount, 17.25% by company) that became central to the report's framing.
- Forced explicit acknowledgment that the matched cohort is "big tech that survived layoffs and kept hiring," not "companies harmed by layoffs."
- Prevented building 6 analytics queries on a misunderstood foundation.
- Produced a reusable artifact (`output/diagnostics/join_hit_rate/` summary CSV) that the final report cites directly.

**Demerit**:
- None.

**Net verdict**: Pure win. The Step 0 gate is the engineering pattern most worth replicating in future data projects.

---

## D6 — Cohort split as `layoff_affected` vs `non_affected`

**Decision**: Tag every posting as either `layoff_affected` (its company appears in the layoffs record) or `non_affected` (otherwise). All Phase 2 analytics split by this binary cohort.

**Merit**:
- Simple, binary, easy to compute.
- Supports all 6 cohort queries cleanly via a single `subcohort` column.
- One SQL pattern (left join + CASE) replicated in each of `05_*.py`, `06_*.py`, `07_*.py`. Easy to audit.

**Demerit**:
- Labels are semantically loaded. A reader sees "affected" and "non-affected" and reasonably interprets the labels causally.
- The chart titles use these labels. Even with explanatory footers, the connotation is hard to neutralize.
- A more honest naming would be `layoff_listed` vs `not_listed` — emphasizes that the distinction is whether a name appears in a curated dataset, not whether the company was harmed.

**Net verdict**: Net merit functionally; semantic cost is real. Phase 3 report explicitly disclaims the implied causation. Future work: rename to `layoff_listed` / `not_listed` if the project were continued.

---

## D7 — Charts in pandas + matplotlib, not Spark

**Decision**: After Phase 2 produces 8 small result CSVs, render charts using pandas + matplotlib (`scripts/08_make_charts.py`). No Spark in the chart-rendering stage.

**Merit**:
- Right tool for the job. Result CSVs are kilobytes; pulling them into pandas is faster and clearer than Spark plotting.
- Matplotlib's API is well-known and documented; no friction.
- Chart code is independent of the Spark pipeline — can re-render charts without re-running queries.

**Demerit**:
- Course rubric says "use Spark for everything." A literalist grader could argue charts should also be Spark. We interpret "everything" as "all data work and analytics" — charts are presentation, not analytics.
- Adds a non-Spark stage to an otherwise Spark pipeline. Slight architectural inconsistency.

**Net verdict**: Net merit, defensible at grading time. The May 5 presentation should be ready to articulate why post-Spark rendering is the right separation of concerns.

---

## D8 — JOLTS macro add-on

**Decision**: After Phase 2 was complete, add BLS JOLTS as a fourth data source providing 25 years of monthly aggregate hiring/layoff/openings rates. Two new scripts (`09_*.py` ingestion, `10_*.py` analytics), two new charts (Q4.1, Q4.2).

**Merit**:
- Single most analytically valuable late addition.
- Only finding in the project that is *not* industry-confounded (because JOLTS is sector-aggregated, not per-company).
- Reframes the popular 2023 "tech layoff wave" narrative — the most surprising and memorable insight.
- Demonstrates the Phase 1 patterns are reusable (the new ingestion script clones the 01-03 pattern almost verbatim).

**Demerit**:
- Information sector ≠ "tech" exactly (NAICS 51 excludes Amazon, Tesla, fintech). Reported in `B_methodological_confounds.md`.
- Added late, treated as an "add-on" in `IMPLEMENTATION_PLAN.md`. The final report should treat it as first-class.

**Net verdict**: Strongest decision after Step 0 gate. Should be more prominent in the final report than its "add-on" framing implies.

---

## D9 — Honest cohort definition footer on every chart

**Decision**: Every chart includes a small footer line: "Layoff-affected = 432 companies in layoffs 2020-2026 that also posted on LinkedIn 2023-2024 (predominantly big tech). Other = all other posting companies."

**Merit**:
- Necessary disclosure. Without it, every chart silently implies causation.
- Standardized across all 8 charts. A reader sees the same definition every time.
- Accurate. The phrase "predominantly big tech" is supported by the diagnostic verification.

**Demerit**:
- Visually small and easily skimmed past. A reader looking at the headline "20.15% vs 11.87%" remote rate probably won't pause to read the small print.
- Doesn't fully neutralize the loaded `layoff_affected` axis labels.

**Net verdict**: Necessary but insufficient. The report text and presentation slides need to do additional lifting on the same point.

---

## D10 — Single binary cohort (no recency split)

**Decision**: Use a single binary cohort split (`layoff_affected` vs `non_affected`) rather than a three-way split that would further partition the layoff-listed cohort by recency of last layoff (pre-2023 vs 2023+).

**Merit**:
- Keeps the cohort definition simple and fully reproducible from a single SQL pattern.
- Each chart has 2 cohort lines instead of 3, more readable for the report.
- The binary split is sufficient to deliver the report's headline findings: the cohort-vs-broader-market gap is the empirical signal we set out to measure.

**Demerit**:
- A recency-split design would add a quasi-temporal lever to the cohort comparison. Companies whose most recent layoff was during 2023 (Meta Nov 2022, Google Jan 2023, Microsoft Jan 2023) might show different post-layoff hiring patterns than companies whose layoffs were 2-3 years earlier — a within-cohort signal the binary design cannot expose.
- The recency split is the closest the available data gets to a natural experiment.

**Net verdict**: Net merit for the current scope; the binary cohort is the right design for a descriptive cohort comparison. The recency split is queued as Tier-2 future work in `appendix/E_action_items.md` (T2.1).

---

## D11 — Tech-leaning skill set: ENG / IT / ANLS / PRDM (not MGMT / MNFC)

**Decision**: For Q2.2 (tech-leaning skill share), use the set `(ENG, IT, ANLS, PRDM)` rather than a broader `(ENG, IT, ANLS, MGMT, MNFC)` set.

**Merit**:
- The original list included MGMT (universal across industries) and MNFC (manufacturing — actively non-tech). Including them would have diluted the "tech-leaning" signal.
- The corrected list (ENG, IT, ANLS, PRDM) consists of unambiguously technical/analytical roles.
- Caught and documented during plan-tightening (see `phase2-plan-tightening` plan in `.cursor/plans/`).

**Demerit**:
- ANLS is borderline. "Analyst" can be data analyst (technical) or business analyst (less so). Using ANLS as a tech proxy is one defensible choice among several.
- The choice is somewhat arbitrary; a robustness check would test 2-3 different "tech-leaning" definitions to see if Q2.2 conclusions hold.

**Net verdict**: Net merit. Explicit acknowledgment in the report that the chosen list is one reasonable definition, not the only one.

---

## D12 — No statistical inference

**Decision**: Report all cohort differences as point estimates without confidence intervals or significance tests.

**Merit**:
- Stayed lean, kept scope focused on data engineering and Spark patterns rather than statistical methodology.
- The MVP can ship without it.

**Demerit**:
- Cannot make confidence statements. "20.15% vs 11.87% (1.7x)" is reported as a fact, but we don't know how much of that ratio is signal vs sampling noise.
- For an academic publication this would be unacceptable. For a course MVP it is acceptable, but a sharp grader could ask about it.

**Net verdict**: Acceptable for MVP. Listed as Tier-1 future work — a single Spark SQL bootstrap query (~45 minutes) would close the gap meaningfully.

---

## D13 — JOLTS Information sector chosen as tech proxy

**Decision**: For the JOLTS macro context, filter to Information sector (NAICS 51) and Total Nonfarm only. Do not aggregate across multiple "tech-adjacent" NAICS codes.

**Merit**:
- Information is the cleanest single-sector proxy for "tech" in BLS taxonomy.
- Includes software publishing, internet publishing, data processing — the obvious software-industry segment.
- One sector keeps the chart readable; multi-sector aggregation would require explanation and might confuse.

**Demerit**:
- Excludes Amazon (NAICS 4541, electronic shopping), Tesla (NAICS 33611, motor vehicle manufacturing), Apple (NAICS 33411, computer manufacturing), and most fintech (NAICS 522/523).
- Information sector includes some non-tech sub-sectors (motion picture, sound recording) that aren't really "tech."
- The match between "JOLTS Information sector" and "tech as colloquially understood" is partial.

**Net verdict**: Best available choice for the data we had. Future work would be to construct a multi-NAICS aggregate, but that requires JOLTS data at sub-sector granularity which is more complex to ingest.

---

## D14 — Manual JOLTS download, not API integration

**Decision**: Download the JOLTS time-series files manually via PowerShell `Invoke-WebRequest` to `data/jolts/`. Do not integrate with the BLS API.

**Merit**:
- Simpler. No API key, no rate limits, no retry logic.
- Fast. Whole download is ~18 MB and takes 5 seconds on a reasonable connection.
- Reproducible: the BLS files are stable and rarely change format.

**Demerit**:
- Snapshot ages. Re-running this pipeline 6 months from now would still use the same data unless a user manually re-downloads.
- For a real production pipeline, API integration would be standard.

**Net verdict**: Right call for MVP. The submission notes the dataset is a snapshot.

---

## D15 — Treating `remote_allowed` null as `false` in Phase 1 cleaning

**Decision**: `01_profile_and_clean_postings.py` cleaning rule 6 casts `remote_allowed` null to `false`:

```python
clean_df = clean_df.withColumn(
    "remote_allowed",
    F.when(F.col("remote_allowed") == 1, F.lit(True)).otherwise(F.lit(False)),
)
```

**Merit**:
- Simple cleaning rule, applied consistently.
- Produces a clean Boolean column with no nulls — easy to use downstream.

**Demerit**:
- Probably wrong from a data-semantics standpoint. 88% of raw postings are null on this field; the most natural interpretation is "data quality issue, unknown" — not "remote not allowed."
- The Q3.1 chart undercounts the true remote rate by treating ~108k unknown-remote postings as confirmed-not-remote.
- The relative comparison (1.7x ratio) probably still holds because nulls distribute roughly proportionally across cohorts. The absolute rates (20.15%, 11.87%) are under-counts.

**Net verdict**: Genuine demerit. Should be fixed in Phase 3 (treat null as null, exclude from Q3.1 denominator), or at minimum documented prominently. Currently invisible to a casual reader of the chart.

---

## Summary table

| # | Decision | Net verdict |
|---|---|---|
| D1 | 4 data sources, solo team | merit |
| D2 | Spark-only, no notebooks | merit |
| D3 | Long-form profile CSV | merit |
| D4 | Simple regex for `company_normalized` | acceptable |
| D5 | Step 0 diagnostic gate | strong merit |
| D6 | Binary cohort split | merit, semantic cost |
| D7 | Pandas/matplotlib for charts | merit |
| D8 | JOLTS macro add-on | strong merit |
| D9 | Cohort-definition chart footer | merit, partial |
| D10 | Skip recency split | demerit |
| D11 | Tech-skill set without MGMT/MNFC | merit |
| D12 | No statistical inference | acceptable |
| D13 | Information-sector as tech proxy | acceptable |
| D14 | Manual JOLTS download | merit |
| D15 | `remote_allowed` null = false | demerit |

Two decisions are notable strong merits (D5 Step 0 gate, D8 JOLTS add-on). Two are notable demerits (D10 skipping recency split, D15 remote_allowed null treatment). The rest are net merits or acceptable trade-offs for an MVP.

The two demerits are the highest-value items to address in any future iteration of the project. The recency split (D10) is the most analytically useful single addition; the remote_allowed fix (D15) is the easiest correctness improvement.
