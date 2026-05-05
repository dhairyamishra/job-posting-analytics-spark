# Appendix E — Action Items for Phase 3

This appendix tiers the remaining work for the May 5 presentation and May 7 final report by impact-per-time-spent. Tier 1 items are must-do; Tier 2 are high-value if time permits; Tier 3 are polish.

The honest assessment: Tier 1 alone is sufficient to ship a strong submission. Tier 2 lifts the project from "competent course MVP" to "genuinely sharp piece of analytical work." Tier 3 is optional but improves grader-reading experience.

Time estimates assume the developer is the same person who built the project and is already familiar with the codebase.

---

## Tier 1 — Must-do before Phase 3 deadlines (~4-6 hours total)

These five items address the gaps most likely to lose points with a careful grader.

### T1.1 — Build the May 5 slide deck (~2-3 hours)

Use `PRESENTATION_OUTLINE.md` as the template. 10 slides, 8-10 minutes. Critical:

- Slide 5 (JOLTS layoff rate) and Slide 6 (JOLTS openings vs hires) are the headline. Practice these.
- Slide 8 (methodological confounds) demonstrates analytical maturity.
- Backup slides ready for likely Q&A topics.

**Practice**: rehearse twice, target 8 minutes. Be ready for the five most-likely Q&A questions listed in `PRESENTATION_OUTLINE.md`.

### T1.2 — Convert FINAL_REPORT.md into the May 7 PDF (~2-3 hours)

`FINAL_REPORT.md` is the master report and is feature-complete: it has the thesis, data, methodology, findings with all eight charts embedded inline, discussion, scope/confounds, conclusions, and reproducibility instructions. The conversion work is:

1. Render `FINAL_REPORT.md` through any markdown tool that resolves relative image paths (VS Code with a markdown PDF extension, Typora, Obsidian, pandoc + LaTeX). The eight inline `![...](../../output/charts/q*.png)` references will surface the charts in-place.
2. Add a cover page (title, name, NetID, course, submission date).
3. Format pleasantly (consistent fonts, page breaks at sensible places between sections).
4. Save as PDF; target ~8-12 pages with charts inline.

If the chosen tool does not resolve the relative image paths, the eight chart PNGs are at `output/charts/` from the repo root; insert them manually at the §5 locations in the report.

### T1.3 — Final read-through of FINAL_REPORT.md against the result CSVs (~30 minutes)

Before exporting to PDF, do one read-through with the eight result CSVs in `output/results/q*/` open alongside the report. Confirm each cited number matches the corresponding CSV. The pipeline was last verified end-to-end on May 4, 2026; reruns reproduce byte-equivalent CSVs, so this check is fast unless the data sources have been refreshed in between.

---

## Tier 2 — High-value if time allows (~2-3 hours total)

These items would meaningfully strengthen the analytical story but the project ships fine without them.

### T2.1 — Add a recency split inside the layoff cohort (~1 hour)

This is the single most impactful Tier 2 addition. Modify the cohort tagging in `scripts/05_*.py`, `scripts/06_*.py`, and `scripts/07_*.py` to derive a `subcohort_recent` flag:

```sql
CASE 
  WHEN lc.last_layoff_date IS NULL THEN 'non_affected'
  WHEN lc.last_layoff_date >= '2023-01-01' THEN 'recent_layoff'
  ELSE 'old_layoff'
END AS subcohort
```

Where `lc.last_layoff_date` is `MAX(date)` per `company_normalized` from the layoffs table.

This produces a 3-cohort split. Pick one of the existing analytical dimensions (Q1.1 salary by level is the most interesting) and re-render the chart with three cohort lines instead of two. Add as a new chart `q5_salary_by_level_with_recency.png`.

**Why it matters**: This is the closest the available data gets to a quasi-temporal natural experiment. Companies whose layoffs happened during 2023-2024 (Meta Nov 2022, Google Jan 2023, Microsoft Jan 2023) might show different post-layoff hiring patterns than companies whose layoffs were 2-3 years earlier.

**What it adds to the report**: One paragraph and one chart in section 4.1. Strengthens the temporal-context discussion.

### T2.2 — Add a bootstrap noise baseline (~45 minutes)

Add a new Spark SQL query that bootstraps the cohort-comparison metric. Pseudo-SQL:

```sql
-- Generate 1000 random subsamples of 3,569 postings each (same size as layoff cohort)
-- For each subsample, compute the metric (e.g., remote_pct or median_salary)
-- Count how often the random-subsample metric reaches or exceeds the observed cohort metric
```

Output: an empirical noise distribution per metric. Compare the observed cohort-vs-non-cohort ratio against this distribution.

If the observed ratio (e.g., 1.7x for remote rate) lies in the 95th percentile of random-subsample ratios, that's a "p-value-like" interpretation suggesting the difference is unlikely to be sampling noise.

**Why it matters**: Without this, "1.7x" is a point estimate with no associated uncertainty. With it, every cohort claim has a noise-baseline interpretation.

