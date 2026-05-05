# LinkedIn Job Market Analytics — Phase 2 Implementation Plan

> **Status (May 4, 2026): Implemented and verified.** The six core queries (Q1.1-Q3.2) plus the JOLTS add-on (Q4.1, Q4.2) and the chart renderer all ship; Script 04 diagnostic gate passes; the entire Phase 1 + Phase 2 pipeline reproduces in ~6 min via the one-shot in `Readme.md`. The spec below is preserved verbatim as the "locked Phase 2 contract." All amendments since locking (the JOLTS add-on, the eighth chart) are documented in `IMPLEMENTATION_PLAN.md` under "Phase 2 Add-on — Macro Context (BLS JOLTS)." Headline reproduction: layoff cohort 3,569 postings vs non-affected 118,116, Mid-Senior share 66.36% vs 43.25%, tech-skill share 36.39% vs 20.39%, remote rate 20.15% vs 11.87% — bit-equivalent across reruns.

## Context

Phase 1 is complete. Cleaned parquet datasets exist at:
- `output/parquet/postings/` (~123,394 rows)
- `output/parquet/skills/` (joined `job_id, skill_abr, skill_name`)
- `output/parquet/layoffs/` (~2,886 rows, with `company_normalized` join key)

Phase 2 scope: produce six Spark SQL analytics queries grouped by thesis angle, plus six matplotlib charts. **Final code + report due May 7. Presentation May 5.**

**Constraint:** Stay lean. Spark SQL only (no MLlib, no streaming). One pandas/matplotlib script for charts. No dashboards, no orchestration.

## Verified Join Baseline (from diagnostic)

- Distinct layoff companies matched to postings: **432 of 2,503** (17.25% raw, ~60–70% headcount-weighted — matched cohort covers Amazon, Intel, Oracle, Microsoft, Meta, Salesforce, Cisco, Tesla, Google, SAP, etc.)
- Matched postings: **3,569 of 123,394** (~2.9%)
- ~1,709 postings (~1.4%) have null `company_normalized` and are excluded from both cohorts. Document in report limitations; no code fix.

**One manual alias to apply at script read time:**
```python
postings = postings.withColumn(
    "company_normalized",
    F.when(F.col("company_normalized").isin("x", "x corp"), "twitter")
     .otherwise(F.col("company_normalized"))
)
```
Recovers ~3,700 Twitter/X layoffs. Skip all other manual renames.

## Folder Additions

```
job-posting-analytics-spark/
├── scripts/
│   ├── 04_diagnostic_join_check.py        ← Step 0 join hit-rate gate
│   ├── 05_analytics_salary_level.py       ← Angle 1, 2 queries (Q1.1, Q1.2)
│   ├── 06_analytics_skills_pivot.py       ← Angle 2, 2 queries (Q2.1, Q2.2)
│   ├── 07_analytics_geo_remote.py         ← Angle 3, 2 queries (Q3.1, Q3.2)
│   ├── 08_make_charts.py                  ← matplotlib only, no Spark
│   ├── 09_profile_and_clean_jolts.py      ← add-on: BLS JOLTS Phase 1 clean
│   └── 10_analytics_macro_context.py      ← add-on: 2 macro queries (Q4.1, Q4.2)
└── output/
    ├── diagnostics/                       ← Step 0 join_hit_rate CSV
    ├── results/                           ← one CSV per query (8 total)
    └── charts/                            ← one PNG per query (8 total)
```

> The 09/10 JOLTS add-on and the resulting eighth chart were added after this spec was locked. The two extra queries do not modify any of the six core queries below; they read a fourth Parquet (`output/parquet/jolts/`) produced by Script 09 and write `q4_1_*` and `q4_2_*` CSVs that Script 08 picks up. See `IMPLEMENTATION_PLAN.md` for the add-on description.

## Common Pattern for Analytics Scripts (05–07)

Every analytics script must:

1. Create a `SparkSession` named after the script.
2. Read all three parquets:
   ```python
   postings = spark.read.parquet("output/parquet/postings/")
   skills   = spark.read.parquet("output/parquet/skills/")
   layoffs  = spark.read.parquet("output/parquet/layoffs/")
   ```
3. Apply the Twitter→X alias on `postings` (see above).
4. Build the cohort-tagging view at the top:
   ```sql
   CREATE OR REPLACE TEMP VIEW layoff_companies AS
   SELECT DISTINCT company_normalized
   FROM layoffs
   WHERE company_normalized IS NOT NULL
     AND (total_laid_off IS NOT NULL OR percentage_laid_off IS NOT NULL);

   CREATE OR REPLACE TEMP VIEW postings_tagged AS
   SELECT p.*,
          CASE WHEN lc.company_normalized IS NOT NULL
               THEN 'layoff_affected'
               ELSE 'non_affected'
          END AS subcohort
   FROM postings p
   LEFT JOIN layoff_companies lc
          ON p.company_normalized = lc.company_normalized
   WHERE p.company_normalized IS NOT NULL;
   ```
