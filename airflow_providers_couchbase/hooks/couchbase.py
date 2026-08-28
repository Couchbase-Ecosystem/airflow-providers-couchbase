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
"""Hook for Couchbase."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any, TypedDict

from couchbase.auth import Authenticator, CertificateAuthenticator, PasswordAuthenticator
from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions, Compression, IpProtocol, KnownConfigProfiles, TLSVerifyMode

from airflow.sdk import BaseHook

if TYPE_CHECKING:
    from types import TracebackType
    from typing import Self

    from couchbase.bucket import Bucket
    from couchbase.collection import Collection
    from couchbase.scope import Scope


class Config(TypedDict, total=False):
    """
    Cluster level options forwarded to :class:`~couchbase.options.ClusterOptions`.

    Every key is optional; omitted keys fall back to the Couchbase SDK defaults. See
    https://docs.couchbase.com/python-sdk/current/ref/client-settings.html for the full reference.

    ``profile`` is not a :class:`~couchbase.options.ClusterOptions` argument: it is applied
    separately via :meth:`~couchbase.options.ClusterOptions.apply_profile`.
    """

    profile: KnownConfigProfiles | str

    # Timeout options.
    bootstrap_timeout: timedelta
    resolve_timeout: timedelta
    connect_timeout: timedelta
    kv_timeout: timedelta
    kv_durable_timeout: timedelta
    views_timeout: timedelta
    query_timeout: timedelta
    analytics_timeout: timedelta
    search_timeout: timedelta
    management_timeout: timedelta
    dns_srv_timeout: timedelta
    idle_http_connection_timeout: timedelta
    config_idle_redial_timeout: timedelta
    config_total_timeout: timedelta

    # Tracing options.
    tracing_threshold_kv: timedelta
    tracing_threshold_view: timedelta
    tracing_threshold_query: timedelta
    tracing_threshold_search: timedelta
    tracing_threshold_analytics: timedelta
    tracing_threshold_eventing: timedelta
    tracing_threshold_management: timedelta
    tracing_threshold_queue_size: int
    tracing_threshold_queue_flush_interval: timedelta
    tracing_orphaned_queue_size: int
    tracing_orphaned_queue_flush_interval: timedelta

    # General options.
    enable_tls: bool
    enable_mutation_tokens: bool
    enable_tcp_keep_alive: bool
    ip_protocol: IpProtocol | str
    enable_dns_srv: bool
    show_queries: bool
    enable_unordered_execution: bool
    enable_clustermap_notification: bool
    enable_compression: bool
    enable_tracing: bool
    enable_metrics: bool
    network: str
    tls_verify: TLSVerifyMode | str
    tcp_keep_alive_interval: timedelta
    config_poll_interval: timedelta
    config_poll_floor: timedelta
    max_http_connections: int
    user_agent_extra: str
    logging_meter_emit_interval: timedelta
    log_redaction: bool
    compression: Compression
    compression_min_size: int
    compression_min_ratio: float
    dns_nameserver: str
    dns_port: int
    disable_mozilla_ca_certificates: bool
    dump_configuration: bool


class CouchbaseHook(BaseHook):
    """
    Interact with a Couchbase cluster.

    Documentation on establishing a connection can be found here:
    https://docs.couchbase.com/python-sdk/current/hello-world/start-using-sdk.html

    The authenticator is chosen from the Airflow connection: when neither a username nor a
    password is set, certificate authentication is used, otherwise password authentication is.
    Certificate paths are read from the ``extra`` field of the connection:

    ```json
    {
        "cert_path": "/path/to/custom/ca-cert",
        "key_path": "/path/to/key-file",
        "trust_store_path": "/path/to/cert-file"
    }
    ```

    - `cert_path`: This is a common field used for both password and certificate-based authenticators.
    - In the case of **password authentication**, only the `cert_path` field is considered.
    - For **certificate authentication**, you must specify `cert_path`, `key_path`, and `trust_store_path`.

    Make sure to provide valid paths according to your environment.

    :param couchbase_conn_id: ID of the Airflow connection holding the cluster credentials.
    :param config: Optional cluster level options, see :class:`Config`.
    """

    conn_name_attr = "couchbase_conn_id"
    default_conn_name = "couchbase_default"
    conn_type = "couchbase"
    hook_name = "Couchbase"

    def __init__(self, couchbase_conn_id: str = default_conn_name, config: Config | None = None) -> None:
        super().__init__()
        self.couchbase_conn_id = couchbase_conn_id
        self.cluster_config: Config = config if config is not None else Config()
        self.cluster: Cluster | None = None

    def test_connection(self) -> tuple[bool, str]:
        """Test the Couchbase connectivity from UI."""
        try:
            self.get_conn()
        except Exception as exc:
            # Any failure is reported back to the UI rather than raised.
            return False, str(exc)
        else:
            return True, "Connection successfully tested"
        finally:
            self.close()

    def get_conn(self) -> Cluster:
        """Fetch the Couchbase cluster, connecting on first use and reusing it afterwards."""
        if self.cluster is None:
            connection = self.get_connection(self.couchbase_conn_id)
            if not connection.host:
                msg = f"Connection {self.couchbase_conn_id!r} has no host set, expected a Couchbase connection string."
                raise ValueError(msg)
            authenticator = self._build_authenticator(
                login=connection.login,
                password=connection.password,
                extra=connection.extra_dejson,
            )
            # `Cluster.__init__` annotates `*options` with the SDK's own deprecated
            # `couchbase.cluster.ClusterOptions` shim instead of the `couchbase.options` class it
            # documents (and which alone carries `apply_profile`), so checkers see a false mismatch.
            options = self._build_cluster_options(authenticator)
            self.cluster = Cluster(connection.host, options)  # pyright: ignore[reportArgumentType]
        return self.cluster

    def get_bucket(self, bucket: str) -> Bucket:
        """
        Fetch a couchbase bucket object.

        :param bucket: Name of the bucket.
        """
        return self.get_conn().bucket(bucket)

    def get_scope(self, bucket: str, scope: str) -> Scope:
        """
        Fetch a couchbase scope object for querying.

        :param bucket: Name of the bucket holding the scope.
        :param scope: Name of the scope.
        """
        return self.get_bucket(bucket).scope(scope)

    def get_collection(self, bucket: str, scope: str, collection: str) -> Collection:
        """
        Fetch a couchbase collection object for querying.

        :param bucket: Name of the bucket holding the scope.
        :param scope: Name of the scope holding the collection.
        :param collection: Name of the collection.
        """
        return self.get_scope(bucket, scope).collection(collection)

    def close(self) -> None:
        """Close the Couchbase cluster if one is open, so it can be reopened by :meth:`get_conn`."""
        if self.cluster is not None:
            self.cluster.close()
            self.cluster = None

    def __enter__(self) -> Self:
        """Return the object when a context manager is created."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Close couchbase cluster when exiting the context manager."""
        self.close()

    def _build_cluster_options(self, authenticator: Authenticator) -> ClusterOptions:
        """Turn :attr:`cluster_config` into :class:`~couchbase.options.ClusterOptions`."""
        config: dict[str, Any] = dict(self.cluster_config)
        profile = config.pop("profile", None)
        options = ClusterOptions(authenticator=authenticator, **config)
        if profile is not None:
            options.apply_profile(profile)
        return options

    @staticmethod
    def _build_authenticator(login: str | None, password: str | None, extra: dict[str, Any]) -> Authenticator:
        """Build the authenticator matching the credentials found on the Airflow connection."""
        cert_path = extra.get("cert_path")
        if login or password:
            if not (login and password):
                msg = "Password authentication requires both a username and a password on the connection."
                raise ValueError(msg)
            return PasswordAuthenticator(login, password, cert_path)

        key_path = extra.get("key_path")
        trust_store_path = extra.get("trust_store_path")
        if not (cert_path and key_path and trust_store_path):
            msg = (
                "Certificate authentication requires 'cert_path', 'key_path' and 'trust_store_path' "
                "in the connection extra, or a username/password for password authentication."
            )
            raise ValueError(msg)
        return CertificateAuthenticator(cert_path, key_path, trust_store_path)
