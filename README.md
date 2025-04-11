<h1 align="center">airflow-providers-couchbase</h1>

<p align="center">A custom <a href="https://airflow.apache.org/"><i>Apache Airflow</i></a> provider for <a href="https://www.couchbase.com"><i>Couchbase</i></a></p>

<p align="center">
  <a href="https://github.com/Couchbase-Ecosystem/airflow-providers-couchbase/actions?query=workflow%3Aci-integration-test">
    <img alt="ci" src="https://github.com/Couchbase-Ecosystem/airflow-providers-couchbase/actions/workflows/ci-integration-test.yml/badge.svg" />
  </a>
  <a href="https://pypi.org/project/airflow-providers-couchbase/">
    <img alt="pypi version" src="https://img.shields.io/pypi/v/airflow-providers-couchbase.svg" />
  </a>
  <a href="https://pypi.org/project/apache-airflow/">
    <img alt="airflow version" src="https://img.shields.io/pypi/v/apache-airflow.svg?label=airflow" />
  </a>
</p>

---

# Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Running a DAG in Docker](#running-a-dag-example-inside-an-airflow-docker-container)
  - [Prerequisites](#prerequisites)
  - [Connecting to a Local Couchbase Server](#connecting-to-a-local-couchbase-server)
  - [Steps to Run the Example DAG](#steps-to-run-the-example-dag)
  - [Example DAGs Explanation](#example-dags-explanation)
  - [Clean Up](#clean-up)
- [Additional Resources](#additional-resources)
- [License](#license)

## Overview

The `airflow-providers-couchbase` enables interactions with Couchbase clusters within Apache Airflow workflows. It provides custom Couchbase Hook that allow users to seamlessly interact with Couchbase databases, execute queries, manage documents, and more.

For those new to Apache Airflow, a [DAG (Directed Acyclic Graph)](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html) represents a workflow as a collection of tasks with directional dependencies. Each task in our example DAGs performs specific operations with Couchbase, such as querying data or processing documents.

## Installation

```bash
pip install airflow-providers-couchbase
```

## Running a DAG Example Inside an Airflow Docker Container

### Prerequisites

- Docker and Docker Compose installed on your machine
- A running Couchbase cluster accessible from your Docker container
- The travel-sample bucket available in your Couchbase cluster

### Connecting to a Local Couchbase Server

If you're running Couchbase Server locally (either installed natively or in Docker), you'll need to make some adjustments to connect from the Airflow containers:

1. **For locally installed Couchbase Server**:
   - Update the Couchbase connection host to use your machine's IP address instead of `localhost`
   - Example: `couchbase://192.168.1.100` (replace with your actual IP)

2. **For Couchbase Server running in Docker**:
   - Add Couchbase service to your docker-compose.yaml:

   ```yaml
   services:
     couchbase:
       image: couchbase/server:latest
       ports:
         - "8091-8096:8091-8096"
         - "11210-11211:11210-11211"
       networks:
         - airflow-couchbase

     airflow-common:
       networks:
         - airflow-couchbase
         
   networks:
     airflow-couchbase:
       driver: bridge
   ```

   - Update the Couchbase connection host to use the service name: `couchbase://couchbase`

Remember to initialize your Couchbase Server with:

- Create a bucket named "travel-sample"
- Import the travel-sample dataset
- Create a user with appropriate permissions

### Steps to Run the Example DAG

1. **Navigate to the Docker Directory**:

   ```bash
   cd docker
   ```

2. **Build and Run the Docker Containers**:

   ```bash
   # Initialize the Airflow database and create the first user account
   docker compose up airflow-init
   
   # Start all services defined in docker-compose.yml
   docker compose up --build
   ```

3. **Access the Airflow Web UI**:
   - Open your web browser: <http://localhost:8080>
   - Login credentials:
     - Username: `airflow`
     - Password: `airflow`

4. **Configure a Couchbase Connection**:
   - Go to Admin -> Connections
   - Click "+" to add a new connection
   - Fill in the details:
     - Connection Id: `couchbase_conn_id`
     - Connection Type: Couchbase
     - Host: `your_couchbase_host`
     - Login: Your Couchbase username
     - Password: Your Couchbase password
     - Extra: Additional configuration parameters (JSON format)

5. **Trigger the DAG**:
   - Go to DAGs view
   - Find "airflow_test_couchbase_cluster" DAG
   - Click "Play" to trigger a manual run

6. **Monitor the Execution**:
   - Click on the DAG run to view progress
   - View logs, duration, and status for each task
   - For a visual guide of this process, check our step-by-step tutorial on [docs/videos/airflow](docs/videos/airflow.mp4)

### Example DAGs Explanation

#### 1. airflow_test_couchbase_cluster.py

- Basic Couchbase interaction example
- Connects using CouchbaseHook
- Queries "airline" collection
- Extracts document IDs
- Converts data to CSV

#### 2. airflow_test_couchbase_scope.py

- Advanced example with direct scope/collection access
- Retrieves document IDs and full documents
- Includes error handling
- Processes complete documents

Both DAGs follow ETL pattern:

- **Extract**: 
  - Connect to Couchbase using CouchbaseHook
  - Query the "airline" collection in "travel-sample" bucket
  - Retrieve document IDs and data (airflow_test_couchbase_scope.py retrieves full documents, airflow_test_couchbase_cluster.py retrieves IDs only)

- **Transform**: 
  - Convert Couchbase query results to pandas DataFrame
  - Save DataFrame to a temporary CSV file using `tempfile.NamedTemporaryFile`

- **Load**: 
  - Read the temporary CSV file to verify data integrity
  - Clean up by removing the temporary file
  - (Placeholder: In production, you would upload to S3 or similar storage)

### Clean Up

```bash
docker-compose down -v
```

## Additional Resources

- [Apache Airflow Documentation](https://airflow.apache.org/docs/apache-airflow/stable/index.html)
- [Airflow Installation Guide](https://airflow.apache.org/docs/apache-airflow/stable/installation/index.html)

## License

`airflow-providers-couchbase` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.

---

# 📢 Support Policy

We truly appreciate your interest in this project!  
This project is **community-maintained**, which means it's **not officially supported** by our support team.

If you need help, have found a bug, or want to contribute improvements, the best place to do that is right here — by [opening a GitHub issue](https://github.com/Couchbase-Ecosystem/airflow-providers-couchbase/issues).  
Our support portal is unable to assist with requests related to this project, so we kindly ask that all inquiries stay within GitHub.

Your collaboration helps us all move forward together — thank you!
