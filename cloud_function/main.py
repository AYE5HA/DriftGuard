"""Google Cloud Function entry point for DriftGuard."""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlparse

import functions_framework
from google.cloud import storage

from bq_logger import log_anomalies
from firestore_store import fetch_baseline, register_baseline_from_yaml
from notifier import send_slack_alert
from schema_detector import compare_schemas, infer_schema_from_bytes


BASELINE_COLLECTION = os.getenv("BASELINE_COLLECTION", "driftguard_baselines")
BQ_TABLE_ID = os.getenv("BQ_TABLE_ID")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")


@functions_framework.http
def driftguard(request):
    """HTTP Cloud Function used by Cloud Scheduler."""
    request_json = request.get_json(silent=True) or {}
    action = request_json.get("action", request.args.get("action", "detect"))

    if action == "register":
        config_path = request_json.get("config_path") or request.args.get("config_path")
        if not config_path:
            return {"error": "config_path is required for registration."}, 400
        baseline = register_baseline_from_yaml(config_path, BASELINE_COLLECTION)
        return {"message": "Baseline registered.", "baseline": baseline}, 200

    dataset_name = request_json.get("dataset_name") or request.args.get("dataset_name")
    if not dataset_name:
        return {"error": "dataset_name is required."}, 400

    result = run_detection(dataset_name)
    status_code = 200 if not result["anomalies"] else 207
    return result, status_code


def run_detection(dataset_name: str) -> dict[str, Any]:
    """Run one schema drift detection pass for a dataset."""
    baseline = fetch_baseline(dataset_name, BASELINE_COLLECTION)
    file_path = baseline["file_path"]
    expected_schema = baseline["expected_schema"]
    threshold = int(os.getenv("SIMILARITY_THRESHOLD", baseline.get("similarity_threshold", 80)))

    file_name, file_content = download_gcs_file(file_path)
    current_schema = infer_schema_from_bytes(file_name, file_content)
    anomalies = compare_schemas(
        expected_schema=expected_schema,
        current_schema=current_schema,
        dataset_name=dataset_name,
        similarity_threshold=threshold,
    )

    log_anomalies(BQ_TABLE_ID, anomalies)
    send_slack_alert(SLACK_WEBHOOK_URL, dataset_name, anomalies)

    return {
        "dataset_name": dataset_name,
        "file_path": file_path,
        "current_schema": current_schema,
        "anomalies": anomalies,
        "message": "No drift detected." if not anomalies else "Schema drift detected.",
    }


def download_gcs_file(gcs_uri: str) -> tuple[str, bytes]:
    """Download a file from a gs:// URI."""
    parsed = urlparse(gcs_uri)
    if parsed.scheme != "gs" or not parsed.netloc or not parsed.path:
        raise ValueError(f"Invalid GCS URI: {gcs_uri}")

    bucket_name = parsed.netloc
    blob_name = parsed.path.lstrip("/")

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    return blob_name, blob.download_as_bytes()


if __name__ == "__main__":
    config_path = os.getenv("CONFIG_PATH", "../config/sample_config.yaml")
    print(register_baseline_from_yaml(config_path, BASELINE_COLLECTION))
