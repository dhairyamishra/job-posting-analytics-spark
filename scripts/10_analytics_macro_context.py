from pyspark.sql import SparkSession


JOLTS_PARQUET = "output/parquet/jolts"
RESULTS_DIR = "output/results"


def write_result(df, name):
    df.coalesce(1).write.mode("overwrite").option("header", True).csv(f"{RESULTS_DIR}/{name}")


def main():
    spark = SparkSession.builder.appName("10_analytics_macro_context").getOrCreate()

    spark.read.parquet(JOLTS_PARQUET).createOrReplaceTempView("jolts")

    print("QUERY: q4_1_jolts_layoff_rate")
    q4_1 = spark.sql(
        """
        SELECT obs_date, year, month, industry, value AS layoffs_discharges_rate
        FROM jolts
        WHERE metric = 'layoffs_discharges_rate'
        ORDER BY industry, obs_date
        """
    )
    q4_1.show(10, truncate=False)
    print(f"QUERY: q4_1 row_count={q4_1.count()}")
    write_result(q4_1, "q4_1_jolts_layoff_rate")

    print("QUERY: q4_2_jolts_openings_hires_rate")
    q4_2 = spark.sql(
        """
        SELECT obs_date, year, month, industry,
               MAX(CASE WHEN metric = 'job_openings_rate' THEN value END) AS job_openings_rate,
               MAX(CASE WHEN metric = 'hires_rate'        THEN value END) AS hires_rate
        FROM jolts
        WHERE metric IN ('job_openings_rate', 'hires_rate')
        GROUP BY obs_date, year, month, industry
        ORDER BY industry, obs_date
        """
    )
    q4_2.show(10, truncate=False)
    print(f"QUERY: q4_2 row_count={q4_2.count()}")
    write_result(q4_2, "q4_2_jolts_openings_hires_rate")

    print("DONE: script 10 completed")
    spark.stop()


if __name__ == "__main__":
    main()
