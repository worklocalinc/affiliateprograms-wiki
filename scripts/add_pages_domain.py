#!/usr/bin/env python3
"""Add custom domain to Pages project"""

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

    # Add custom domain
    print("Adding affiliateprograms.wiki to Pages project...")
    r = requests.post(
        f"https://api.cloudflare.com/client/v4/accounts/{account_id}/pages/projects/affiliateprograms-wiki/domains",
        headers=headers,
        json={"name": "affiliateprograms.wiki"}
    )

    data = r.json()
    if data.get("success"):
        print("✓ Domain added successfully!")
        print(f"Result: {data.get('result')}")
    else:
        errors = data.get("errors", [])
        for e in errors:
            print(f"Error {e.get('code')}: {e.get('message')}")

if __name__ == "__main__":
    main()
