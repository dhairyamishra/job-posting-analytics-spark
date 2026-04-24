# LinkedIn Job Market Analytics — Implementation Plan

## Context

Course project for NYU CSCI-GA.2437 (Big Data Application Development, Spring 2026). Solo team, professor-approved. **Phase 1 (data profiling + cleaning) is due April 24** and is the immediate scope of this plan. Phases 2 and 3 are noted at the end but not implemented here.

**Constraint:** Use Spark for everything. Keep scope lean — no production polish, no extra features, no unrequested abstractions.

## Thesis

> Comparing LinkedIn job postings against the 2020–2026 layoffs record, we examine whether layoff-affected companies have resumed hiring at the same scale, level, skill mix, and locations as before — or whether they have structurally shifted what they hire for.

## Datasets

| # | Name | Source | Files used | Size |
|---|------|--------|------------|------|
| 1 | LinkedIn Job Postings (2023–2024) | Kaggle: `arshkon/linkedin-job-postings` | `postings.csv`, `mappings/skills.csv`, `jobs/job_skills.csv` | ~1–2 GB total |
| 2 | Tech Layoffs (2020–present) | Kaggle: `swaptr/layoffs-2022` | `layoffs.csv` | <5 MB, ~2,886 rows |

`postings.csv` is already the merge of `jobs.csv` + `salaries.csv` with a few enrichments (`company_name`, `normalized_salary`, `zip_code`, `fips`) — do not re-merge those.

## Folder Structure

```
linkedin-spark-project/
├── data/
│   ├── linkedin/
│   │   ├── postings.csv
│   │   ├── mappings/skills.csv
│   │   └── jobs/job_skills.csv
│   └── layoffs/
│       └── layoffs.csv
├── output/
│   ├── parquet/         # cleaned datasets
│   ├── profiles/        # CSV summaries of profiling results
│   └── logs/            # stdout dumps from each run
└── scripts/
    ├── 01_profile_and_clean_postings.py
    ├── 02_profile_and_clean_skills.py
    └── 03_profile_and_clean_layoffs.py
```

## Environment

Docker on Windows, `jupyter/pyspark-notebook` image, scripts run via `spark-submit` from inside the container. No Jupyter, no notebooks — scripts only.

```powershell
docker run -it --rm -v "${PWD}:/home/jovyan/work" --memory=8g jupyter/pyspark-notebook bash
cd work
spark-submit scripts/01_profile_and_clean_postings.py 2>&1 | tee output/logs/01_postings.log
```

- [x] Docker environment setup validated and Spark runtime smoke-tested in-container (`spark-submit --version` and `spark-sql` test query).

## Common Script Pattern

Every script must:

1. Create a `SparkSession` named after the script.
2. Load the CSV with `header=True, multiLine=True, escape='"', quote='"'` (the LinkedIn `description` field has embedded quotes and newlines — defaults will mis-parse).
3. **Profile**: print schema, row count, null counts per column, distinct counts on key categorical columns, `.describe()` for numeric columns. Print samples with `.show(5, truncate=False)`.
4. For each key categorical column, also print top-10 value counts via `groupBy(col).count().orderBy(desc("count")).show(10, truncate=False)`.
5. **Clean** per the rules below.
6. Print cleaned schema + cleaned row count + count of rows dropped.
7. Write a profiling summary as a single CSV to `output/profiles/<name>.csv` in long-form with columns `dataset, column, metric, value` (use `.coalesce(1).write.csv(...)`).
8. Write the cleaned data to `output/parquet/<name>/` with `mode("overwrite")`.
9. Stop the SparkSession.

All `print` statements should be clear, labeled, and grep-friendly so the log file is the evidence.

## Script 1 — `01_profile_and_clean_postings.py`

**Input:** `data/linkedin/postings.csv` (31 columns)

- [x] Script 1 implemented, tested via `spark-submit`, and output parquet/profile/log artifacts verified.

**Keep these columns:**
`job_id, company_id, company_name, title, location, formatted_work_type, formatted_experience_level, remote_allowed, min_salary, max_salary, med_salary, pay_period, normalized_salary, currency, views, applies, original_listed_time, zip_code`

**Drop these columns:**
`description, skills_desc, job_posting_url, application_url, posting_domain, application_type, closed_time, expiry, listed_time, sponsored, work_type, compensation_type, fips`

