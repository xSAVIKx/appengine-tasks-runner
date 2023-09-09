#!/usr/bin/env bash

##################################################################################################
# This script performs setup of the AppEngine Tasks Runner-related
# services and environments.
##################################################################################################

GCP_PROJECT="${GOOGLE_CLOUD_PROJECT}"
APPENGINE_GCP_REGION="${APPENGINE_GCP_REGION:-us-central}"
TASKS_GCP_REGION="${TASKS_GCP_REGION:-us-central1}"


echo "Running script for project ${GCP_PROJECT} and AppEngine region ${APPENGINE_GCP_REGION} and Cloud Tasks region ${TASKS_GCP_REGION}"

echo "Enabling required GCP services"
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
echo "Creating AppEngine application"
gcloud app create \
  --region="${APPENGINE_GCP_REGION}" \
  --project="${GCP_PROJECT}"


# Create and configure a service account used to perform authorized HTTP calls.
SERVICE_CALLER_SA="service-caller"

echo "Creating ${SERVICE_CALLER_SA} service account"
gcloud iam service-accounts create "${SERVICE_CALLER_SA}" \
  --display-name="Service Caller" \
  --description="Performs authorized service and API HTTP calls." \
  --project="${GCP_PROJECT}"

SERVICE_CALLER_SA_EMAIL="${SERVICE_CALLER_SA}@${GCP_PROJECT}.iam.gserviceaccount.com"

echo "Creating IAM permissions to ${SERVICE_CALLER_SA} service account"
gcloud projects add-iam-policy-binding ${GCP_PROJECT} \
  --member="serviceAccount:${SERVICE_CALLER_SA_EMAIL}" \
  --role="roles/cloudfunctions.invoker" \
  --condition=None
gcloud projects add-iam-policy-binding ${GCP_PROJECT} \
  --member="serviceAccount:${SERVICE_CALLER_SA_EMAIL}" \
  --role="roles/run.invoker" \
  --condition=None

# Create a service account JSON key

echo "Exporting ${SERVICE_CALLER_SA} service account key"
gcloud iam service-accounts keys create "service-caller.key.json" \
  --iam-account="${SERVICE_CALLER_SA_EMAIL}" \
  --project="${GCP_PROJECT}"

# Store the key in a Secret Manager secret

echo "Creating secret with the SA key"
gcloud secrets create "service-caller-sa-key" \
  --data-file="service-caller.key.json" \
  --labels="service=appengine-tasks-runner" \
  --project="${GCP_PROJECT}"


echo "Creating scheduled tasks queue"
gcloud tasks queues create "scheduled-tasks" \
  --location="${TASKS_GCP_REGION}" \
  --max-attempts=3 \
  --max-backoff="10s" \
  --max-dispatches-per-second=1 \
  --max-concurrent-dispatches=500 \
  --routing-override="service:tasks-runner" \
  --project="${GCP_PROJECT}"

echo "Setup complete"
