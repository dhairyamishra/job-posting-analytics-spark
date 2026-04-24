from pyspark.sql import SparkSession


POSTINGS_PARQUET = "output/parquet/postings"
LAYOFFS_PARQUET = "output/parquet/layoffs"
SUMMARY_OUTPUT_PATH = "output/diagnostics/join_hit_rate"


def scalar(spark, sql):
    return spark.sql(sql).collect()[0][0]


def main():
    spark = SparkSession.builder.appName("04_diagnostic_join_check").getOrCreate()

    spark.read.parquet(POSTINGS_PARQUET).createOrReplaceTempView("postings")
    spark.read.parquet(LAYOFFS_PARQUET).createOrReplaceTempView("layoffs")

    distinct_layoff_companies = scalar(
        spark,
        "SELECT COUNT(DISTINCT company_normalized) FROM layoffs WHERE company_normalized IS NOT NULL",
    )
    distinct_posting_companies = scalar(
        spark,
        "SELECT COUNT(DISTINCT company_normalized) FROM postings WHERE company_normalized IS NOT NULL",
    )
    matched_companies = scalar(
        spark,
        """
        SELECT COUNT(*) FROM (
            SELECT DISTINCT l.company_normalized
            FROM layoffs l
            INNER JOIN postings p ON l.company_normalized = p.company_normalized
            WHERE l.company_normalized IS NOT NULL
        )
        """,
    )
    total_postings = scalar(spark, "SELECT COUNT(*) FROM postings")
    matched_postings = scalar(
        spark,
        """
        SELECT COUNT(*) FROM postings p
        WHERE p.company_normalized IN (
            SELECT DISTINCT company_normalized FROM layoffs WHERE company_normalized IS NOT NULL
        )
        """,
    )

    company_hit_rate_pct = (
        round(matched_companies / distinct_layoff_companies * 100, 2)
        if distinct_layoff_companies
        else 0.0
    )
    posting_share_in_layoff_cohort_pct = (
        round(matched_postings / total_postings * 100, 2) if total_postings else 0.0
    )

    print(f"DIAG: distinct_layoff_companies={distinct_layoff_companies}")
    print(f"DIAG: distinct_posting_companies={distinct_posting_companies}")
    print(f"DIAG: matched_companies={matched_companies}")
    print(f"DIAG: company_hit_rate_pct={company_hit_rate_pct}")
    print(f"DIAG: total_postings={total_postings}")
    print(f"DIAG: matched_postings={matched_postings}")
    print(f"DIAG: posting_share_in_layoff_cohort_pct={posting_share_in_layoff_cohort_pct}")

    print("DIAG: top20_unmatched_layoff_companies (by total_laid_off desc)")
    spark.sql(
        """
        SELECT l.company, l.company_normalized, l.total_laid_off, l.date, l.industry, l.country
        FROM layoffs l
        LEFT ANTI JOIN (
            SELECT DISTINCT company_normalized FROM postings WHERE company_normalized IS NOT NULL
        ) p ON l.company_normalized = p.company_normalized
        WHERE l.company_normalized IS NOT NULL
        ORDER BY l.total_laid_off DESC NULLS LAST
        LIMIT 20
        """
    ).show(20, truncate=False)

    summary_rows = [
        ("distinct_layoff_companies", str(distinct_layoff_companies)),
        ("distinct_posting_companies", str(distinct_posting_companies)),
        ("matched_companies", str(matched_companies)),
        ("company_hit_rate_pct", str(company_hit_rate_pct)),
        ("total_postings", str(total_postings)),
        ("matched_postings", str(matched_postings)),
        ("posting_share_in_layoff_cohort_pct", str(posting_share_in_layoff_cohort_pct)),
    ]
    summary_df = spark.createDataFrame(summary_rows, ["metric", "value"])
    summary_df.coalesce(1).write.mode("overwrite").option("header", True).csv(SUMMARY_OUTPUT_PATH)

    print("DONE: diagnostic summary written")
    spark.stop()


if __name__ == "__main__":
    main()
