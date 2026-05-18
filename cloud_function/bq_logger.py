"""BigQuery incident logging for schema drift anomalies."""

from __future__ import annotations

from typing import Any

from google.cloud import bigquery


def log_anomalies(table_id: str | None, anomalies: list[dict[str, Any]]) -> None:
    """Insert anomaly rows into BigQuery when a table is configured."""
    if not anomalies:
        return
    if not table_id:
        print("BQ_TABLE_ID is not set. Skipping BigQuery logging.")
        return

    client = bigquery.Client()
    errors = client.insert_rows_json(table_id, anomalies)
    if errors:
        raise RuntimeError(f"BigQuery insert failed: {errors}")
