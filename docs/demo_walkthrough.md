# Local Demo Walkthrough

This walkthrough shows DriftGuard running without Google Cloud billing.

## 1. Install Dependencies

```bash
pip install -r requirements.txt
```

## 2. Run the Demo

```bash
python local_demo.py
```

Expected output:

```text
DriftGuard local demo complete
Dataset: ecommerce_events
Anomalies: 3

Detected changes:
- [MEDIUM] renamed_column: Possible rename from user_id to userid with 100.0% similarity.
- [LOW] new_column: New column marketing_source was found in the incoming file.
- [HIGH] datatype_change: Column purchase_amount changed from float to string.
```

## 3. Inspect Generated Artifacts

The demo writes files into `demo_output/`.

```text
demo_output/
  baseline_schema.json
  current_schema.json
  incidents.json
  slack_alert_preview.txt
```

These files simulate the production outputs:

- `baseline_schema.json`: the expected schema loaded from YAML
- `current_schema.json`: the schema inferred from the incoming file
- `incidents.json`: BigQuery-style anomaly rows
- `slack_alert_preview.txt`: the Slack alert message preview

## 4. Try a No-Drift File

Run the demo against the clean CSV sample:

```bash
python local_demo.py --input samples/events.csv
```

This lets reviewers see both the healthy and drifted paths.

## 5. Why This Helps Reviewers

Some Google Cloud resources require billing to be enabled, even for free-tier usage. The local demo lets recruiters, mentors, and reviewers run the project immediately without cloud credentials.

