"""Schema inference and drift comparison helpers for DriftGuard."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime
from typing import Any

import pandas as pd

from semantic_matcher import find_likely_renames


SUPPORTED_TYPES = {"string", "integer", "float", "boolean", "timestamp", "null"}


def infer_schema_from_bytes(file_name: str, content: bytes, sample_size: int = 100) -> dict[str, str]:
    """Infer a simple schema from JSON or CSV file bytes."""
    lowered_name = file_name.lower()

    if lowered_name.endswith(".json"):
        return infer_json_schema(content, sample_size)
    if lowered_name.endswith(".csv"):
        return infer_csv_schema(content, sample_size)

    raise ValueError("Only .json and .csv files are supported in version 1.")


def infer_json_schema(content: bytes, sample_size: int = 100) -> dict[str, str]:
    """Infer primitive field types from a JSON array, JSON object, or JSONL file."""
    text = content.decode("utf-8")
    rows = _load_json_rows(text)[:sample_size]

    field_values: dict[str, list[Any]] = {}
    for row in rows:
        flattened = flatten_dict(row)
        for key, value in flattened.items():
            field_values.setdefault(key, []).append(value)

    return {
        field: infer_column_type(values)
        for field, values in sorted(field_values.items())
    }


def infer_csv_schema(content: bytes, sample_size: int = 100) -> dict[str, str]:
    """Infer primitive field types from the first rows of a CSV file."""
    text = content.decode("utf-8-sig")
    dataframe = pd.read_csv(io.StringIO(text), nrows=sample_size)

    return {
        column: infer_column_type(dataframe[column].dropna().tolist())
        for column in dataframe.columns
    }


def compare_schemas(
    expected_schema: dict[str, str],
    current_schema: dict[str, str],
    dataset_name: str,
    similarity_threshold: int = 80,
) -> list[dict[str, Any]]:
    """Compare expected and current schemas and return drift anomalies."""
    expected_columns = set(expected_schema)
    current_columns = set(current_schema)

    missing_columns = expected_columns - current_columns
    added_columns = current_columns - expected_columns
    shared_columns = expected_columns & current_columns

    anomalies: list[dict[str, Any]] = []

    rename_matches = find_likely_renames(
        missing_columns,
        added_columns,
        threshold=similarity_threshold,
    )

    renamed_old_columns = {match["old_column"] for match in rename_matches}
    renamed_new_columns = {match["new_column"] for match in rename_matches}

    for match in rename_matches:
        old_type = expected_schema.get(match["old_column"])
        new_type = current_schema.get(match["new_column"])
        detail = (
            f"Possible rename from {match['old_column']} to {match['new_column']} "
            f"with {match['score']:.1f}% similarity."
        )
        if old_type != new_type:
            detail += f" Type also changed from {old_type} to {new_type}."

        anomalies.append(
            build_anomaly(
                dataset_name=dataset_name,
                anomaly_type="renamed_column",
                severity="MEDIUM",
                details=detail,
                old_column=match["old_column"],
                new_column=match["new_column"],
            )
        )

    for column in sorted(missing_columns - renamed_old_columns):
        anomalies.append(
            build_anomaly(
                dataset_name=dataset_name,
                anomaly_type="missing_column",
                severity="HIGH",
                details=f"Expected column {column} is missing.",
                old_column=column,
            )
        )

    for column in sorted(added_columns - renamed_new_columns):
        anomalies.append(
            build_anomaly(
                dataset_name=dataset_name,
                anomaly_type="new_column",
                severity="LOW",
                details=f"New column {column} was found in the incoming file.",
                new_column=column,
            )
        )

    for column in sorted(shared_columns):
        expected_type = expected_schema[column]
        current_type = current_schema[column]
        if expected_type != current_type:
            anomalies.append(
                build_anomaly(
                    dataset_name=dataset_name,
                    anomaly_type="datatype_change",
                    severity="HIGH",
                    details=(
                        f"Column {column} changed from {expected_type} "
                        f"to {current_type}."
                    ),
                    old_column=column,
                    new_column=column,
                )
            )

    return anomalies


def flatten_dict(
    value: dict[str, Any],
    parent_key: str = "",
    separator: str = ".",
) -> dict[str, Any]:
    """Flatten nested dictionaries using dot notation."""
    flattened: dict[str, Any] = {}

    for key, item in value.items():
        full_key = f"{parent_key}{separator}{key}" if parent_key else str(key)
        if isinstance(item, dict):
            flattened.update(flatten_dict(item, full_key, separator))
        else:
            flattened[full_key] = item

    return flattened


def infer_column_type(values: list[Any]) -> str:
    """Infer one primitive type from sampled values."""
    non_empty_values = [
        value
        for value in values
        if value is not None and not (isinstance(value, str) and value.strip() == "")
    ]

    if not non_empty_values:
        return "null"

    inferred_types = {infer_value_type(value) for value in non_empty_values}

    if inferred_types == {"integer"}:
        return "integer"
    if inferred_types <= {"integer", "float"}:
        return "float" if "float" in inferred_types else "integer"
    if inferred_types == {"boolean"}:
        return "boolean"
    if inferred_types == {"timestamp"}:
        return "timestamp"

    return "string"


def infer_value_type(value: Any) -> str:
    """Infer the primitive type for one value."""
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        stripped = value.strip()
        if _is_boolean_string(stripped):
            return "boolean"
        if _is_integer_string(stripped):
            return "integer"
        if _is_float_string(stripped):
            return "float"
        if _is_timestamp_string(stripped):
            return "timestamp"
        return "string"

    return "string"


def build_anomaly(
    dataset_name: str,
    anomaly_type: str,
    severity: str,
    details: str,
    old_column: str | None = None,
    new_column: str | None = None,
) -> dict[str, Any]:
    """Create a BigQuery-friendly anomaly record."""
    return {
        "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "dataset_name": dataset_name,
        "anomaly_type": anomaly_type,
        "old_column": old_column,
        "new_column": new_column,
        "severity": severity,
        "details": details,
    }


def _load_json_rows(text: str) -> list[dict[str, Any]]:
    stripped = text.strip()
    if not stripped:
        return []

    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, list):
            return [row for row in parsed if isinstance(row, dict)]
        if isinstance(parsed, dict):
            return [parsed]
    except json.JSONDecodeError:
        pass

    rows: list[dict[str, Any]] = []
    for line in stripped.splitlines():
        if line.strip():
            parsed_line = json.loads(line)
            if isinstance(parsed_line, dict):
                rows.append(parsed_line)
    return rows


def _is_boolean_string(value: str) -> bool:
    return value.lower() in {"true", "false"}


def _is_integer_string(value: str) -> bool:
    if value.startswith(("-", "+")):
        value = value[1:]
    return value.isdigit()


def _is_float_string(value: str) -> bool:
    try:
        float(value)
    except ValueError:
        return False
    return "." in value or "e" in value.lower()


def _is_timestamp_string(value: str) -> bool:
    try:
        pd.to_datetime(value, errors="raise")
    except (ValueError, TypeError):
        return False
    return any(marker in value for marker in ("-", "/", "T", ":"))
