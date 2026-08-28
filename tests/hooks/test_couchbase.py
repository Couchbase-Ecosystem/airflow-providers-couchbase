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
from __future__ import annotations

from datetime import timedelta
from unittest import mock

import couchbase.auth
import couchbase.bucket
import couchbase.cluster
import couchbase.collection
import couchbase.scope
import pytest
from couchbase.options import ClusterOptions, KnownConfigProfiles

from airflow.sdk import Connection
from airflow_providers_couchbase import get_provider_info
from airflow_providers_couchbase.hooks import Config, CouchbaseHook

pytestmark = pytest.mark.unit_test

CONN_ID = "couchbase_default"
CERT_PATH = "/path/to/custom/ca-cert"
KEY_PATH = "/path/to/key-file"
TRUST_STORE_PATH = "/path/to/cert-file"

PASSWORD_CONNECTION = Connection(conn_id=CONN_ID, login="user", password="password", host="localhost")
PASSWORD_CONNECTION_WITH_CERT = Connection(
    conn_id=CONN_ID,
    login="user",
    password="password",
    host="remote_host",
    extra=f'{{"cert_path": "{CERT_PATH}"}}',
)
CERTIFICATE_CONNECTION = Connection(
    conn_id=CONN_ID,
    host="remote_host",
    extra=f'{{"cert_path": "{CERT_PATH}", "key_path": "{KEY_PATH}", "trust_store_path": "{TRUST_STORE_PATH}"}}',
)


def patch_connection(connection: Connection):
    """Patch ``CouchbaseHook.get_connection`` so no Airflow metadata database is needed."""
    return mock.patch(
        "airflow_providers_couchbase.hooks.couchbase.CouchbaseHook.get_connection",
        return_value=connection,
    )


def patch_cluster():
    """Patch the Couchbase ``Cluster`` so no cluster is contacted."""
    return mock.patch("airflow_providers_couchbase.hooks.couchbase.Cluster")


def password_options() -> ClusterOptions:
    return ClusterOptions(authenticator=couchbase.auth.PasswordAuthenticator(username="user", password="password"))


@pytest.fixture
def mock_cluster_class():
    with patch_cluster() as mock_cluster:
        yield mock_cluster


@pytest.fixture
def mock_cluster(mock_cluster_class):
    """Return the ``Cluster`` instance the hook will build, with bucket/scope/collection stubbed."""
    cluster = mock.Mock(spec=couchbase.cluster.Cluster)
    bucket = mock.Mock(spec=couchbase.bucket.Bucket)
    scope = mock.Mock(spec=couchbase.scope.Scope)
    collection = mock.Mock(spec=couchbase.collection.Collection)

    mock_cluster_class.return_value = cluster
    cluster.bucket.return_value = bucket
    bucket.scope.return_value = scope
    scope.collection.return_value = collection
    return cluster


class TestCouchbaseHookConnection:
    def test_defaults(self):
        hook = CouchbaseHook()
        assert hook.couchbase_conn_id == CouchbaseHook.default_conn_name
        assert hook.cluster is None
        assert hook.cluster_config == {}

    def test_config_is_not_shared_between_hooks(self):
        """A hook must never mutate the config of another hook (no shared mutable default)."""
        first, second = CouchbaseHook(), CouchbaseHook()
        first.cluster_config["query_timeout"] = timedelta(seconds=1)
        assert second.cluster_config == {}

    @patch_connection(PASSWORD_CONNECTION_WITH_CERT)
    def test_get_conn_is_cached(self, mock_get_connection, mock_cluster_class):
        hook = CouchbaseHook()
        assert hook.get_conn() is hook.get_conn(), "Connection initialized only if None."
        mock_cluster_class.assert_called_once()

    @patch_connection(PASSWORD_CONNECTION_WITH_CERT)
    def test_get_conn_with_password_auth_extra_config(self, mock_get_connection, mock_cluster_class):
        connection = mock_get_connection.return_value
        CouchbaseHook().get_conn()
        mock_cluster_class.assert_called_once_with(
            connection.host,
            ClusterOptions(
                authenticator=couchbase.auth.PasswordAuthenticator(
                    username=connection.login,
                    password=connection.password,
                    cert_path=CERT_PATH,
                )
            ),
        )

    @patch_connection(CERTIFICATE_CONNECTION)
    def test_get_conn_with_certificate_auth_extra_config(self, mock_get_connection, mock_cluster_class):
        connection = mock_get_connection.return_value
        CouchbaseHook().get_conn()
        mock_cluster_class.assert_called_once_with(
            connection.host,
            ClusterOptions(
                authenticator=couchbase.auth.CertificateAuthenticator(
                    cert_path=CERT_PATH,
                    key_path=KEY_PATH,
                    trust_store_path=TRUST_STORE_PATH,
                )
            ),
        )

    @patch_connection(Connection(conn_id=CONN_ID, host="remote_host", extra=f'{{"cert_path": "{CERT_PATH}"}}'))
    def test_get_conn_with_incomplete_certificate_config(self, mock_get_connection, mock_cluster_class):
        with pytest.raises(ValueError, match="Certificate authentication requires"):
            CouchbaseHook().get_conn()
        mock_cluster_class.assert_not_called()

    @patch_connection(Connection(conn_id=CONN_ID, login="user", host="remote_host"))
    def test_get_conn_with_username_but_no_password(self, mock_get_connection, mock_cluster_class):
        with pytest.raises(ValueError, match="Password authentication requires both"):
            CouchbaseHook().get_conn()
        mock_cluster_class.assert_not_called()

    @patch_connection(Connection(conn_id=CONN_ID, login="user", password="password"))
    def test_get_conn_without_host(self, mock_get_connection, mock_cluster_class):
        with pytest.raises(ValueError, match="has no host set"):
            CouchbaseHook().get_conn()
        mock_cluster_class.assert_not_called()

    @patch_connection(PASSWORD_CONNECTION)
    def test_get_conn_password_stays_default(self, mock_get_connection, mock_cluster_class):
        hook = CouchbaseHook()
        hook.get_conn()
        assert hook.cluster is not None
        mock_cluster_class.assert_called_once_with("localhost", password_options())

    @patch_connection(PASSWORD_CONNECTION)
    def test_get_conn_applies_config_profile(self, mock_get_connection, mock_cluster_class):
        hook = CouchbaseHook(config=Config(profile=KnownConfigProfiles.WanDevelopment))
        hook.get_conn()

        expected_options = password_options()
        expected_options.apply_profile(KnownConfigProfiles.WanDevelopment)
        mock_cluster_class.assert_called_once_with("localhost", expected_options)
        assert hook.cluster_config == {"profile": KnownConfigProfiles.WanDevelopment}, "config must not be consumed"

    @patch_connection(PASSWORD_CONNECTION)
    def test_get_conn_forwards_cluster_options(self, mock_get_connection, mock_cluster_class):
        hook = CouchbaseHook(config=Config(enable_tls=True))
        hook.get_conn()
        mock_cluster_class.assert_called_once_with(
            "localhost",
            ClusterOptions(
                authenticator=couchbase.auth.PasswordAuthenticator(username="user", password="password"),
                enable_tls=True,
            ),
        )


