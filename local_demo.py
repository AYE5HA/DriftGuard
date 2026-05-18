"""Run DriftGuard locally without Google Cloud billing.

This script mirrors the production flow:
1. load a baseline schema from YAML
2. read an incoming JSON or CSV sample file
3. infer the current schema
4. detect schema drift
5. write local incident logs
6. print a Slack-style alert
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "cloud_function"))

from notifier import summarize_anomalies
from schema_detector import compare_schemas, infer_schema_from_bytes


def run_local_demo(
    config_path: Path,
    input_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Run one local drift detection pass and save demo artifacts."""
    config = load_yaml(config_path)
    dataset_name = config["dataset_name"]
    expected_schema = config["expected_schema"]
    threshold = int(config.get("similarity_threshold", 80))

    content = input_path.read_bytes()
    current_schema = infer_schema_from_bytes(input_path.name, content)
    anomalies = compare_schemas(
        expected_schema=expected_schema,
        current_schema=current_schema,
        dataset_name=dataset_name,
        similarity_threshold=threshold,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "current_schema.json", current_schema)
    write_json(output_dir / "baseline_schema.json", expected_schema)
    write_json(output_dir / "incidents.json", anomalies)
    write_alert(output_dir / "slack_alert_preview.txt", dataset_name, anomalies)

    return {
        "dataset_name": dataset_name,
        "input_file": str(input_path),
        "current_schema": current_schema,
        "anomalies": anomalies,
        "output_dir": str(output_dir),
    }


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def write_json(path: Path, value: Any) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump(value, file, indent=2)
        file.write("\n")


def write_alert(path: Path, dataset_name: str, anomalies: list[dict[str, Any]]) -> None:
    if not anomalies:
        message = f"DriftGuard local demo: no drift detected for {dataset_name}."
    else:
        lines = [
            "DriftGuard local demo detected schema drift",
            f"Dataset: {dataset_name}",
            f"Summary: {summarize_anomalies(anomalies)}",
            "Detected changes:",
        ]
        for anomaly in anomalies:
            column_text = anomaly.get("old_column") or anomaly.get("new_column") or "unknown"
            if anomaly.get("old_column") and anomaly.get("new_column"):
                column_text = f"{anomaly['old_column']} -> {anomaly['new_column']}"
            lines.append(
                f"- [{anomaly['severity']}] {anomaly['anomaly_type']}: "
                f"{column_text} - {anomaly['details']}"
            )
        message = "\n".join(lines)

    with path.open("w", encoding="utf-8") as file:
        file.write(message + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run DriftGuard without GCP resources.")
    parser.add_argument(
        "--config",
        default="config/sample_config.yaml",
        help="Path to the baseline YAML config.",
    )
    parser.add_argument(
        "--input",
        default="samples/events_drift.json",
        help="Incoming JSON or CSV file to inspect.",
    )
    parser.add_argument(
        "--output-dir",
        default="demo_output",
        help="Directory for local incident and alert artifacts.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_local_demo(
        config_path=PROJECT_ROOT / args.config,
        input_path=PROJECT_ROOT / args.input,
        output_dir=PROJECT_ROOT / args.output_dir,
    )

    print("DriftGuard local demo complete")
    print(f"Dataset: {result['dataset_name']}")
    print(f"Input: {result['input_file']}")
    print(f"Anomalies: {len(result['anomalies'])}")
    print(f"Output folder: {result['output_dir']}")

    if result["anomalies"]:
        print("\nDetected changes:")
        for anomaly in result["anomalies"]:
            print(f"- [{anomaly['severity']}] {anomaly['anomaly_type']}: {anomaly['details']}")
    else:
        print("No drift detected.")


if __name__ == "__main__":
    main()
