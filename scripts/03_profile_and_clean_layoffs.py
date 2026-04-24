from pyspark.sql import SparkSession, functions as F


INPUT_PATH = "data/layoffs/layoffs.csv"
PROFILE_OUTPUT_PATH = "output/profiles/layoffs"
PARQUET_OUTPUT_PATH = "output/parquet/layoffs"

KEEP_COLUMNS = [
    "company",
    "location",
    "total_laid_off",
    "date",
    "percentage_laid_off",
    "industry",
    "stage",
    "country",
]

CATEGORICAL_COLUMNS = ["country", "industry", "stage", "location"]
DISTINCT_COLUMNS = ["country", "industry", "stage"]
NUMERIC_COLUMNS = ["total_laid_off", "percentage_laid_off"]


def add_metric(metrics, dataset, column_name, metric, value):
    metrics.append((dataset, column_name, metric, str(value)))


def row_count(df):
    return df.count()


def main():
    spark = SparkSession.builder.appName("03_profile_and_clean_layoffs").getOrCreate()
    metrics = []

    print("STEP: read raw layoffs")
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
    add_metric(metrics, "layoffs_raw", "_dataset", "row_count", raw_count)

    print("PROFILE: null counts per column")
    null_exprs = [F.sum(F.when(F.col(c).isNull(), 1).otherwise(0)).alias(c) for c in df.columns]
    null_row = df.select(*null_exprs).collect()[0].asDict()
    for col_name, null_count in null_row.items():
        print(f"PROFILE: null_count[{col_name}]={null_count}")
        add_metric(metrics, "layoffs_raw", col_name, "null_count", null_count)

    for col_name in DISTINCT_COLUMNS:
        distinct_count = df.select(col_name).distinct().count()
        print(f"PROFILE: distinct_count[{col_name}]={distinct_count}")
        add_metric(metrics, "layoffs_raw", col_name, "distinct_count", distinct_count)

    print("PROFILE: top-10 value counts for key categoricals")
    for col_name in CATEGORICAL_COLUMNS:
        print(f"PROFILE: top10[{col_name}]")
        df.groupBy(col_name).count().orderBy(F.desc("count")).show(10, truncate=False)

    print("PROFILE: numeric describe")
    df.select(*NUMERIC_COLUMNS).describe().show(truncate=False)

    print("PROFILE: sample rows")
    df.show(5, truncate=False)

    clean_df = df
    drop_metrics = []

    print("CLEAN: parse date as DateType (M/d/yyyy)")
    clean_df = clean_df.withColumn("date", F.to_date(F.col("date"), "M/d/yyyy"))

    before = row_count(clean_df)
    clean_df = clean_df.filter(
        F.col("total_laid_off").isNotNull() | F.col("percentage_laid_off").isNotNull()
    )
    after = row_count(clean_df)
    dropped = before - after
    print(f"CLEAN: dropped[both_laid_off_fields_null]={dropped}")
    drop_metrics.append(("layoffs_clean", "_dataset", "dropped_both_laid_off_fields_null", str(dropped)))

    print("CLEAN: cast total_laid_off as IntegerType")
    clean_df = clean_df.withColumn("total_laid_off", F.col("total_laid_off").cast("int"))

    print("CLEAN: cast percentage_laid_off as DoubleType")
    clean_df = clean_df.withColumn("percentage_laid_off", F.col("percentage_laid_off").cast("double"))

    print("CLEAN: add company_normalized")
    clean_df = clean_df.withColumn(
        "company_normalized",
        F.lower(
            F.trim(
                F.regexp_replace(
                    F.col("company"),
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

    add_metric(metrics, "layoffs_clean", "_dataset", "row_count", final_count)
    add_metric(metrics, "layoffs_clean", "_dataset", "total_dropped", total_dropped)
    for item in drop_metrics:
        metrics.append(item)

    profile_df = spark.createDataFrame(metrics, ["dataset", "column", "metric", "value"])
    profile_df.coalesce(1).write.mode("overwrite").option("header", True).csv(PROFILE_OUTPUT_PATH)
    clean_df.write.mode("overwrite").parquet(PARQUET_OUTPUT_PATH)

    print("DONE: profile and parquet outputs written")
    spark.stop()


if __name__ == "__main__":
    main()
