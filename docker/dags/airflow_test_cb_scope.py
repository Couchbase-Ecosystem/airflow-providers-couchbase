"""Example DAG: use the scope and collection accessors of :class:`CouchbaseHook` directly."""

from __future__ import annotations

import os
import tempfile
from datetime import timedelta
from typing import Any

import pandas as pd
import pendulum
from couchbase.options import KnownConfigProfiles

from airflow.sdk import dag, task
from airflow.sdk.exceptions import AirflowException
from airflow_providers_couchbase.hooks import Config, CouchbaseHook

BUCKET = "travel-sample"
SCOPE = "inventory"
COLLECTION = "airline"
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
    "airflow_test_couchbase_scope",
    default_args=default_args,
    schedule=None,
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    tags=["couchbase", "example"],
    catchup=False,
    max_active_runs=1,
)
def couchbase_scope_test():
    @task()
    def get_data_from_airline_collection() -> list[Any]:
        hook = CouchbaseHook(
            couchbase_conn_id="couchbase_conn_id",
            config=Config(profile=KnownConfigProfiles.WanDevelopment),
        )

        with hook:
            scope = hook.get_scope(bucket=BUCKET, scope=SCOPE)
            collection = hook.get_collection(bucket=BUCKET, scope=SCOPE, collection=COLLECTION)

            doc_ids = [row["id"] for row in scope.query(QUERY)]
            kv_response = collection.get_multi(doc_ids)
            if not kv_response.all_ok and kv_response.exceptions:
                errors = [{"id": doc_id, "exception": exc} for doc_id, exc in kv_response.exceptions.items()]
                msg = f"Failed to read documents from couchbase. Errors:\n{errors}"
                raise AirflowException(msg)

            return [
                result.value
                for result in (kv_response.results.get(doc_id) for doc_id in doc_ids)
                if result is not None and result.success
            ]

    @task()
    def transform_data_to_csv(documents) -> str:
        # Transform data into a pandas DataFrame.
        df = pd.DataFrame(documents)

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
    documents = get_data_from_airline_collection()
    csv_path = transform_data_to_csv(documents)
    load_data_to_s3(csv_path)


couchbase_scope_test()
