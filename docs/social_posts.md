# Social Sharing Templates

## LinkedIn Post

I built DriftGuard, a beginner-friendly data engineering project that detects schema drift in JSON and CSV files before downstream analytics pipelines break.

It can detect:

- missing columns
- newly added columns
- datatype changes
- likely renamed columns using fuzzy matching

The production architecture is designed for Google Cloud Platform using Cloud Functions, Cloud Storage, Firestore, BigQuery, Cloud Scheduler, and Slack alerts.

I also added a no-billing local demo so reviewers can run the full drift detection workflow without needing cloud credentials.

GitHub: https://github.com/AYE5HA/DriftGuard

This project helped me practice Python, ETL pipeline reliability, schema inference, cloud architecture, and writing clearer technical documentation.

## Short Version

I built DriftGuard, a GCP-ready schema drift monitoring project for ETL pipelines.

It detects missing columns, new columns, datatype changes, and likely renamed fields in JSON/CSV files before downstream analytics jobs break.

It also includes a no-billing local demo for easy review.

GitHub: https://github.com/AYE5HA/DriftGuard

## Reddit / Community Version

I’m a beginner building data engineering portfolio projects, and I made DriftGuard: a small schema drift detector for JSON/CSV ETL pipelines.

The idea is to catch upstream schema changes before they break dashboards or transformations. It includes schema inference, fuzzy rename detection, incident logging format, Slack-style alerts, tests, and a local demo that does not require GCP billing.

I’d appreciate feedback on the architecture, README, and what I should improve next.

Repo: https://github.com/AYE5HA/DriftGuard

