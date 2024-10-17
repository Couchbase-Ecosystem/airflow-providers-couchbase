from datetime import datetime
import logging
import os
import re
import subprocess
import time
import pytest

pytestmark = pytest.mark.integration_test

container_name = 'docker-airflow-worker-1'


@pytest.fixture(autouse=True)
def setup_before_test(request):
    print("=============================================")
    print("Executing ", request.node.name)
    print("=============================================")


def run_docker_exec(command):

    result = subprocess.run(['docker', 'exec', container_name] + command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    output = result.stdout.decode("utf-8")
    print(output)

    return result, output


def assert_airflow_dag_log_contains(string, output):
    assert string in output


def assert_airflow_dag_completed(result):
    assert result.returncode == 0


def assert_airflow_dag_failed(result):
    assert result.returncode == 1


def test_airflow_test_cb_cluster():

    command = 'airflow dags test airflow_test_couchbase_cluster'
    result, output = run_docker_exec(command)

    assert_airflow_dag_completed(result)


def test_airflow_test_cb_scope():

    command = 'airflow dags test airflow_test_couchbase_scope'
    result, output = run_docker_exec(command)

    assert_airflow_dag_completed(result)


if __name__ == '__main__':
    pytest.main()
