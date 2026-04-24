from pyspark.sql import SparkSession, functions as F


INPUT_PATH = "data/linkedin/postings.csv"
PROFILE_OUTPUT_PATH = "output/profiles/postings"
PARQUET_OUTPUT_PATH = "output/parquet/postings"

KEEP_COLUMNS = [
    "job_id",
    "company_id",
    "company_name",
    "title",
    "location",
    "formatted_work_type",
    "formatted_experience_level",
    "remote_allowed",
    "min_salary",
    "max_salary",
    "med_salary",
    "pay_period",
    "normalized_salary",
    "currency",
    "views",
    "applies",
    "original_listed_time",
    "zip_code",
]

CATEGORICAL_COLUMNS = [
    "formatted_work_type",
    "formatted_experience_level",
    "currency",
    "state",
    "city",
]

NUMERIC_COLUMNS = ["normalized_salary", "min_salary", "med_salary", "max_salary", "views", "applies"]


def add_metric(metrics, dataset, column_name, metric, value):
    metrics.append((dataset, column_name, metric, str(value)))


def row_count(df):
    return df.count()


def main():
    spark = SparkSession.builder.appName("01_profile_and_clean_postings").getOrCreate()
    metrics = []

    print("STEP: read raw postings")
    raw_df = (
        spark.read.option("header", True)
        .option("multiLine", True)
        .option("escape", '"')
        .option("quote", '"')
        .csv(INPUT_PATH)
    )
    df = raw_df.select(*KEEP_COLUMNS)

    print("PROFILE: raw schema")
    df.printSchema()

    raw_count = row_count(df)
    print(f"PROFILE: raw_row_count={raw_count}")
    add_metric(metrics, "postings_raw", "_dataset", "row_count", raw_count)

    print("PROFILE: null counts per column")
    null_exprs = [F.sum(F.when(F.col(c).isNull(), 1).otherwise(0)).alias(c) for c in df.columns]
    null_row = df.select(*null_exprs).collect()[0].asDict()
    for col_name, null_count in null_row.items():
        print(f"PROFILE: null_count[{col_name}]={null_count}")
        add_metric(metrics, "postings_raw", col_name, "null_count", null_count)

    for col_name in ["formatted_work_type", "formatted_experience_level", "currency"]:
        distinct_count = df.select(col_name).distinct().count()
        print(f"PROFILE: distinct_count[{col_name}]={distinct_count}")
        add_metric(metrics, "postings_raw", col_name, "distinct_count", distinct_count)

    print("PROFILE: numeric describe")
    df.select(*NUMERIC_COLUMNS).describe().show(truncate=False)

    print("PROFILE: sample rows")
    df.show(5, truncate=False)

    clean_df = df
    drop_metrics = []

    print("CLEAN: split location into city/state")
    clean_df = (
        clean_df.withColumn("city", F.lower(F.trim(F.split(F.col("location"), ",").getItem(0))))
        .withColumn("state", F.lower(F.trim(F.split(F.col("location"), ",").getItem(1))))
    )

    print("PROFILE: top-10 value counts for key categoricals")
    for col_name in CATEGORICAL_COLUMNS:
        print(f"PROFILE: top10[{col_name}]")
        (
            clean_df.groupBy(col_name)
            .count()
            .orderBy(F.desc("count"))
            .show(10, truncate=False)
        )

    print("CLEAN: cast zip_code to string")
    clean_df = clean_df.withColumn("zip_code", F.col("zip_code").cast("string"))

    print("CLEAN: derive listed_date from original_listed_time")
    clean_df = clean_df.withColumn(
        "listed_date",
        F.from_unixtime(F.col("original_listed_time") / F.lit(1000)).cast("date"),
    )

    before = row_count(clean_df)
    clean_df = clean_df.filter(
        ~(
            F.col("min_salary").isNotNull()
            & F.col("max_salary").isNotNull()
            & (F.col("min_salary").cast("double") > F.col("max_salary").cast("double"))
        )
    )
    after = row_count(clean_df)
    dropped = before - after
    print(f"CLEAN: dropped[min_salary_gt_max_salary]={dropped}")
    drop_metrics.append(("postings_clean", "_dataset", "dropped_min_salary_gt_max_salary", str(dropped)))

    before = after
    clean_df = clean_df.filter(
        F.col("normalized_salary").isNull()
        | (
            (F.col("normalized_salary").cast("double") >= F.lit(10000))
            & (F.col("normalized_salary").cast("double") <= F.lit(1000000))
        )
    )
    after = row_count(clean_df)
    dropped = before - after
    print(f"CLEAN: dropped[normalized_salary_out_of_bounds]={dropped}")
    drop_metrics.append(("postings_clean", "_dataset", "dropped_normalized_salary_out_of_bounds", str(dropped)))

    print("CLEAN: cast remote_allowed to boolean")
    clean_df = clean_df.withColumn("remote_allowed", F.when(F.col("remote_allowed") == 1, F.lit(True)).otherwise(F.lit(False)))

    print("CLEAN: add company_normalized")
    clean_df = clean_df.withColumn(
        "company_normalized",
        F.lower(
            F.trim(
                F.regexp_replace(
                    F.col("company_name"),
                    r"(?i)\s*(inc|corp|corporation|llc|ltd|limited)\.?$",
                    "",
                )
            )
        ),
    )

    final_count = row_count(clean_df)
    total_dropped = raw_count - final_count
    print(f"CLEAN: final_row_count={final_count}")
    print(f"CLEAN: total_dropped={total_dropped}")
    print("CLEAN: cleaned schema")
    clean_df.printSchema()

    add_metric(metrics, "postings_clean", "_dataset", "row_count", final_count)
    add_metric(metrics, "postings_clean", "_dataset", "total_dropped", total_dropped)
    for item in drop_metrics:
        metrics.append(item)

    profile_df = spark.createDataFrame(metrics, ["dataset", "column", "metric", "value"])
    profile_df.coalesce(1).write.mode("overwrite").option("header", True).csv(PROFILE_OUTPUT_PATH)
    clean_df.write.mode("overwrite").parquet(PARQUET_OUTPUT_PATH)

    print("DONE: profile and parquet outputs written")
    spark.stop()


if __name__ == "__main__":
    main()
