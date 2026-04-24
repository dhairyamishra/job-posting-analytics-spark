import glob
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.gridspec import GridSpec
from matplotlib.patches import FancyBboxPatch


RESULTS_DIR = "output/results"
CHARTS_DIR = "output/charts"

COLORS = {"layoff_affected": "#d97706", "non_affected": "#2563eb"}
BG_GRAY = "#e5e7eb"
FOOTER_GRAY = "#4b5563"
TEXT_DARK = "#111827"
DELTA_BOX = dict(boxstyle="round,pad=0.45", facecolor="#fef3c7", edgecolor="#fbbf24")

COHORT_ORDER = ["layoff_affected", "non_affected"]
DISPLAY_SHORT = {"layoff_affected": "Layoff-affected", "non_affected": "Other"}

EXPERIENCE_ORDER = [
    "Internship",
    "Entry level",
    "Associate",
    "Mid-Senior level",
    "Director",
    "Executive",
]

COHORT_DEF_LINE = (
    "Layoff-affected = 432 companies in layoffs 2020-2026 that also posted on "
    "LinkedIn 2023-2024 (predominantly big tech). Other = all other posting companies."
)

SAMPLE_SIZES = {}
DISPLAY_LONG = {}


def load_result(query_name):
    pattern = f"{RESULTS_DIR}/{query_name}/part-*.csv"
    matches = glob.glob(pattern)
    if not matches:
        print(f"WARN: no result CSV found for {query_name}")
        return None
    df = pd.read_csv(matches[0])
    print(f"LOAD: {query_name} rows={len(df)} cols={list(df.columns)}")
    return df


def init_sample_sizes():
    df = load_result("q3_1_remote_rate")
    if df is None:
        raise RuntimeError("Cannot derive sample sizes: q3_1_remote_rate CSV missing.")
    for _, row in df.iterrows():
        SAMPLE_SIZES[row["subcohort"]] = int(row["total_postings"])
    for key in COHORT_ORDER:
        label = "Layoff-affected companies" if key == "layoff_affected" else "Other companies"
        DISPLAY_LONG[key] = f"{label} (n={SAMPLE_SIZES[key]:,} postings)"


def save_chart(name):
    Path(CHARTS_DIR).mkdir(parents=True, exist_ok=True)
    path = f"{CHARTS_DIR}/{name}.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"SAVE: {path}")


def add_footer(fig, takeaway):
    fig.text(0.5, -0.01, COHORT_DEF_LINE, ha="center", fontsize=8, color=FOOTER_GRAY, wrap=True)
    fig.text(0.5, -0.05, takeaway, ha="center", fontsize=9, color=TEXT_DARK, weight="bold", wrap=True)


def set_header(fig, title, subtitle, y_title=0.97, y_subtitle=0.92):
    fig.suptitle(title, fontsize=13, y=y_title)
    fig.text(0.5, y_subtitle, subtitle, ha="center", fontsize=10, color=FOOTER_GRAY)


