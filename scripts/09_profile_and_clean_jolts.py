from pyspark.sql import SparkSession, functions as F


INPUT_FILES = [
    "data/jolts/jt.data.2.JobOpenings",
    "data/jolts/jt.data.3.Hires",
    "data/jolts/jt.data.6.LayoffsDischarges",
]
PROFILE_OUTPUT_PATH = "output/profiles/jolts"
PARQUET_OUTPUT_PATH = "output/parquet/jolts"

KEEP_SERIES_IDS = [
    "JTS000000000000000JOR",
    "JTS000000000000000HIR",
    "JTS000000000000000LDR",
    "JTS510000000000000JOR",
    "JTS510000000000000HIR",
    "JTS510000000000000LDR",
]

METRIC_BY_DATAELEMENT = {
    "JO": "job_openings_rate",
    "HI": "hires_rate",
    "LD": "layoffs_discharges_rate",
}

CATEGORICAL_COLUMNS = ["industry", "metric"]
NUMERIC_COLUMNS = ["value"]


def add_metric(metrics, dataset, column_name, metric, value):
    metrics.append((dataset, column_name, metric, str(value)))


def row_count(df):
    return df.count()


def read_jolts_file(spark, path):
    raw = spark.read.option("header", True).option("sep", "\t").csv(path)
    raw = raw.toDF(*[c.strip() for c in raw.columns])
    return raw.select(
        F.trim(F.col("series_id")).alias("series_id"),
        F.trim(F.col("year")).alias("year"),
        F.trim(F.col("period")).alias("period"),
        F.trim(F.col("value")).alias("value"),
    )


def main():
    spark = SparkSession.builder.appName("09_profile_and_clean_jolts").getOrCreate()
    metrics = []

    print("STEP: read raw jolts files")
    per_file = [read_jolts_file(spark, p) for p in INPUT_FILES]
    df = per_file[0]
    for other in per_file[1:]:
        df = df.unionByName(other)

    print("PROFILE: raw schema")
    df.printSchema()

    raw_count = row_count(df)
    print(f"PROFILE: raw_row_count={raw_count}")
    add_metric(metrics, "jolts_raw", "_dataset", "row_count", raw_count)

    print("PROFILE: raw null counts per column")
    null_exprs = [F.sum(F.when(F.col(c).isNull() | (F.col(c) == ""), 1).otherwise(0)).alias(c) for c in df.columns]
    null_row = df.select(*null_exprs).collect()[0].asDict()
    for col_name, null_count in null_row.items():
        print(f"PROFILE: null_count[{col_name}]={null_count}")
        add_metric(metrics, "jolts_raw", col_name, "null_count", null_count)

    print("PROFILE: sample raw rows")
    df.show(5, truncate=False)

    print("CLEAN: filter to 6 target series ids")
    before = row_count(df)
    df = df.filter(F.col("series_id").isin(KEEP_SERIES_IDS))
    after = row_count(df)
    dropped = before - after
    print(f"CLEAN: dropped[non_target_series]={dropped}")
    add_metric(metrics, "jolts_clean", "_dataset", "dropped_non_target_series", dropped)

    print("CLEAN: drop annual-average period M13")
    before = after
    df = df.filter(F.col("period") != "M13")
    after = row_count(df)
    dropped = before - after
    print(f"CLEAN: dropped[period_m13]={dropped}")
    add_metric(metrics, "jolts_clean", "_dataset", "dropped_period_m13", dropped)

    print("CLEAN: cast year and value, derive month, obs_date, industry, metric")
    df = (
        df.withColumn("year", F.col("year").cast("int"))
        .withColumn("value", F.col("value").cast("double"))
        .withColumn("month", F.substring(F.col("period"), 2, 2).cast("int"))
        .withColumn(
            "obs_date",
            F.to_date(
                F.concat_ws("-", F.col("year"), F.lpad(F.col("month").cast("string"), 2, "0"), F.lit("01"))
            ),
        )
        .withColumn(
            "industry",
            F.when(F.col("series_id").startswith("JTS000000"), F.lit("Total Nonfarm")).otherwise(F.lit("Information")),
        )
        .withColumn("dataelement", F.substring(F.col("series_id"), 19, 2))
    )

    metric_expr = F.col("dataelement")
    for de_code, metric_name in METRIC_BY_DATAELEMENT.items():
        metric_expr = F.when(F.col("dataelement") == de_code, F.lit(metric_name)).otherwise(metric_expr)
    df = df.withColumn("metric", metric_expr)

    clean_df = df.select("obs_date", "year", "month", "industry", "metric", "value")

    print("PROFILE: distinct counts and top-10 for categoricals")
    for col_name in CATEGORICAL_COLUMNS:
        distinct_count = clean_df.select(col_name).distinct().count()
        print(f"PROFILE: distinct_count[{col_name}]={distinct_count}")
        add_metric(metrics, "jolts_clean", col_name, "distinct_count", distinct_count)
        print(f"PROFILE: top10[{col_name}]")
        clean_df.groupBy(col_name).count().orderBy(F.desc("count")).show(10, truncate=False)

    print("PROFILE: numeric describe")
    clean_df.select(*NUMERIC_COLUMNS).describe().show(truncate=False)

    print("PROFILE: sample cleaned rows")
    clean_df.orderBy("industry", "metric", "obs_date").show(5, truncate=False)

    final_count = row_count(clean_df)
    total_dropped = raw_count - final_count
    print(f"CLEAN: final_row_count={final_count}")
    print(f"CLEAN: total_dropped={total_dropped}")
    print("CLEAN: cleaned schema")
    clean_df.printSchema()

    add_metric(metrics, "jolts_clean", "_dataset", "row_count", final_count)
    add_metric(metrics, "jolts_clean", "_dataset", "total_dropped", total_dropped)

    profile_df = spark.createDataFrame(metrics, ["dataset", "column", "metric", "value"])
    profile_df.coalesce(1).write.mode("overwrite").option("header", True).csv(PROFILE_OUTPUT_PATH)
    clean_df.write.mode("overwrite").parquet(PARQUET_OUTPUT_PATH)

    print("DONE: profile and parquet outputs written")
    spark.stop()


if __name__ == "__main__":
    main()
