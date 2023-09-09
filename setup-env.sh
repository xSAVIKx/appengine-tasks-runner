#!/usr/bin/env bash

##################################################################################################
# This script performs setup of the AppEngine Tasks Runner-related
# services and environments.
##################################################################################################

GCP_PROJECT="${GOOGLE_CLOUD_PROJECT}"
GCP_REGION="${GCP_REGION:us-central}"


# Enable all required GCP services
gcloud services enable serviceusage.googleapis.com --project="${GCP_PROJECT}"
gcloud services enable servicemanagement.googleapis.com --project="${GCP_PROJECT}"
gcloud services enable secretmanager.googleapis.com --project="${GCP_PROJECT}"
gcloud services enable cloudapis.googleapis.com --project="${GCP_PROJECT}"
gcloud services enable cloudtasks.googleapis.com --project="${GCP_PROJECT}"
gcloud services enable storage-component.googleapis.com --project="${GCP_PROJECT}"
gcloud services enable monitoring.googleapis.com --project="${GCP_PROJECT}"
gcloud services enable cloudbuild.googleapis.com --project="${GCP_PROJECT}"
gcloud services enable logging.googleapis.com --project="${GCP_PROJECT}"
gcloud services enable appengine.googleapis.com --project="${GCP_PROJECT}"
gcloud services enable iamcredentials.googleapis.com --project="${GCP_PROJECT}"
gcloud services enable iam.googleapis.com --project="${GCP_PROJECT}"

# Create App Engine application
gcloud app create \
  --region="${GCP_REGION}" \
  --project="${GCP_PROJECT}"


# Create and configure a service account used to perform authorized HTTP calls.
SERVICE_CALLER_SA="service-caller"

gcloud iam service-accounts create "${SERVICE_CALLER_SA}" \
  --display-name="Service Caller" \
  --description="Performs authorized service and API HTTP calls." \
  --project="${GCP_PROJECT}"

SERVICE_CALLER_SA_EMAIL="${SERVICE_CALLER_SA}@${GCP_PROJECT}.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding ${GCP_PROJECT} \
  --member="serviceAccount:${SERVICE_CALLER_SA_EMAIL}" \
  --role="roles/cloudfunctions.invoker" \
  --condition=None
gcloud projects add-iam-policy-binding ${GCP_PROJECT} \
  --member="serviceAccount:${SERVICE_CALLER_SA_EMAIL}" \
  --role="roles/run.invoker" \
  --condition=None

# Create a service account JSON key
gcloud iam service-accounts keys create "service-caller.key.json" \
  --iam-account="${SERVICE_CALLER_SA_EMAIL}" \
  --project="${GCP_PROJECT}"

# Store the key in a Secret Manager secret
gcloud secrets create "service-caller-sa-key" \
  --data-file="service-caller.key.json" \
  --labels="service=appengine-tasks-runner" \
  --project="${GCP_PROJECT}"

gcloud tasks queues create "scheduled-tasks" \
  --location="${GCP_REGION}" \
  --max-attempts=3 \
  --max-backoff="10s" \
  --max-dispatches-per-second=1 \
  --max-concurrent-dispatches=500 \
  --routing-override="service:tasks-runner" \
  --project="${GCP_PROJECT}"
