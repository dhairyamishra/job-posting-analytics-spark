from pyspark.sql import SparkSession, functions as F


POSTINGS_PARQUET = "output/parquet/postings"
SKILLS_PARQUET = "output/parquet/skills"
LAYOFFS_PARQUET = "output/parquet/layoffs"
RESULTS_DIR = "output/results"


def write_result(df, name):
    df.coalesce(1).write.mode("overwrite").option("header", True).csv(f"{RESULTS_DIR}/{name}")


def main():
    spark = SparkSession.builder.appName("06_analytics_skills_pivot").getOrCreate()

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

    print("QUERY: q2_1_top_skills_by_subcohort")
    q2_1 = spark.sql(
        """
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
        ORDER BY subcohort, n DESC
        """
    )
    q2_1.show(truncate=False)
    write_result(q2_1, "q2_1_top_skills_by_subcohort")

    print("QUERY: q2_2_tech_skill_share")
    q2_2 = spark.sql(
        """
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
        ORDER BY subcohort
        """
    )
    q2_2.show(truncate=False)
    write_result(q2_2, "q2_2_tech_skill_share")

    print("DONE: script 06 completed")
    spark.stop()


if __name__ == "__main__":
    main()
