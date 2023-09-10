#!/usr/bin/env bash

##################################################################################################
# This script deploys Cloud Run Job service.
##################################################################################################

GCP_PROJECT="${GOOGLE_CLOUD_PROJECT}"
GCP_REGION="${GCP_REGION:-us-central1}"

gcloud app deploy "job-service" \
  --allow-unauthenticated \
  --cpu-boost \
  --execution-environment="gen2" \
  --region="${GCP_REGION}" \
  --project="${GCP_PROJECT}"