**Cleaning rules (in order):**
1. Split `location` on `,`: create `city` (first part, trimmed, lowercased) and `state` (second part, trimmed, lowercased). Keep the original `location` column for display.
2. Cast `zip_code` as `StringType` (must preserve leading zeros — never cast to int).
3. Convert `original_listed_time` (millis epoch, Long) to a new `listed_date` column: `from_unixtime(col("original_listed_time")/1000).cast("date")`.
4. Drop rows where `min_salary > max_salary` (only when both are present).
5. Drop rows where `normalized_salary < 10000 OR normalized_salary > 1000000` (sanity bounds).
6. Cast `remote_allowed` to Boolean: `1 → true`, anything else (0, null, empty) → `false`.
7. Add a `company_normalized` column for future joins: `lower(trim(regexp_replace(company_name, "(?i)\\s*(inc|corp|corporation|llc|ltd|limited)\\.?$", "")))` (matches Script 3 normalization logic).

**Deferred to Phase 2 (query-time filters):**
- Salary-only analyses will filter to rows with at least one non-null salary field (`normalized_salary`, `min_salary`, `med_salary`, or `max_salary`).
- Salary-only analyses will restrict to `currency = "USD"`.

**Output:** `output/parquet/postings/`

## Script 2 — `02_profile_and_clean_skills.py`

**Inputs:**
- `data/linkedin/jobs/job_skills.csv` (`job_id`, `skill_abr`)
- `data/linkedin/mappings/skills.csv` (`skill_abr`, `skill_name`)

- [x] Script 2 implemented, tested via `spark-submit`, and output parquet/profile/log artifacts verified.

**Cleaning rules:**
1. Profile both files independently.
2. Join `job_skills` with `skills` on `skill_abr` (left join, keeping all `job_id`/`skill_abr` rows).
3. Drop rows where `skill_name` is null after the join (orphaned skill codes).
4. Deduplicate on `(job_id, skill_abr)`.

**Output:** `output/parquet/skills/` (single joined parquet with columns `job_id, skill_abr, skill_name`)

## Script 3 — `03_profile_and_clean_layoffs.py`

**Input:** `data/layoffs/layoffs.csv` (~2,886 rows)

- [x] Script 3 implemented, tested via `spark-submit`, and output parquet/profile/log artifacts verified.

**Keep these columns:**
`company, location, total_laid_off, date, percentage_laid_off, industry, stage, country`

**Drop these columns:**
`source, funds_raised, date_added`

**Cleaning rules (in order):**
1. Parse `date` with format `M/d/yyyy` into a `DateType` column (replace the original).
2. Drop rows where BOTH `total_laid_off` AND `percentage_laid_off` are null.
3. Cast `total_laid_off` as `IntegerType`.
4. Cast `percentage_laid_off` as `DoubleType`.
5. Add a `company_normalized` column for joining: `lower(trim(regexp_replace(company, "(?i)\\s*(inc|corp|corporation|llc|ltd|limited)\\.?$", "")))`.

**Output:** `output/parquet/layoffs/`

## Acceptance Criteria

For each script:
- Runs to completion via `spark-submit` with no errors.
- Produces a non-empty `.parquet/` directory in `output/parquet/<name>/`.
- Produces a non-empty profiling summary CSV in `output/profiles/`.
- Stdout log clearly shows: original row count, dropped row count per cleaning step, final row count.

## Phase 1 Submission

Zip the following as `Dhairya_dpm8739_phase1.zip`:
- `scripts/` (all 3 `.py` files)
- `output/profiles/` (CSV summaries)
- `output/logs/` (stdout logs)
- 1–2 screenshots of the terminal showing a successful run

Do **not** include parquet files in the zip (too bulky; reference them in the report instead).

## Out of Scope for Phase 1

Do not implement any of these — they belong to later phases:
- Joining the cleaned datasets together
- Running any analytics queries
- Visualizations or dashboards
- MLlib, Streaming, GraphFrames
- Any orchestration, scheduling, or CI tooling
- Tests beyond the acceptance criteria above

## Phase 2 — Analytics (complete)

- [x] Step 0 diagnostic verified join hit rate: 432/2,505 companies matched (17.25% raw; headcount-weighted cohort covers Amazon, Intel, Oracle, Microsoft, Meta, Salesforce, Cisco, Tesla, Google, etc.).
- [x] Scripts 5-7 implemented (6 Spark SQL queries across 3 thesis angles: salary/level, skills pivot, geo+remote), tested via `spark-submit`, results written to `output/results/`.
- [x] Script 8 chart generation implemented, 6 PNGs in `output/charts/`.
- See [PHASE_2_IMPLEMENTATION_PLAN.md](PHASE_2_IMPLEMENTATION_PLAN.md) for the full Phase 2 spec.

## Future Phases (reference only — do not build now)


- **Phase 3 (Presentation + Report, due May 5 / May 7):** Slides and a 5–8 page report covering thesis, data, cleaning decisions, queries, findings, and limitations.
