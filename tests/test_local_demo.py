import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from local_demo import run_local_demo


def test_local_demo_writes_expected_artifacts(tmp_path):
    result = run_local_demo(
        config_path=PROJECT_ROOT / "config" / "sample_config.yaml",
        input_path=PROJECT_ROOT / "samples" / "events_drift.json",
        output_dir=tmp_path,
    )

    anomaly_types = {anomaly["anomaly_type"] for anomaly in result["anomalies"]}

    assert "renamed_column" in anomaly_types
    assert "datatype_change" in anomaly_types
    assert "new_column" in anomaly_types
    assert (tmp_path / "current_schema.json").exists()
    assert (tmp_path / "baseline_schema.json").exists()
    assert (tmp_path / "incidents.json").exists()
    assert (tmp_path / "slack_alert_preview.txt").exists()
