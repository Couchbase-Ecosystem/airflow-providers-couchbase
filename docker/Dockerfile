FROM apache/airflow:3.3.1-python3.12

COPY ./ /opt/airflow/airflow_providers_couchbase

RUN pip install --no-cache-dir pandas /opt/airflow/airflow_providers_couchbase
