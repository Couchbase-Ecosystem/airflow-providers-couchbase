FROM apache/airflow:2.10.2

COPY ./ /opt/airflow/airflow_providers_couchbase

RUN pip install /opt/airflow/airflow_providers_couchbase
RUN pip install pandas