5. Run the script's queries against `postings_tagged` (and `skills` where needed).
6. For each query: `.show(truncate=False)` to log AND write to `output/results/<query_name>.csv` via `.coalesce(1).write.mode("overwrite").option("header", True).csv(...)`.
7. Stop the SparkSession.

All `print` statements should be labeled and grep-friendly.

## Script 5 — `05_analytics_salary_level.py` (Angle 1: Salary & Experience Shift)

**Q1.1 — Median salary by experience level × subcohort (USD only)**

```sql
SELECT subcohort,
       formatted_experience_level AS experience_level,
       PERCENTILE_APPROX(normalized_salary, 0.5) AS median_salary,
       COUNT(*) AS posting_count
FROM postings_tagged
WHERE currency = 'USD'
  AND normalized_salary IS NOT NULL
  AND formatted_experience_level IS NOT NULL
GROUP BY subcohort, formatted_experience_level
ORDER BY experience_level, subcohort;
```
Output: `output/results/q1_1_median_salary_by_level.csv`

**Q1.2 — Experience-level distribution by subcohort (share of postings)**

```sql
WITH counts AS (
  SELECT subcohort,
         formatted_experience_level AS experience_level,
         COUNT(*) AS n
  FROM postings_tagged
  WHERE formatted_experience_level IS NOT NULL
  GROUP BY subcohort, formatted_experience_level
),
totals AS (
  SELECT subcohort, SUM(n) AS total_n FROM counts GROUP BY subcohort
)
SELECT c.subcohort,
       c.experience_level,
       c.n,
       ROUND(100.0 * c.n / t.total_n, 2) AS pct_of_subcohort
FROM counts c
JOIN totals t USING (subcohort)
ORDER BY experience_level, subcohort;
```
Output: `output/results/q1_2_experience_level_distribution.csv`

## Script 6 — `06_analytics_skills_pivot.py` (Angle 2: Skills Mix)

**Q2.1 — Top 10 skills by share, per subcohort**

```sql
WITH joined AS (
  SELECT pt.subcohort, s.skill_name
  FROM postings_tagged pt
  JOIN skills s ON pt.job_id = s.job_id
),
counts AS (
  SELECT subcohort, skill_name, COUNT(*) AS n
  FROM joined
  GROUP BY subcohort, skill_name
),
totals AS (
  SELECT subcohort, SUM(n) AS total_n FROM counts GROUP BY subcohort
),
ranked AS (
  SELECT c.subcohort,
         c.skill_name,
         c.n,
         ROUND(100.0 * c.n / t.total_n, 2) AS pct_of_subcohort,
         ROW_NUMBER() OVER (PARTITION BY c.subcohort ORDER BY c.n DESC) AS rn
  FROM counts c
  JOIN totals t USING (subcohort)
)
SELECT subcohort, skill_name, n, pct_of_subcohort
FROM ranked
WHERE rn <= 10
ORDER BY subcohort, n DESC;
```
Output: `output/results/q2_1_top_skills_by_subcohort.csv`

**Q2.2 — Tech-leaning skill share per subcohort**

Tech-leaning set: `ENG, IT, ANLS, PRDM` (Engineering, IT, Analyst, Product Management). Verified to exist in `data/linkedin/mappings/skills.csv`. Excludes `MGMT` (universal across industries) and `MNFC` (industrial, would dilute signal).

```sql
WITH joined AS (
  SELECT pt.subcohort, s.skill_abr
  FROM postings_tagged pt
  JOIN skills s ON pt.job_id = s.job_id
)
SELECT subcohort,
       COUNT(*) AS total_skill_tags,
       SUM(CASE WHEN skill_abr IN ('ENG','IT','ANLS','PRDM') THEN 1 ELSE 0 END) AS tech_skill_tags,
       ROUND(100.0 * SUM(CASE WHEN skill_abr IN ('ENG','IT','ANLS','PRDM') THEN 1 ELSE 0 END) / COUNT(*), 2) AS tech_pct
FROM joined
GROUP BY subcohort
ORDER BY subcohort;
```
Output: `output/results/q2_2_tech_skill_share.csv`

## Script 7 — `07_analytics_geo_remote.py` (Angle 3: Geographic & Remote)

**Q3.1 — Remote-allowed rate by subcohort**

```sql
SELECT subcohort,
       COUNT(*) AS total_postings,
       SUM(CASE WHEN remote_allowed = true THEN 1 ELSE 0 END) AS remote_postings,
       ROUND(100.0 * SUM(CASE WHEN remote_allowed = true THEN 1 ELSE 0 END) / COUNT(*), 2) AS remote_pct
FROM postings_tagged
GROUP BY subcohort
ORDER BY subcohort;
```
Output: `output/results/q3_1_remote_rate.csv`

**Q3.2 — Top 10 states by posting count, per subcohort**

