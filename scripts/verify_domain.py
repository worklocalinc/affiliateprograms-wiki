#!/usr/bin/env python3
"""Add TXT verification record and activate domain"""

import subprocess
import requests

ZONE_ID = "799ff7f21bfb64d97055faf5b496fd97"
TXT_NAME = "_acme-challenge"
TXT_VALUE = "rEwNsCqfCz0Pt4_myuLdPrI9nFOFFHg47sfyXf-UZKw"

def get_secret(name):
    result = subprocess.run(
        ["/home/skynet/google-cloud-sdk/bin/gcloud", "secrets", "versions", "access",
         "latest", f"--secret={name}", "--project=superapp-466313"],
        capture_output=True, text=True, timeout=30
    )
    return result.stdout.strip()

def main():
    cf_token = get_secret("CLOUDFLARE_API_TOKEN")
    account_id = get_secret("CLOUDFLARE_ACCOUNT_ID")

    headers = {
        "Authorization": f"Bearer {cf_token}",
        "Content-Type": "application/json"
    }

    # Add TXT record for verification
    print(f"Adding TXT record: {TXT_NAME}.affiliateprograms.wiki = {TXT_VALUE}")

    r = requests.post(
        f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records",
        headers=headers,
        json={
            "type": "TXT",
            "name": TXT_NAME,
            "content": TXT_VALUE,
            "ttl": 1
        }
    )

    data = r.json()
    if data.get("success"):
        print("✓ TXT record added")
    else:
        print(f"TXT record: {data.get('errors')}")

    # Try to activate/re-add the domain
    print("\nAttempting to activate domain...")
    r = requests.patch(
        f"https://api.cloudflare.com/client/v4/accounts/{account_id}/pages/projects/affiliateprograms-wiki/domains/affiliateprograms.wiki",
        headers=headers,
        json={}
    )
    print(f"Activate response: {r.json()}")

if __name__ == "__main__":
    main()
