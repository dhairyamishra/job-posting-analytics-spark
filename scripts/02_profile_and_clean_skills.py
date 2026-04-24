from pyspark.sql import SparkSession, functions as F


JOB_SKILLS_INPUT_PATH = "data/linkedin/jobs/job_skills.csv"
SKILLS_INPUT_PATH = "data/linkedin/mappings/skills.csv"
PROFILE_OUTPUT_PATH = "output/profiles/skills"
PARQUET_OUTPUT_PATH = "output/parquet/skills"


def add_metric(metrics, dataset, column_name, metric, value):
    metrics.append((dataset, column_name, metric, str(value)))


def row_count(df):
    return df.count()


def profile_dataset(df, dataset_name, key_columns, metrics):
    print(f"PROFILE: {dataset_name} schema")
    df.printSchema()

    count = row_count(df)
    print(f"PROFILE: {dataset_name}_row_count={count}")
    add_metric(metrics, dataset_name, "_dataset", "row_count", count)

    print(f"PROFILE: {dataset_name} null counts")
    null_exprs = [F.sum(F.when(F.col(c).isNull(), 1).otherwise(0)).alias(c) for c in df.columns]
    null_row = df.select(*null_exprs).collect()[0].asDict()
    for col_name, null_count in null_row.items():
        print(f"PROFILE: null_count[{dataset_name}.{col_name}]={null_count}")
        add_metric(metrics, dataset_name, col_name, "null_count", null_count)

    for col_name in key_columns:
        distinct_count = df.select(col_name).distinct().count()
        print(f"PROFILE: distinct_count[{dataset_name}.{col_name}]={distinct_count}")
        add_metric(metrics, dataset_name, col_name, "distinct_count", distinct_count)

        print(f"PROFILE: top10[{dataset_name}.{col_name}]")
        df.groupBy(col_name).count().orderBy(F.desc("count")).show(10, truncate=False)

    print(f"PROFILE: {dataset_name} sample rows")
    df.show(5, truncate=False)

    return count


def main():
    spark = SparkSession.builder.appName("02_profile_and_clean_skills").getOrCreate()
    metrics = []

    print("STEP: read source CSVs")
    job_skills_df = (
        spark.read.option("header", True)
        .option("multiLine", True)
        .option("escape", '"')
        .option("quote", '"')
        .csv(JOB_SKILLS_INPUT_PATH)
        .select("job_id", "skill_abr")
    )
    skills_df = (
        spark.read.option("header", True)
        .option("multiLine", True)
        .option("escape", '"')
        .option("quote", '"')
        .csv(SKILLS_INPUT_PATH)
        .select("skill_abr", "skill_name")
    )

    job_skills_count = profile_dataset(job_skills_df, "job_skills_raw", ["skill_abr", "job_id"], metrics)
    profile_dataset(skills_df, "skills_raw", ["skill_abr", "skill_name"], metrics)

    print("CLEAN: left join job_skills to skills on skill_abr")
    joined_df = job_skills_df.join(skills_df, on="skill_abr", how="left")
    post_join_count = row_count(joined_df)
    print(f"CLEAN: post_join_row_count={post_join_count}")
    add_metric(metrics, "skills_clean", "_dataset", "post_join_row_count", post_join_count)

    print("CLEAN: drop orphaned skill codes where skill_name is null")
    no_orphans_df = joined_df.filter(F.col("skill_name").isNotNull())
    post_orphan_count = row_count(no_orphans_df)
    orphan_dropped = post_join_count - post_orphan_count
    print(f"CLEAN: dropped[orphaned_skill_codes]={orphan_dropped}")
    add_metric(metrics, "skills_clean", "_dataset", "dropped_orphaned_skill_codes", orphan_dropped)

    print("CLEAN: deduplicate on (job_id, skill_abr)")
    final_df = no_orphans_df.dropDuplicates(["job_id", "skill_abr"]).select("job_id", "skill_abr", "skill_name")
    final_count = row_count(final_df)
    duplicate_dropped = post_orphan_count - final_count
    print(f"CLEAN: dropped[duplicate_job_skill_pairs]={duplicate_dropped}")
    print(f"CLEAN: final_row_count={final_count}")
    print(f"CLEAN: total_dropped={job_skills_count - final_count}")
    print("CLEAN: final schema")
    final_df.printSchema()

    add_metric(metrics, "skills_clean", "_dataset", "row_count", final_count)
    add_metric(metrics, "skills_clean", "_dataset", "dropped_duplicate_job_skill_pairs", duplicate_dropped)
    add_metric(metrics, "skills_clean", "_dataset", "total_dropped", job_skills_count - final_count)

    profile_df = spark.createDataFrame(metrics, ["dataset", "column", "metric", "value"])
    profile_df.coalesce(1).write.mode("overwrite").option("header", True).csv(PROFILE_OUTPUT_PATH)
    final_df.write.mode("overwrite").parquet(PARQUET_OUTPUT_PATH)

    print("DONE: profile and parquet outputs written")
    spark.stop()


if __name__ == "__main__":
    main()