```sql
WITH counts AS (
  SELECT subcohort, state, COUNT(*) AS n
  FROM postings_tagged
  WHERE state IS NOT NULL AND state != ''
  GROUP BY subcohort, state
),
totals AS (
  SELECT subcohort, SUM(n) AS total_n FROM counts GROUP BY subcohort
),
ranked AS (
  SELECT c.subcohort,
         c.state,
         c.n,
         ROUND(100.0 * c.n / t.total_n, 2) AS pct_of_subcohort,
         ROW_NUMBER() OVER (PARTITION BY c.subcohort ORDER BY c.n DESC) AS rn
  FROM counts c
  JOIN totals t USING (subcohort)
)
SELECT subcohort, state, n, pct_of_subcohort
FROM ranked
WHERE rn <= 10
ORDER BY subcohort, n DESC;
```
Output: `output/results/q3_2_top_states_by_subcohort.csv`

## Script 8 — `08_make_charts.py` (Pandas + matplotlib, no Spark)

Reads the 6 CSVs from `output/results/`, produces 6 PNGs in `output/charts/`. One chart per query. Keep styling minimal — graders care about the data, not the design.

| Query | Chart type |
|---|---|
| Q1.1 | Grouped bar: x=experience_level, y=median_salary, hue=subcohort |
| Q1.2 | Grouped bar: x=experience_level, y=pct_of_subcohort, hue=subcohort |
| Q2.1 | Two horizontal bar charts side-by-side (or faceted): one per subcohort, top 10 skills |
| Q2.2 | Simple bar: x=subcohort, y=tech_pct |
| Q3.1 | Simple bar: x=subcohort, y=remote_pct |
| Q3.2 | Two horizontal bar charts side-by-side: one per subcohort, top 10 states |

Implementation notes:
- Use `pandas.read_csv()` — Spark's `coalesce(1).write.csv()` writes a directory with a single `part-00000-*.csv`; the script should glob for that file.
- Save with `plt.savefig("output/charts/<query_name>.png", dpi=150, bbox_inches="tight")`.
- One chart per `plt.figure()`. No subplots beyond the side-by-side cases.

## Acceptance Criteria

For each analytics script (05, 06, 07):
- Runs to completion via `spark-submit` with no errors.
- Produces 2 result CSVs in `output/results/`.
- Stdout log shows query results via `.show()`.

For `08_make_charts.py`:
- Runs as `python scripts/08_make_charts.py` (no Spark needed).
- Produces 6 PNGs in `output/charts/` (8 PNGs once the JOLTS add-on Q4.1 + Q4.2 charts are wired in).

For the JOLTS add-on (Scripts 09, 10):
- 09 follows the same Phase 1 pattern as 01-03: profile + clean + parquet + profile-CSV. Final cleaned Parquet has 1,818 rows = 6 series x 303 months.
- 10 produces `q4_1_jolts_layoff_rate/` and `q4_2_jolts_openings_hires_rate/` CSVs in `output/results/`.

## Reporting Stance

If a query result shows little or no difference between `layoff_affected` and `non_affected` (e.g., remote rates within 1-2 percentage points, or top-10 lists that overlap heavily), report that as the finding. "No meaningful structural shift detected on dimension X" is a legitimate, defensible result — do not adjust queries, filters, or cohort definitions to manufacture a stronger contrast.

## Phase 2 Submission (preliminary — final bundle is Phase 3)

Keep these for the final May 7 zip:
- `scripts/05_*.py`, `scripts/06_*.py`, `scripts/07_*.py`, `scripts/08_*.py`
- `output/results/` (small, include directly)
- `output/charts/` (small, include directly)
- `output/logs/` (Phase 2 stdout logs)

## Out of Scope for Phase 2

- Joining beyond the three datasets already in scope
- ML, predictions, modeling
- Streaming
- Time-series analysis (e.g., before/after layoff date) — postings dataset has no longitudinal coverage to support it; flag in limitations
- Interactive dashboards
- Any query beyond the six listed above (resist scope creep)

## Notes for the Coding Agent

- Verify the tech-leaning skill abbreviations (`ENG, IT, ANLS, PRDM`) actually exist in `output/parquet/skills/` before running Q2.2. If any are missing or named differently, substitute the closest equivalent and document the change in the script's docstring.
- The `state` column produced in Phase 1 is lowercased and trimmed. Q3.2 will yield results like `ca, ny, tx`. That's fine — the chart script can `.str.upper()` for display.
- Use `PERCENTILE_APPROX` (not `PERCENTILE`) for medians — it's the Spark SQL idiom and runs distributed.
- If Q2.2 implementation or verification stalls for any reason (>10 minutes of incidental friction), drop Q2.2 entirely and ship 5 queries. Q2.1 already carries the skills-pivot story end-to-end via the top-10 comparison; tech roles will surface naturally if they are present in the cohort. Do not block on Q2.2.
