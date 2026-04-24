from pyspark.sql import SparkSession, functions as F


POSTINGS_PARQUET = "output/parquet/postings"
SKILLS_PARQUET = "output/parquet/skills"
LAYOFFS_PARQUET = "output/parquet/layoffs"
RESULTS_DIR = "output/results"


def write_result(df, name):
    df.coalesce(1).write.mode("overwrite").option("header", True).csv(f"{RESULTS_DIR}/{name}")


def main():
    spark = SparkSession.builder.appName("07_analytics_geo_remote").getOrCreate()

    postings = spark.read.parquet(POSTINGS_PARQUET)
    skills = spark.read.parquet(SKILLS_PARQUET)
    layoffs = spark.read.parquet(LAYOFFS_PARQUET)

    postings = postings.withColumn(
        "company_normalized",
        F.when(F.col("company_normalized").isin("x", "x corp"), "twitter").otherwise(
            F.col("company_normalized")
        ),
    )

    postings.createOrReplaceTempView("postings")
    skills.createOrReplaceTempView("skills")
    layoffs.createOrReplaceTempView("layoffs")

    spark.sql(
        """
        CREATE OR REPLACE TEMP VIEW layoff_companies AS
        SELECT DISTINCT company_normalized
        FROM layoffs
        WHERE company_normalized IS NOT NULL
          AND (total_laid_off IS NOT NULL OR percentage_laid_off IS NOT NULL)
        """
    )

    spark.sql(
        """
        CREATE OR REPLACE TEMP VIEW postings_tagged AS
        SELECT p.*,
               CASE WHEN lc.company_normalized IS NOT NULL
                    THEN 'layoff_affected'
                    ELSE 'non_affected'
               END AS subcohort
        FROM postings p
        LEFT JOIN layoff_companies lc
               ON p.company_normalized = lc.company_normalized
        WHERE p.company_normalized IS NOT NULL
        """
    )

    print("QUERY: q3_1_remote_rate")
    q3_1 = spark.sql(
        """
        SELECT subcohort,
               COUNT(*) AS total_postings,
               SUM(CASE WHEN remote_allowed = true THEN 1 ELSE 0 END) AS remote_postings,
               ROUND(100.0 * SUM(CASE WHEN remote_allowed = true THEN 1 ELSE 0 END) / COUNT(*), 2) AS remote_pct
        FROM postings_tagged
        GROUP BY subcohort
        ORDER BY subcohort
        """
    )
    q3_1.show(truncate=False)
    write_result(q3_1, "q3_1_remote_rate")

    print("QUERY: q3_2_top_states_by_subcohort")
    q3_2 = spark.sql(
        """
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
        ORDER BY subcohort, n DESC
        """
    )
    q3_2.show(truncate=False)
    write_result(q3_2, "q3_2_top_states_by_subcohort")

    print("DONE: script 07 completed")
    spark.stop()


if __name__ == "__main__":
    main()