def chart_q1_1():
    df = load_result("q1_1_median_salary_by_level")
    if df is None:
        return

    median_pivot = df.pivot(index="experience_level", columns="subcohort", values="median_salary")
    count_pivot = df.pivot(index="experience_level", columns="subcohort", values="posting_count")
    levels = [lvl for lvl in EXPERIENCE_ORDER if lvl in median_pivot.index]
    median_pivot = median_pivot.reindex(levels)
    count_pivot = count_pivot.reindex(levels)

    fig, ax = plt.subplots(figsize=(11, 7))
    y_positions = np.arange(len(levels))

    for i, level in enumerate(levels):
        la = median_pivot.loc[level, "layoff_affected"]
        na = median_pivot.loc[level, "non_affected"]
        la_n = int(count_pivot.loc[level, "layoff_affected"])
        na_n = int(count_pivot.loc[level, "non_affected"])

        ax.plot([min(la, na), max(la, na)], [i, i], color="#9ca3af", linewidth=2, zorder=1)
        ax.scatter(
            [la], [i], color=COLORS["layoff_affected"], s=180, zorder=2,
            label=DISPLAY_SHORT["layoff_affected"] if i == 0 else None,
        )
        ax.scatter(
            [na], [i], color=COLORS["non_affected"], s=180, zorder=2,
            label=DISPLAY_SHORT["non_affected"] if i == 0 else None,
        )
        ax.annotate(
            f"${la:,.0f}", (la, i), xytext=(0, 12), textcoords="offset points",
            ha="center", fontsize=9, color=COLORS["layoff_affected"], weight="bold",
        )
        ax.annotate(
            f"${na:,.0f}", (na, i), xytext=(0, -18), textcoords="offset points",
            ha="center", fontsize=9, color=COLORS["non_affected"], weight="bold",
        )
        ax.annotate(
            f"n = {la_n:,} / {na_n:,}",
            xy=(1.01, i), xycoords=("axes fraction", "data"),
            fontsize=8, color="#6b7280", va="center",
        )

    ax.set_yticks(y_positions)
    ax.set_yticklabels(levels)
    ax.invert_yaxis()
    ax.set_xlabel("Median normalized salary (USD)")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x/1000:.0f}k"))
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.01), ncol=2, frameon=False, fontsize=10)
    ax.grid(axis="x", alpha=0.3)
    set_header(fig, "Q1.1  Median salary by experience level",
               "Median normalized USD salary. USD postings with a non-null salary only.",
               y_title=0.97, y_subtitle=0.93)
    fig.subplots_adjust(top=0.86, bottom=0.10, left=0.12, right=0.90)
    add_footer(fig, "Takeaway: Layoff-affected cohort pays more at every level; gap grows with seniority.")
    save_chart("q1_1_median_salary_by_level")


def chart_q1_2():
    df = load_result("q1_2_experience_level_distribution")
    if df is None:
        return

    pivot = df.pivot(index="subcohort", columns="experience_level", values="pct_of_subcohort").fillna(0)
    levels = [lvl for lvl in EXPERIENCE_ORDER if lvl in pivot.columns]
    pivot = pivot[levels]
    pivot = pivot.reindex(COHORT_ORDER)

    cmap = plt.cm.Greens
    level_colors = [cmap(0.30 + 0.55 * i / max(len(levels) - 1, 1)) for i in range(len(levels))]

    fig, ax = plt.subplots(figsize=(12, 4.5))
    y_positions = np.arange(len(COHORT_ORDER))
    left = np.zeros(len(COHORT_ORDER))

    for i, level in enumerate(levels):
        widths = pivot[level].values
        bars = ax.barh(y_positions, widths, left=left, color=level_colors[i], label=level, edgecolor="white")
        for bar, w in zip(bars, widths):
            if w >= 4:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_y() + bar.get_height() / 2,
                    f"{w:.1f}%", ha="center", va="center",
                    fontsize=9, color="white", weight="bold",
                )
        left += widths

    ax.set_yticks(y_positions)
    ax.set_yticklabels([DISPLAY_LONG[c] for c in COHORT_ORDER])
    ax.set_xlabel("Share of postings (%)")
    ax.set_xlim(0, 100)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.28), ncol=len(levels), fontsize=8, frameon=False)
    set_header(fig, "Q1.2  Experience-level distribution",
               "Share of postings by experience level, within each cohort.",
               y_title=0.96, y_subtitle=0.89)
    fig.subplots_adjust(top=0.82, bottom=0.25, left=0.22, right=0.95)
    add_footer(fig, "Takeaway: Layoff cohort is 66% mid-senior; other cohort is 40% entry-level and 43% mid-senior.")
    save_chart("q1_2_experience_level_distribution")


