# Presentation Outline (In-Class Symposium, May 5)

10 slides total. Target talk time: 8-10 minutes presentation + 2-3 minutes Q&A. Each slide is described below with the visual to use, the headline takeaway, and 2-3 spoken-talking-points.

The deck leads with the surprising JOLTS finding rather than the cohort comparison. This is a storytelling choice: setting up the macro reframe first lets the cohort comparison be read inside the macro context the audience now holds, which is the same integrated interpretation the report defends in `FINAL_REPORT.md` §6.

---

## Slide 1 — Title

**Visual**: clean text-only title slide.

**Headline**: LinkedIn Job Market Analytics — what the 2023-2024 tech labor data actually shows

**Subhead**: Dhairya P. Mishra (dpm8739) — CSCI-GA.2437 BDAD, Spring 2026

**Talking points** (~30 seconds):
- Solo project, professor-approved.
- Four data sources joined in Apache Spark.
- The story we set out to tell isn't quite the story the data supports.

---

## Slide 2 — The question, in two parts

**Visual**: two stacked panels. Top panel: cross-sectional cohort comparison ("how does big-tech 2023-2024 hiring compare to the rest of the US market, along salary / level / skills / geography / remote?"). Bottom panel: longitudinal macro reading ("how does 2023-2024 sit inside 25 years of BLS JOLTS hiring, openings, and separation rates?").

**Headline**: A two-part empirical thesis. Cohort comparison + 25-year macro context.

**Talking points** (~60 seconds):
- The thesis pairs a cross-sectional cohort comparison (high resolution at the employer level, low in time) with a longitudinal macro reading (high resolution in time, sector-aggregate).
- The cohort comparison answers what is happening at the named layoff-listed employers in 2023-2024 across five dimensions.
- The macro reading places that snapshot inside 25 years of aggregate JOLTS data and tests whether the popular "2023 tech layoff wave" narrative shows up at the sector level.
- Together they support an integrated interpretation that neither alone can produce.

---

## Slide 3 — Data and pipeline

**Visual**: simple architecture diagram. Four raw sources on the left (LinkedIn postings, LinkedIn skills, Kaggle layoffs, BLS JOLTS) → 10 Spark scripts in the middle (with 4 cleaning + 1 diagnostic + 4 analytics + 1 chart-rendering boxes) → output deliverables on the right (8 result CSVs + 8 chart PNGs).

**Headline**: 4 sources, 10 scripts, ~6 minutes end-to-end in Docker.

**Talking points** (~45 seconds):
- 123,394 cleaned LinkedIn postings (2023-2024).
- 213,768 skill tags after a left join + dedup.
- 3,643 layoff events (2020-03-11 to 2026-04-16).
- 1,818 monthly JOLTS observations (Dec 2000 to present).
- All Spark with Spark SQL on top of DataFrames. Single docker-run reproduces everything.

---

## Slide 4 — The diagnostic gate (Step 0)

**Visual**: simple two-bar chart: "company hit rate (17.25%)" vs "headcount-weighted hit rate (~60-70%)". Overlay names of the top matched companies.

**Headline**: 17% by company, but ~60-70% by total layoff headcount.

