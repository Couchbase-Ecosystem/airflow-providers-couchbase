#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
"""End-to-end tests running the example DAGs inside the docker-compose Airflow worker."""

from __future__ import annotations

import shutil
import subprocess

import pytest

pytestmark = pytest.mark.integration_test

WORKER_CONTAINER = "docker-airflow-worker-1"
DAG_IDS = ["airflow_test_couchbase_cluster", "airflow_test_couchbase_scope"]


def run_in_worker(*command: str) -> subprocess.CompletedProcess[str]:
    """Run a command inside the Airflow worker container and return its completed process."""
    docker = shutil.which("docker")
    if docker is None:
        pytest.skip("docker is not available on this machine")

    result = subprocess.run(  # noqa: S603 - fixed command, no shell, test-only helper.
        [docker, "exec", WORKER_CONTAINER, *command],
        capture_output=True,
        text=True,
        check=False,
    )
    print(result.stdout)  # noqa: T201 - surfaced by pytest when the assertion below fails.
    print(result.stderr)  # noqa: T201
    return result


@pytest.mark.parametrize("dag_id", DAG_IDS)
def test_example_dag_runs(dag_id: str):
    result = run_in_worker("airflow", "dags", "test", dag_id)
    assert result.returncode == 0, f"DAG {dag_id} failed:\n{result.stdout}\n{result.stderr}"