def chart_q2_1():
    df = load_result("q2_1_top_skills_by_subcohort")
    if df is None:
        return

    fig, axes = plt.subplots(1, 2, figsize=(13, 6), sharex=True)
    max_pct = df["pct_of_subcohort"].max()

    for ax, sub in zip(axes, COHORT_ORDER):
        sub_df = df[df["subcohort"] == sub].sort_values("pct_of_subcohort", ascending=True)
        bars = ax.barh(sub_df["skill_name"], sub_df["pct_of_subcohort"], color=COLORS[sub])
        for bar, pct, n in zip(bars, sub_df["pct_of_subcohort"], sub_df["n"]):
            ax.text(
                bar.get_width() + max_pct * 0.02,
                bar.get_y() + bar.get_height() / 2,
                f"{pct:.1f}% (n={int(n):,})", va="center", fontsize=8, color=TEXT_DARK,
            )
        ax.set_title(DISPLAY_LONG[sub], fontsize=10)
        ax.set_xlabel("Share of skill tags (%)")
        ax.set_xlim(0, max_pct * 1.25)
        ax.grid(axis="x", alpha=0.3)

    fig.suptitle("Q2.1  Top 10 skills by cohort", fontsize=13, y=1.02)
    fig.text(
        0.5, 0.97, "Top 10 skills by share of skill tags, per cohort. Shared x-axis.",
        ha="center", fontsize=10, color=FOOTER_GRAY,
    )
    fig.tight_layout()
    add_footer(fig, "Takeaway: Layoff cohort concentrates IT + Engineering (32%); other market spreads to Sales, Manufacturing, Healthcare.")
    save_chart("q2_1_top_skills_by_subcohort")


def chart_q2_2():
    df = load_result("q2_2_tech_skill_share")
    if df is None:
        return

    fig, axes = plt.subplots(1, 2, figsize=(11, 5.5))
    pcts = {}

    for ax, sub in zip(axes, COHORT_ORDER):
        row = df[df["subcohort"] == sub].iloc[0]
        tech = int(row["tech_skill_tags"])
        total = int(row["total_skill_tags"])
        other = total - tech
        pct = float(row["tech_pct"])
        pcts[sub] = pct

        ax.pie(
            [tech, other],
            colors=[COLORS[sub], BG_GRAY],
            startangle=90,
            counterclock=False,
            wedgeprops=dict(width=0.35, edgecolor="white"),
        )
        ax.text(0, 0.10, f"{pct:.1f}%", ha="center", va="center", fontsize=24, weight="bold", color=COLORS[sub])
        ax.text(0, -0.14, "tech-leaning", ha="center", va="center", fontsize=9, color=FOOTER_GRAY)
        ax.set_title(DISPLAY_LONG[sub], fontsize=10)
        ax.text(
            0, -1.22,
            f"Tech tags: {tech:,}\nOther tags: {other:,}",
            ha="center", va="center", fontsize=8, color=TEXT_DARK,
        )

    delta_pp = pcts["layoff_affected"] - pcts["non_affected"]
    ratio = pcts["layoff_affected"] / pcts["non_affected"]
    fig.text(
        0.5, -0.07,
        f"Layoff cohort has {ratio:.2f}x the tech-skill concentration  (+{delta_pp:.1f} percentage points)",
        ha="center", fontsize=10, color=TEXT_DARK, weight="bold", bbox=DELTA_BOX,
    )
    fig.suptitle("Q2.2  Tech-leaning skill share", fontsize=13, y=1.02)
    fig.text(
        0.5, 0.97, "Share of skill tags in ENG, IT, ANLS, PRDM.",
        ha="center", fontsize=10, color=FOOTER_GRAY,
    )
    fig.tight_layout()
    add_footer(fig, "Takeaway: Layoff-affected cohort is strongly tech-concentrated; consistent with matched companies being predominantly big tech.")
    save_chart("q2_2_tech_skill_share")