class TestCouchbaseHookAccessors:
    @patch_connection(PASSWORD_CONNECTION)
    def test_get_bucket(self, mock_get_connection, mock_cluster):
        bucket = CouchbaseHook().get_bucket("bucket")
        mock_cluster.bucket.assert_called_once_with("bucket")
        assert bucket is mock_cluster.bucket.return_value

    @patch_connection(PASSWORD_CONNECTION)
    def test_get_scope(self, mock_get_connection, mock_cluster):
        scope = CouchbaseHook().get_scope(bucket="bucket", scope="scope")
        mock_cluster.bucket.assert_called_once_with("bucket")
        mock_cluster.bucket.return_value.scope.assert_called_once_with("scope")
        assert isinstance(scope, couchbase.scope.Scope), "scope is not of type Scope"

    @patch_connection(PASSWORD_CONNECTION)
    def test_get_collection(self, mock_get_connection, mock_cluster):
        collection = CouchbaseHook().get_collection(bucket="bucket", scope="scope", collection="collection")
        scope = mock_cluster.bucket.return_value.scope.return_value
        mock_cluster.bucket.assert_called_once_with("bucket")
        mock_cluster.bucket.return_value.scope.assert_called_once_with("scope")
        scope.collection.assert_called_once_with("collection")
        assert isinstance(collection, couchbase.collection.Collection), "collection is not of type Collection"


class TestCouchbaseHookLifecycle:
    @patch_connection(PASSWORD_CONNECTION)
    def test_close_releases_the_cluster(self, mock_get_connection, mock_cluster):
        hook = CouchbaseHook()
        hook.get_conn()
        hook.close()
        mock_cluster.close.assert_called_once_with()
        assert hook.cluster is None

    def test_close_without_connection_is_a_no_op(self):
        CouchbaseHook().close()

    @patch_connection(PASSWORD_CONNECTION)
    def test_context_manager_closes_the_cluster(self, mock_get_connection, mock_cluster):
        with CouchbaseHook() as hook:
            assert hook.get_conn() is mock_cluster
        mock_cluster.close.assert_called_once_with()
        assert hook.cluster is None

    @patch_connection(PASSWORD_CONNECTION)
    def test_test_connection_success(self, mock_get_connection, mock_cluster):
        hook = CouchbaseHook()
        assert hook.test_connection() == (True, "Connection successfully tested")
        mock_cluster.close.assert_called_once_with()
        assert hook.cluster is None, "the probe connection must not be leaked"

    def test_test_connection_failure(self):
        hook = CouchbaseHook()
        with mock.patch.object(CouchbaseHook, "get_connection", side_effect=ValueError("boom")):
            assert hook.test_connection() == (False, "boom")


def test_connection_form_is_declared_in_provider_info():
    """
    Airflow 3.2 deprecated `Hook.get_ui_field_behaviour()`, so the connection form must be
    described declaratively (kebab-case) in `get_provider_info()` and the hook must not define
    the method - its mere presence on the class triggers AirflowProviderDeprecationWarning.
    """
    assert "get_ui_field_behaviour" not in CouchbaseHook.__dict__

    (conn_type,) = get_provider_info()["connection-types"]
    assert conn_type["connection-type"] == CouchbaseHook.conn_type
    assert conn_type["hook-name"] == CouchbaseHook.hook_name
    assert conn_type["hook-class-name"].endswith("CouchbaseHook")

    behaviour = conn_type["ui-field-behaviour"]
    assert behaviour["hidden-fields"] == ["schema", "port"]
    assert set(behaviour["relabeling"]) == {"host", "login"}
    assert set(behaviour["placeholders"]) == {"login", "password", "host", "extra"}
    assert "cert_path" in behaviour["placeholders"]["extra"]
