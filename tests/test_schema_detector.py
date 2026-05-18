import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "cloud_function"))

from schema_detector import compare_schemas, flatten_dict, infer_json_schema


def test_flatten_dict_uses_dot_notation():
    row = {"user": {"id": 123, "profile": {"name": "Ayesha"}}}

    assert flatten_dict(row) == {
        "user.id": 123,
        "user.profile.name": "Ayesha",
    }


def test_infer_json_schema_handles_nested_json():
    rows = [
        {
            "user_id": "u_1001",
            "purchase_amount": 49.99,
            "is_member": True,
            "timestamp": "2026-05-18T09:15:00Z",
            "user": {"email": "customer@example.com"},
        }
    ]

    schema = infer_json_schema(json.dumps(rows).encode("utf-8"))

    assert schema["user_id"] == "string"
    assert schema["purchase_amount"] == "float"
    assert schema["is_member"] == "boolean"
    assert schema["timestamp"] == "timestamp"
    assert schema["user.email"] == "string"


def test_compare_schemas_detects_core_anomalies():
    expected = {
        "user_id": "string",
        "event_type": "string",
        "purchase_amount": "float",
    }
    current = {
        "userid": "string",
        "event_type": "string",
        "purchase_amount": "string",
        "marketing_source": "string",
    }

    anomalies = compare_schemas(expected, current, "ecommerce_events", 80)
    anomaly_types = {anomaly["anomaly_type"] for anomaly in anomalies}

    assert "renamed_column" in anomaly_types
    assert "datatype_change" in anomaly_types
    assert "new_column" in anomaly_types
