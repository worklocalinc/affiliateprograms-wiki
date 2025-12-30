#!/bin/bash
set -e

# Get DB URL
DB_URL=$(/home/skynet/google-cloud-sdk/bin/gcloud secrets versions access latest --secret=database_url_affiliate_wiki --project=superapp-466313)
export DATABASE_URL="$DB_URL"

# Activate venv
source /home/skynet/affiliateprograms-wiki/api/.venv/bin/activate

# Run server
cd /home/skynet/affiliateprograms-wiki/api
exec python server.py
