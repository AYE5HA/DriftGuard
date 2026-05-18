# GCP Deployment Notes

DriftGuard is designed for Google Cloud Platform, but some resources may require an active billing account even when usage is low.

## Required GCP Services

- Cloud Functions
- Cloud Scheduler
- Cloud Storage
- Firestore
- BigQuery

## Deployment Steps

Set your project:

```bash
gcloud config set project YOUR_PROJECT_ID
```

Enable APIs:

```bash
gcloud services enable cloudfunctions.googleapis.com cloudscheduler.googleapis.com storage.googleapis.com firestore.googleapis.com bigquery.googleapis.com
```

Create a storage bucket:

```bash
gcloud storage buckets create gs://YOUR_BUCKET_NAME --location=us-central1
gcloud storage cp samples/events_baseline.json gs://YOUR_BUCKET_NAME/events.json
```

Create BigQuery resources:

```bash
bq mk --dataset YOUR_PROJECT_ID:driftguard
bq mk --table YOUR_PROJECT_ID:driftguard.schema_incidents bigquery/schema.json
```

Deploy the function:

```bash
gcloud functions deploy driftguard \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=cloud_function \
  --entry-point=driftguard \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars=BASELINE_COLLECTION=driftguard_baselines,BQ_TABLE_ID=YOUR_PROJECT_ID.driftguard.schema_incidents,SLACK_WEBHOOK_URL=YOUR_SLACK_WEBHOOK_URL
```

Create a scheduler job:

```bash
gcloud scheduler jobs create http driftguard-ecommerce-events \
  --location=us-central1 \
  --schedule="*/5 * * * *" \
  --uri="FUNCTION_URL?dataset_name=ecommerce_events" \
  --http-method=GET
```

## Billing Note

Google Cloud may require billing to be enabled for Cloud Functions, Cloud Scheduler, and Cloud Storage. If billing is unavailable, use the local demo:

```bash
python local_demo.py
```

The local demo preserves the main engineering logic while avoiding cloud charges.

