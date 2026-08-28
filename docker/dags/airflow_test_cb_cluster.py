"""Example DAG: query a Couchbase scope through the cluster returned by :class:`CouchbaseHook`."""

from __future__ import annotations

import os
import tempfile
from datetime import timedelta

import pandas as pd
import pendulum
from couchbase.options import KnownConfigProfiles

from airflow.sdk import dag, task
from airflow_providers_couchbase.hooks import Config, CouchbaseHook

BUCKET = "travel-sample"
SCOPE = "inventory"
QUERY = "select meta().id from airline limit 10"

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email": ["airflow@example.com"],
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 0,
    "retry_delay": timedelta(minutes=5),
}


@dag(
    "airflow_test_couchbase_cluster",
    default_args=default_args,
    schedule=None,
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    tags=["couchbase", "example"],
    catchup=False,
    max_active_runs=1,
)
def couchbase_cluster_test():
    @task()
    def get_data_from_airline_collection() -> list[dict]:
        hook = CouchbaseHook(
            couchbase_conn_id="couchbase_conn_id",
            config=Config(profile=KnownConfigProfiles.WanDevelopment),
        )

        with hook:
            cluster = hook.get_conn()
            cluster.wait_until_ready(timedelta(seconds=30))
            scope = cluster.bucket(BUCKET).scope(SCOPE)
            return list(scope.query(QUERY))

    @task()
    def transform_data_to_csv(rows) -> str:
        # Transform data into a pandas DataFrame.
        df = pd.DataFrame(rows)

        # Save the DataFrame as a CSV file in a temporary file.
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_file:
            df.to_csv(temp_file.name, index=False)
            return temp_file.name

    @task()
    def load_data_to_s3(file_path) -> None:
        # Placeholder for the load step: read the CSV back to verify it, then clean up.
        pd.read_csv(file_path)
        os.remove(file_path)

    # At parse time a task call returns an XComArg reference, not the value itself, so the
    # downstream parameters below are deliberately left unannotated (the return annotations
    # still document what each step produces).
    rows = get_data_from_airline_collection()
    csv_path = transform_data_to_csv(rows)
    load_data_to_s3(csv_path)


couchbase_cluster_test()
