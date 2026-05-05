# Final Submission Workspace

This folder consolidates everything needed for Phase 3 of the project (final report due May 7, presentation due May 5). It is the working space where the main report, presentation outline, and supporting analytical documents live before being converted to PDF/PPTX deliverables.

## Project at a glance

LinkedIn Job Market Analytics, NYU CSCI-GA.2437 Big Data Application Development, Spring 2026. A solo Apache Spark pipeline that ingests four public datasets and tests how companies appearing in the public 2020-2026 layoffs record hire compared to the rest of the US job market during 2023-2024, with 25-year macro-level context drawn from BLS JOLTS time series. The cross-sectional cohort comparison and the longitudinal macro reading are the two halves of a single empirical thesis; together they describe a 2023-2024 tech labor market in which named layoff-listed employers continued hiring at premium senior-and-technical profiles while the aggregate Information-sector underwent a hiring slowdown rather than a separation surge.

The Phase 1 ingestion deliverable was submitted on April 24, 2026 and is preserved at `submission/Dhairya_dpm8739_phase1/`. This folder is the working space for the Phase 3 analytical deliverable — `FINAL_REPORT.md` is the master report document, with the eight published charts embedded inline at the locations referenced in the report's findings sections.

## Folder structure

```
final_submission/
├── README.md                              <- this file (index)
├── FINAL_REPORT.md                        <- master report; 8 charts embedded inline
├── PRESENTATION_OUTLINE.md                <- slide-by-slide structure for May 5
└── appendix/
    ├── A_thesis_revision_rationale.md     <- thesis scope and boundary discussion
    ├── B_methodological_confounds.md      <- detailed limitations writeup
    ├── C_decisions_log.md                 <- 15 major decisions, merits + demerits
    ├── D_findings_inferences_review.md    <- per-finding inference audit
    └── E_action_items.md                  <- Phase 3 remaining work, tiered by impact
```

## Reading order

If you are reviewing this folder for the first time, read in this order:

1. **FINAL_REPORT.md** — the master report. Contains the executive summary, thesis, data, methodology, all eight findings with inline charts, discussion, scope/confounds, conclusions, and reproducibility instructions. This is the source document for the May 7 PDF.
2. **appendix/D_findings_inferences_review.md** — per-finding inference audit (what each chart can and cannot defensibly claim).
3. **appendix/B_methodological_confounds.md** — detailed write-up of every confound named in §7 of the report.
4. **appendix/A_thesis_revision_rationale.md** — discussion of the thesis scope, what the design supports, and the data-driven boundaries that determined the scope.
5. **PRESENTATION_OUTLINE.md** — slide deck plan for the May 5 in-class symposium.
6. **appendix/C_decisions_log.md** — engineering and analytical decisions, with merit/demerit recorded for Q&A defense.
7. **appendix/E_action_items.md** — natural extensions and remaining Phase 3 work, prioritized.

## Relationship to the rest of the project

| Asset | Location | Status |
|---|---|---|
| Phase 1 ingestion submission | `submission/Dhairya_dpm8739_phase1/` | submitted Apr 24, 2026 (frozen) |
| Spark code (10 scripts) | `scripts/` at project root | complete |
| Cleaned Parquet datasets | `output/parquet/` (postings, skills, layoffs, jolts) | complete |
| Profile CSVs | `output/profiles/` | complete |
| Analytics result CSVs | `output/results/` (q1_1 ... q4_2) | 8 queries complete |
| Chart PNGs | `output/charts/` | 8 PNGs complete |
| Run logs | `output/logs/` | complete |
| Phase 1 spec + cross-phase status | `IMPLEMENTATION_PLAN.md` | up-to-date |
| Phase 2 spec | `PHASE_2_IMPLEMENTATION_PLAN.md` | locked, status: implemented |
| Top-level README + run instructions | `Readme.md` | up-to-date |
| Pipeline reproducibility | one-shot Docker command in top-level `Readme.md` | last verified end-to-end May 4, 2026 |

To reproduce every number, chart, and intermediate Parquet referenced in `FINAL_REPORT.md`, run the one-shot in the top-level `Readme.md` "How to run" section. Total runtime ~6 minutes on 8 GB Docker.

## How to convert these markdown files to deliverables

For the May 7 PDF report:

1. Open `FINAL_REPORT.md` in any markdown editor that resolves relative image paths (VS Code, Typora, Obsidian, or any pandoc-driven flow). The eight charts are embedded inline via `![...](../../output/charts/q*.png)` references and will appear in-place when rendered.
2. Add a cover page (title, name, NetID, course, submission date).
3. Export as PDF, target 8-12 pages with charts inline.

If a target tool (Google Docs paste, Word import) does not resolve the relative image paths, the eight chart PNGs are at `output/charts/` from the repo root and can be inserted manually at the locations referenced in the report's §5 findings.

For the May 5 presentation:

1. Open `PRESENTATION_OUTLINE.md`. Each section becomes one slide.
2. Use the same 8 charts as visual anchors.
3. Convert to PowerPoint or Google Slides.

## Headline conclusions

The five claims the report defends, all reproducible from `output/results/` and visualized in `output/charts/`:

1. **Hiring profile of the layoff-listed cohort.** In 2023-2024 the 432 named layoff-listed employers that continued posting on LinkedIn hired with a profile substantially different from the rest of the market: ~2x median entry-level USD salary, 66.4% Mid-Senior posting share against 43.2% elsewhere, 1.78x tech-leaning skill concentration, 1.70x remote-allowed rate, and 58.4% concentration in five tech-hub states (CA, VA, WA, TX, NY).
2. **Aggregate Information-sector separations did not elevate during 2023-2024.** Monthly layoffs-and-discharges rate sat at a 2023-2024 median of 1.2%, within rounding of the 25-year median of 1.1% and far below the 2020-03 peak of 6.6%.
3. **Aggregate Information-sector hiring activity contracted sharply during 2023-2024.** Annual-average job openings fell 38% from 2022 peak (6.81% to 4.20%); the April-2022 monthly peak of 8.3% gave way to a 2023-2024 monthly median of 4.5% (46% drop). Hires fell 28% (3.47% to 2.50%). Openings stayed above hires throughout.
4. **The popular "2023 tech layoff wave" narrative is not what aggregate data shows.** The 2023-2024 macro shift was a hiring freeze, not a separation surge.
5. **The largest layoff-listed employers continued hiring at elevated rates during the macro hiring freeze.** Visible layoffs and continuing hiring at the same employers are both true and are not in tension once the macro context is read alongside the cohort data.

Boundaries the report explicitly does not extend across: causation (the cohort comparison is descriptive, not causal), industry-controlled inference (the cohort is big-tech-skewed by construction; this is acknowledged in §7), and pre-2023 longitudinal claims at the postings level (no pre-2023 postings data is available; the longitudinal axis comes from JOLTS, which is sector-aggregate). See `FINAL_REPORT.md` §7 and `appendix/B_methodological_confounds.md` for the full scope discussion.