**What it adds to the report**: One paragraph in the Methodological Confounds section, addressing confound 9 from `B_methodological_confounds.md`.

### T2.3 — Create a clean architecture diagram for slide 3 (~30 minutes)

The text-only data-flow description in `PRESENTATION_OUTLINE.md` slide 3 should be replaced with a clean visual diagram. Use Mermaid (rendered to PNG via mermaid.live) or PowerPoint's flowchart tools.

Diagram should show:
- 4 raw data sources (left)
- 10 Spark scripts grouped by phase (center)
- 8 chart PNGs (right)
- Single data flow direction (left-to-right) with branching where appropriate

**Why it matters**: A grader processes a diagram in 5 seconds; processes a text description in 30 seconds. Architecture diagrams earn quick points.

---

## Tier 3 — Polish (~1-2 hours total)

Optional improvements that lift the submission's perceived quality.

### T3.1 — Code cleanup (~30 minutes)

- Remove the dead Twitter/X alias from analytics scripts (or document it explicitly as defensive code).
- Add a one-line docstring to each of the 10 scripts explaining what it does.
- Verify `IMPLEMENTATION_PLAN.md` reflects the final state of the project (not in-progress phase markers).

### T3.2 — Update the project README's TL;DR (~15 minutes)

Currently good but should be reworded to lead with the JOLTS reframe and acknowledge the cohort comparison as descriptive. Make it consistent with the final-report ordering.

### T3.3 — Fix the `remote_allowed` null treatment (~30 minutes)

Modify `scripts/01_profile_and_clean_postings.py` cleaning rule 6 to keep null as null (cast to nullable Boolean). Re-run Phase 1 + Phase 2. Q3.1 chart will then show:

- Layoff cohort: ~X% (where X is computed only from postings where the field is set)
- Non-affected cohort: ~Y%
- Both rates will be much higher than the current 20.15% / 11.87%, but the relative ratio should be similar.

Update the chart's footer to note the change in null treatment.

**Why it matters**: Addresses confound D15 (the largest correctness issue in the project). 30 minutes well spent.

### T3.4 — Verify all sample sizes are visible on every chart (~15 minutes)

The chart script labels per-cell sample sizes, but verify visually that every cell with n < 30 is clearly flagged (e.g., italicized or asterisked).

### T3.5 — Polish chart Q3.2 to use percent share instead of raw counts (~15 minutes)

Q3.2's x-axis currently shows raw posting counts, which makes the layoff cohort's bars look small relative to the non-affected cohort's. Switch to `pct_of_subcohort` (already in the result CSV) so both cohorts are on a comparable scale.

---

## Suggested order of execution

If you have 6-8 hours total to put into Phase 3 work, suggested allocation:

| Time | Task |
|---|---|
| 0:00 - 3:00 | T1.1 build the slide deck from `PRESENTATION_OUTLINE.md` (3 hours) |
| 3:00 - 5:30 | T1.2 convert `FINAL_REPORT.md` to PDF and add cover page (2.5 hours) |
| 5:30 - 6:00 | T1.3 final read-through against result CSVs (30 minutes) |
| 6:00 - 8:00 | Tier 2 items if time remains, or rehearsal for the May 5 talk |

If you have only 4 hours, do T1.2 and T1.3 first (the PDF is the hard deadline on May 7), then T1.1 the deck. If less than 4 hours, prioritize the PDF and assemble the deck the evening before the symposium.

---

## What "done" looks like

Phase 3 is complete when:

1. **`FINAL_REPORT.md`** is converted to a PDF with all 8 charts embedded inline, saved as `Dhairya_dpm8739_final_report.pdf`. Target ~8-12 pages with charts.
2. **A slide deck (PowerPoint or Google Slides)** exists with the 10 slides described in `PRESENTATION_OUTLINE.md`.
3. **The deck has been rehearsed** at least once for an 8-10 minute window.
4. **The submission is uploaded to Brightspace** before the May 7 11:59 PM deadline.

Optional but recommended:

5. **Tier 2 items implemented** (recency split, bootstrap noise baseline) for stronger analytical claims.
6. **The Phase 1 ingestion submission** at `submission/Dhairya_dpm8739_phase1/` remains intact (don't replace it; this is a separate Phase 3 submission).
7. **The repository** is tagged or branched at the Phase 3 final state for reproducibility.

---

## Closing note

The project is in good shape. The engineering work is solid, the JOLTS reframe is sharp, and the report's scope discipline (descriptive cohort comparison + sector-aggregate macro reading, no causal overreach) makes the conclusions defensible at the level of detail any reasonable reader will probe. The remaining work is primarily packaging — taking the analysis already in `FINAL_REPORT.md` and presenting it cleanly enough that a grader can recognize the quality in the limited time they have to review.

Don't over-engineer Phase 3. The Tier 1 items are sufficient. Ship.
