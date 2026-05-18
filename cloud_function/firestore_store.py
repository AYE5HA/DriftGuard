"""Firestore reads and writes for baseline schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import yaml
from google.cloud import firestore


def get_firestore_client() -> firestore.Client:
    return firestore.Client()


def register_baseline_from_yaml(
    config_path: str,
    collection_name: str = "driftguard_baselines",
) -> dict[str, Any]:
    """Load a YAML baseline config and store it in Firestore."""
    with open(config_path, "r", encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)

    dataset_name = config["dataset_name"]
    baseline_document = {
        "dataset_name": dataset_name,
        "file_path": config["file_path"],
        "expected_schema": config["expected_schema"],
        "similarity_threshold": config.get("similarity_threshold", 80),
        "updated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }

    client = get_firestore_client()
    client.collection(collection_name).document(dataset_name).set(baseline_document)
    return baseline_document


def fetch_baseline(
    dataset_name: str,
    collection_name: str = "driftguard_baselines",
) -> dict[str, Any]:
    """Fetch one registered baseline schema from Firestore."""
    client = get_firestore_client()
    snapshot = client.collection(collection_name).document(dataset_name).get()

    if not snapshot.exists:
        raise ValueError(f"No baseline schema found for dataset: {dataset_name}")

    return snapshot.to_dict()
