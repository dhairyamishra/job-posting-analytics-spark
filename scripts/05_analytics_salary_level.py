from pyspark.sql import SparkSession, functions as F


POSTINGS_PARQUET = "output/parquet/postings"
SKILLS_PARQUET = "output/parquet/skills"
LAYOFFS_PARQUET = "output/parquet/layoffs"
RESULTS_DIR = "output/results"


def write_result(df, name):
    df.coalesce(1).write.mode("overwrite").option("header", True).csv(f"{RESULTS_DIR}/{name}")


def main():
    spark = SparkSession.builder.appName("05_analytics_salary_level").getOrCreate()

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

    print("QUERY: q1_1_median_salary_by_level")
    q1_1 = spark.sql(
        """
        SELECT subcohort,
               formatted_experience_level AS experience_level,
               PERCENTILE_APPROX(normalized_salary, 0.5) AS median_salary,
               COUNT(*) AS posting_count
        FROM postings_tagged
        WHERE currency = 'USD'
          AND normalized_salary IS NOT NULL
          AND formatted_experience_level IS NOT NULL
        GROUP BY subcohort, formatted_experience_level
        ORDER BY experience_level, subcohort
        """
    )
    q1_1.show(truncate=False)
    write_result(q1_1, "q1_1_median_salary_by_level")

    print("QUERY: q1_2_experience_level_distribution")
    q1_2 = spark.sql(
        """
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
        ORDER BY experience_level, subcohort
        """
    )
    q1_2.show(truncate=False)
    write_result(q1_2, "q1_2_experience_level_distribution")

    print("DONE: script 05 completed")
    spark.stop()


if __name__ == "__main__":
    main()
