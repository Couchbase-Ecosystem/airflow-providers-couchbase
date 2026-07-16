try:
    from importlib.metadata import version
    from reo_census import ReoEventLogger

    _pkg_version = version("airflow-providers-couchbase")
    _logger = ReoEventLogger(
        endpoint_url="https://telemetry.reo.dev/data",
        timeout=3.0,
        package_name="airflow-providers-couchbase",
        package_version=_pkg_version,
    )
    _logger.log_event()
except Exception:
    pass
