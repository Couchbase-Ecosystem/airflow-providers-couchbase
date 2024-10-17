# airflow-providers-couchbase

The `airflow-providers-couchbase` enables interactions with Couchbase clusters within Apache Airflow workflows. It provides custom Couchbase Hook that allow users to seamlessly interact with Couchbase databases, execute queries, manage documents, and more.

## Installation

To install the `airflow-providers-couchbase` package, run:

```bash
pip install airflow-providers-couchbase
```

## Running a DAG Example Inside an Airflow Docker Container

This section demonstrates how to run the example DAG inside an Airflow Docker container. A `docker` folder is provided in the repository, containing a `Dockerfile` and `docker-compose.yaml` file for setting up the Couchbase provider and running Airflow. Additionally, a sample DAG file `airflow_test_cb_cluster.py` is available in the `docker/dags` folder, which interacts with a Couchbase cluster.

### Prerequisites

- Docker and Docker Compose installed on your machine.
- A running Couchbase cluster accessible from your Docker container. If you don’t have one, download and install Couchbase Server from the official website.
- The travel-sample bucket should be available in your Couchbase cluster. If not, you can import it from Couchbase sample buckets.

## Steps to Run the Example DAG

1. Navigate to the Docker Directory:

    ```bash
    cd docker
    ```

2. Build and Run the Docker Containers:

    ```bash
    docker compose up airflow-init
    docker-compose up --build
    ```

3. Access the Airflow Web UI:
    Open your web browser and navigate to <http://localhost:8080> to access the Airflow web UI.
4. Configure a Couchbase Connection:
    Navigate to Airflow Connections and configure the Couchbase connection with the following details:
    - Connection Id: couchbase_default
    - Connection Type: Couchbase
    - Connection: couchbase://your_couchbase_host
    - Username: Your Couchbase username
    - Password: Your Couchbase password
5. Trigger the DAG:
    Trigger the couchbase_cluster_test DAG from the Airflow UI and inspect the logs.
6. Inspect the Logs:
    Click on each task and check the logs to verify the execution of Couchbase queries.

## Clean Up

To stop and remove the Docker containers and volumes, run:

```bash
docker-compose down -v
```

## Additional Resources

- Airflow Installation Guide
- Apache Airflow Documentation
