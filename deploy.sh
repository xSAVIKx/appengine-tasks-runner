#!/usr/bin/env bash

##################################################################################################
# This script deploys AppEngine Tasks Runner service.
##################################################################################################

GCP_PROJECT="${GCP_PROJECT}"

poetry export --no-interaction --without-hashes --format requirements.txt --output requirements.txt

echo "gunicorn" >> requirements.txt

gcloud app deploy app.yaml --project="${GCP_PROJECT}"
