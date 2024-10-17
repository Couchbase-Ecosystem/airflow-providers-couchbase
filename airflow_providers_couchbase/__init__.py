from .__about__ import __version__


def get_provider_info():
    return {
        "package-name": "airflow-providers-couchbase",
        "name": "Apache Airflow Couchbase Provider",
        "description": "An Apache Airflow provider for Couchbase",
        "connection-types": [
            {
                "connection-type": "couchbase",
                "hook-class-name": "airflow_providers_couchbase.hooks.couchbase.CouchbaseHook",
            },
        ],
        "version": [__version__],
    }