**Talking points** (~45 seconds):
- Before writing any analytics queries, we measured the join hit rate.
- Only 432 of 2,505 layoff companies match into the postings — but the matched ones are Amazon, Intel, Oracle, Microsoft, Meta, Google, Salesforce, Cisco, Tesla, IBM.
- Headcount-weighted, this captures most of what people meant by "the 2023 tech layoffs."
- Two-thirds of the unmatched companies are foreign (Flink, Paytm, Byju's), defunct (Katerra, Better.com), or rebranded (Twitter→X).
- This step prevented us from building 6 analytics queries on a brittle assumption.

---

## Slide 5 — JOLTS macro reframe, part 1: there was no layoff wave

**Visual**: chart `q4_1_jolts_layoff_rate_timeseries.png` — Information-sector layoff rate, 2000-present, with 2023-2024 window highlighted. Annotate the 2020 COVID peak (6.6%) and the 2023-2024 median (1.1%).

**Headline**: Aggregate Information-sector layoff rate during 2023-2024 was at the 25-year median.

**Talking points** (~75 seconds):
- The 2023 narrative: "tech layoff wave" — Amazon 18k, Meta 11k, Google 12k, Microsoft 10k.
- The BLS JOLTS data: monthly Information-sector layoff and discharge rate sat at 1.1% during the postings window.
- That's the same as the 25-year median. Nowhere near the 2020 COVID peak of 6.6%.
- The big-name cuts were real, but in aggregate sector terms they were absorbed within normal monthly separation rates.
- This is the project's most surprising finding.

---

## Slide 6 — JOLTS macro reframe, part 2: it was a hiring freeze

**Visual**: chart `q4_2_jolts_openings_vs_hires.png` — Information-sector openings vs hires, 2000-present, with 2023-2024 window highlighted.

**Headline**: Job openings fell 48% from 2022 peak. Hires fell 30%. That's the real story.

**Talking points** (~60 seconds):
- The Information-sector openings rate peaked at 8.3% in 2022.
- During 2023-2024 it fell to a median of 4.3%.
- Hires fell from 3.5% to 2.5% over the same period.
- Openings stayed above hires throughout — companies posted jobs they did not fill quickly.
- The 2023-2024 macro shift was a hiring slowdown, not a layoff surge. The popular narrative pointed at separations; the data shows changed hiring.

---

## Slide 7 — Cohort comparison: what we see in the postings data

**Visual**: 2x2 grid of charts. Top-left: Q1.1 dumbbell. Top-right: Q1.2 stacked bar. Bottom-left: Q2.2 donut pies. Bottom-right: Q3.1 callout cards. (Q3.2 / Q2.1 saved for backup slides.)

**Headline**: Layoff-listed cohort hires bigger paychecks, more senior, more tech, more remote — but it's because they are big tech.

**Talking points** (~90 seconds):
- 2x salary at entry level. 66% mid-senior vs 43%. 1.78x tech-skill share. 1.7x remote rate. 58% concentration in 5 tech-hub states.
- These are real differences in the data.
- They are dominated by industry composition, not by anything intrinsic to having had layoffs.
- A pre-layoff snapshot of the same companies would likely show the same differences.
- This is why the project leads with JOLTS, not with the cohort comparison.

---

## Slide 8 — Methodological confounds (own them)

**Visual**: bullet list of 5-6 confounds, each with one short clause.

**Headline**: Five confounds we explicitly acknowledge.

**Talking points** (~75 seconds):
- **Industry confound**: cohort is overwhelmingly big tech. Comparison conflates layoff effect with industry effect.
- **Snapshot vs longitudinal**: no "before" data. All claims are descriptive, not causal.
- **Selection bias**: layoffs dataset is editorially curated, weighted to large public events. Survivors of layoffs only.
- **Information sector ≠ tech**: NAICS 51 excludes Amazon, Tesla, fintech.
- **Remote-allowed null assumption**: 88% null in raw data; cleaning rule treats null as false. Relative comparison holds; absolute rates are under-counts.
- **No statistical inference**: differences reported as point estimates, no confidence intervals.

These are owned in the report; the project does not overclaim.

---

## Slide 9 — Conclusions

**Visual**: three numbered claims, each with one supporting datapoint.

**Headline**: What this project supports — and what it doesn't.

**Talking points** (~45 seconds):
- **Supports**: a clean "big tech vs broader market" portrait of 2023-2024 hiring (cohort comparison).
- **Supports**: the popular tech-layoff narrative does not match BLS aggregates (JOLTS reframe).
- **Supports**: the 2023-2024 macro shift was a hiring slowdown, not a layoff surge.
- **Does not support**: any causal claim that layoffs changed hiring patterns.
- **Does not support**: claim that 2023-2024 was unusual by historical layoff rates.

---

## Slide 10 — Future work

**Visual**: three-item list, each with effort estimate.

**Headline**: Three things that would meaningfully strengthen this analysis.

**Talking points** (~30 seconds):
- **Industry-matched cohorts**: compare layoff-affected big tech to non-affected big tech.
- **Recency split inside the layoff cohort**: separate companies whose layoff happened during the postings window vs years before.
- **Statistical inference**: bootstrap baselines for every cohort metric.

Each is well-defined and ~half a day of work. Not done in this submission to keep MVP scope.

---

## Backup slides (in case of Q&A)

Have ready but not in the main flow:

- **Backup 1**: chart `q2_1_top_skills_by_subcohort.png` — top 10 skills per cohort.
- **Backup 2**: chart `q3_2_top_states_by_subcohort.png` — top 10 states per cohort.
- **Backup 3**: the diagnostic top-20 unmatched companies list.
- **Backup 4**: `IMPLEMENTATION_PLAN.md` link / one-page methodology summary.

---

## Practice notes

The presentation should rehearse to **8 minutes**, leaving 2-3 minutes for Q&A.

The most likely questions a sharp grader will ask:

1. *"Why didn't you industry-match the cohorts?"* — Answer: out of MVP scope; would need a NAICS resolver for 24,000 distinct postings companies. Tier-1 future work.
2. *"How do you know your differences aren't just sampling noise?"* — Answer: we don't formally test, but the largest cells (Mid-Senior n=609 layoff cohort, n=12,098 non-affected) are large enough that the observed gaps would be highly unlikely under noise. Bootstrap-baseline noise testing is also Tier-1 future work.
3. *"Why is the company hit rate only 17%?"* — Answer: the layoffs dataset is editorially curated and includes many small/foreign/defunct entries; the matched 432 capture ~60-70% of total layoff headcount.
4. *"Why include JOLTS at all if it doesn't join to the postings?"* — Answer: it's a separate analytical layer, not a join. JOLTS provides macro context that the cohort comparison alone cannot — and it produced the most surprising finding.
5. *"What's the most surprising finding for you personally?"* — Answer: the JOLTS reframe. The cohort comparison numbers were predictable directionally, but seeing the aggregate Information-sector layoff rate sit at the 25-year median through 2023-2024 — the period the news cycle described as a "tech layoff wave" — was a sharper finding than the cohort data alone produces.

---

## Slide deck format conversion

The recommended workflow:

1. Open this file in any markdown editor.
2. For each slide section, create a corresponding slide in PowerPoint or Google Slides.
3. Embed the chart PNGs from `output/charts/` exactly as specified in each slide's "Visual" line.
4. Speaker notes can reuse the bulletted talking points verbatim.
5. Practice once or twice for timing — target 8 minutes.
