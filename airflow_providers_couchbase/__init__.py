from __future__ import annotations

import json
from typing import Any

from .__about__ import __version__

__all__ = ["__version__", "get_provider_info"]

# Placeholder shown for the connection's `extra` field in the UI. Kept in sync with the
# authentication options documented on CouchbaseHook.
_EXTRA_PLACEHOLDER = json.dumps(
    {
        "cert_path": "/path/to/custom/ca-cert",
        "key_path": "/path/to/key-file",
        "trust_store_path": "/path/to/cert-file",
    },
    indent=2,
)


def get_provider_info() -> dict[str, Any]:
    """
    Return the provider metadata discovered by the Airflow provider manager.

    The shape is validated against Airflow's ``provider_info.schema.json``. Airflow 3 reads the
    package version from the distribution metadata, so it is no longer part of this payload, and
    the connection form is described declaratively under ``ui-field-behaviour`` (kebab-case keys)
    rather than by a ``CouchbaseHook.get_ui_field_behaviour()`` method, which Airflow deprecated
    in 3.2.0 because it forces the hook to be imported just to render the form.
    """
    return {
        "package-name": "airflow-providers-couchbase",
        "name": "Apache Airflow Couchbase Provider",
        "description": "An Apache Airflow provider for Couchbase",
        "connection-types": [
            {
                "connection-type": "couchbase",
                "hook-class-name": "airflow_providers_couchbase.hooks.couchbase.CouchbaseHook",
                "hook-name": "Couchbase",
                "ui-field-behaviour": {
                    "hidden-fields": ["schema", "port"],
                    "relabeling": {
                        "host": "connection",
                        "login": "username",
                    },
                    "placeholders": {
                        "login": "Username to use for authentication",
                        "password": "Password to use for authentication",
                        "host": "Couchbase connection string",
                        "extra": _EXTRA_PLACEHOLDER,
                    },
                },
            },
        ],
    }
