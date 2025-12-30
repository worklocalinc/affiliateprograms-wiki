#!/bin/bash
export CLOUDFLARE_API_TOKEN=$(cat /tmp/cf_pages_token.txt)
export CLOUDFLARE_ACCOUNT_ID=$(cat /tmp/cf_account_id.txt)
cd /home/skynet/affiliateprograms-wiki/web/affiliate-compass-ui
npx wrangler pages deploy dist --project-name=affiliateprograms-wiki
