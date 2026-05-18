"""Slack alerting for detected schema drift."""

from __future__ import annotations

from typing import Any

from slack_sdk.webhook import WebhookClient


def send_slack_alert(webhook_url: str | None, dataset_name: str, anomalies: list[dict[str, Any]]) -> None:
    """Send a compact Slack alert when anomalies are present."""
    if not anomalies:
        return
    if not webhook_url:
        print("SLACK_WEBHOOK_URL is not set. Skipping Slack alert.")
        return

    summary = summarize_anomalies(anomalies)
    lines = [
        ":warning: DriftGuard detected schema drift",
        f"*Dataset:* `{dataset_name}`",
        f"*Summary:* {summary}",
        "*Detected changes:*",
    ]
    for anomaly in anomalies:
        column_text = anomaly.get("old_column") or anomaly.get("new_column") or "unknown"
        if anomaly.get("old_column") and anomaly.get("new_column"):
            column_text = f"{anomaly['old_column']} -> {anomaly['new_column']}"
        lines.append(
            f"- [{anomaly['severity']}] {anomaly['anomaly_type']}: "
            f"`{column_text}` - {anomaly['details']}"
        )

    client = WebhookClient(webhook_url)
    response = client.send(text="\n".join(lines))
    if response.status_code >= 400:
        raise RuntimeError(f"Slack webhook failed: {response.status_code} {response.body}")


def summarize_anomalies(anomalies: list[dict[str, Any]]) -> str:
    counts: dict[str, int] = {}
    for anomaly in anomalies:
        counts[anomaly["anomaly_type"]] = counts.get(anomaly["anomaly_type"], 0) + 1

    return ", ".join(
        f"{count} {anomaly_type.replace('_', ' ')}"
        for anomaly_type, count in sorted(counts.items())
    )
