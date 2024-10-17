import os
import tempfile
from datetime import timedelta

import pandas as pd
from couchbase.options import KnownConfigProfiles

from airflow.decorators import dag, task
from airflow.utils.dates import days_ago
from airflow_providers_couchbase.hooks import Config, CouchbaseHook

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
    schedule_interval=None,
    start_date=days_ago(1),
    tags=[],
    catchup=False,
    max_active_runs=1,
)
def couchbase_cluster_test():

    @task()
    def get_data_from_airline_collection():
        hook = CouchbaseHook(
            couchbase_conn_id="couchbase_conn_id",
            config=Config(profile=KnownConfigProfiles.WanDevelopment),
        )

        scope = hook.get_scope(bucket="travel-sample", scope="inventory")
        collection = hook.get_collection(bucket="travel-sample", scope="inventory", collection="airline")
        result = scope.query("select meta().id from airline limit 10")
        ids = []
        for row in result:
            ids.append(row["id"])
        kv_response = collection.get_multi(ids)
        if not kv_response.all_ok and kv_response.exceptions:
            errors = []
            for id, ex in kv_response.exceptions.items():
                errors.append({"id": id, "exception": ex})
            if len(errors) > 0:
                msg = f"Failed to write documents to couchbase. Errors:\n{errors}"
                raise Exception(msg)
        documents = []
        for id in ids:
            get_result = kv_response.results.get(id)
            if get_result is not None and get_result.success:
                documents.append(get_result.value)
        return documents

    @task()
    def transform_data_to_csv(documents):
        # Transform data into a pandas DataFrame
        df = pd.DataFrame(documents)

        # Save the DataFrame as a CSV file in a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_file:
            df.to_csv(temp_file.name, index=False)
            return temp_file.name

    @task()
    def load_data_to_s3(file_path):
        pd.read_csv(file_path)
        os.remove(file_path)

    ids = get_data_from_airline_collection()
    file_path = transform_data_to_csv(ids)
    load_data_to_s3(file_path)


couchbase_cluster_test()