#!/usr/bin/env python3
"""Check Pages project domains"""

import subprocess
import requests

def get_secret(name):
    result = subprocess.run(
        ["/home/skynet/google-cloud-sdk/bin/gcloud", "secrets", "versions", "access",
         "latest", f"--secret={name}", "--project=superapp-466313"],
        capture_output=True, text=True, timeout=30
    )
    return result.stdout.strip()

def main():
    cf_token = get_secret("CLOUDFLARE_API_TOKEN_PAGES")
    account_id = get_secret("CLOUDFLARE_ACCOUNT_ID")

    headers = {
        "Authorization": f"Bearer {cf_token}",
        "Content-Type": "application/json"
    }

    # Get project info
    r = requests.get(
        f"https://api.cloudflare.com/client/v4/accounts/{account_id}/pages/projects/affiliateprograms-wiki",
        headers=headers
    )

    data = r.json()
    if data.get("success"):
        project = data.get("result", {})
        print(f"Project: {project.get('name')}")
        print(f"Subdomain: {project.get('subdomain')}")
        print(f"Domains: {project.get('domains', [])}")
        print(f"Latest deployment: {project.get('latest_deployment', {}).get('url')}")
    else:
        print(f"Error: {data.get('errors')}")

if __name__ == "__main__":
    main()
