FROM apache/airflow:2.10.2

COPY ./ /opt/airflow/airflow_provider_couchbase

RUN pip install /opt/airflow/airflow_provider_couchbase
RUN pip install pandas