def chart_q3_1():
    df = load_result("q3_1_remote_rate")
    if df is None:
        return

    fig = plt.figure(figsize=(12, 5.5))
    gs = GridSpec(1, 3, width_ratios=[3, 1, 3], figure=fig, wspace=0.05)
    pcts = {}

    for i, sub in enumerate(COHORT_ORDER):
        row = df[df["subcohort"] == sub].iloc[0]
        pct = float(row["remote_pct"])
        remote = int(row["remote_postings"])
        total = int(row["total_postings"])
        pcts[sub] = pct

        ax = fig.add_subplot(gs[0, 0 if i == 0 else 2])
        ax.axis("off")
        rect = FancyBboxPatch(
            (0.04, 0.08), 0.92, 0.84,
            boxstyle="round,pad=0.02,rounding_size=0.05",
            linewidth=2, edgecolor=COLORS[sub],
            facecolor=COLORS[sub] + "22",
            transform=ax.transAxes,
        )
        ax.add_patch(rect)
        ax.text(0.5, 0.83, DISPLAY_LONG[sub], ha="center", va="center",
                fontsize=10, weight="bold", color=TEXT_DARK, transform=ax.transAxes)
        ax.text(0.5, 0.52, f"{pct:.2f}%", ha="center", va="center",
                fontsize=44, weight="bold", color=COLORS[sub], transform=ax.transAxes)
        ax.text(0.5, 0.22, f"{remote:,} of {total:,} postings\nallow remote",
                ha="center", va="center", fontsize=10, color=FOOTER_GRAY, transform=ax.transAxes)

    delta_ax = fig.add_subplot(gs[0, 1])
    delta_ax.axis("off")
    delta_pp = pcts["layoff_affected"] - pcts["non_affected"]
    ratio = pcts["layoff_affected"] / pcts["non_affected"]
    delta_ax.text(
        0.5, 0.5, f"+{delta_pp:.2f} pp\n({ratio:.2f}x)",
        ha="center", va="center", fontsize=16, weight="bold", color=TEXT_DARK,
        bbox=DELTA_BOX, transform=delta_ax.transAxes,
    )

    fig.suptitle("Q3.1  Remote-allowed rate by cohort", fontsize=13, y=0.98)
    fig.text(
        0.5, 0.90, "Share of postings with remote_allowed = true.",
        ha="center", fontsize=10, color=FOOTER_GRAY,
    )
    add_footer(fig, "Takeaway: Layoff cohort allows remote at about 1.7x the rate of the broader market.")
    save_chart("q3_1_remote_rate")


def chart_q3_2():
    df = load_result("q3_2_top_states_by_subcohort")
    if df is None:
        return

    df = df.copy()
    df["state_disp"] = df["state"].str.upper()

    fig, axes = plt.subplots(1, 2, figsize=(13, 6), sharex=True)
    max_pct = df["pct_of_subcohort"].max()

    for ax, sub in zip(axes, COHORT_ORDER):
        sub_df = df[df["subcohort"] == sub].sort_values("pct_of_subcohort", ascending=True)
        bars = ax.barh(sub_df["state_disp"], sub_df["pct_of_subcohort"], color=COLORS[sub])
        for bar, pct, n in zip(bars, sub_df["pct_of_subcohort"], sub_df["n"]):
            ax.text(
                bar.get_width() + max_pct * 0.02,
                bar.get_y() + bar.get_height() / 2,
                f"{pct:.1f}% (n={int(n):,})", va="center", fontsize=8, color=TEXT_DARK,
            )
        ax.set_title(DISPLAY_LONG[sub], fontsize=10)
        ax.set_xlabel("Share of postings (%)")
        ax.set_xlim(0, max_pct * 1.25)
        ax.grid(axis="x", alpha=0.3)

    fig.suptitle("Q3.2  Top 10 states by cohort", fontsize=13, y=1.02)
    fig.text(
        0.5, 0.97,
        "Top 10 states by share of postings, per cohort. Shared x-axis. "
        "(UNITED STATES = postings whose location had no state portion.)",
        ha="center", fontsize=9, color=FOOTER_GRAY,
    )
    fig.tight_layout()
    add_footer(fig, "Takeaway: Layoff cohort clusters in CA + VA + WA + TX + NY tech hubs (58%); other cohort disperses to FL, NC, PA, OH.")
    save_chart("q3_2_top_states_by_subcohort")


def main():
    os.makedirs(CHARTS_DIR, exist_ok=True)
    init_sample_sizes()
    print(f"STEP: building Phase 2 charts; sample sizes = {SAMPLE_SIZES}")
    chart_q1_1()
    chart_q1_2()
    chart_q2_1()
    chart_q2_2()
    chart_q3_1()
    chart_q3_2()
    print("DONE: all charts regenerated")


if __name__ == "__main__":
    main()
