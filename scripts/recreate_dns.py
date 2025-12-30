#!/usr/bin/env python3
"""Recreate DNS record for affiliateprograms.wiki"""

import subprocess
import requests
import time

ZONE_ID = "799ff7f21bfb64d97055faf5b496fd97"

def get_secret(name):
    result = subprocess.run(
        ["/home/skynet/google-cloud-sdk/bin/gcloud", "secrets", "versions", "access",
         "latest", f"--secret={name}", "--project=superapp-466313"],
        capture_output=True, text=True, timeout=30
    )
    return result.stdout.strip()

def main():
    cf_token = get_secret("CLOUDFLARE_API_TOKEN_DNS")

    headers = {
        "Authorization": f"Bearer {cf_token}",
        "Content-Type": "application/json"
    }

    # Get current DNS records
    r = requests.get(
        f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records",
        headers=headers
    )
    records = r.json().get("result", [])

    # Find and delete the main CNAME record
    for rec in records:
        if rec["name"] == "affiliateprograms.wiki" and rec["type"] == "CNAME":
            print(f"Deleting CNAME record {rec['id']}...")
            del_r = requests.delete(
                f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records/{rec['id']}",
                headers=headers
            )
            result = del_r.json()
            if result.get("success"):
                print("✓ Deleted")
            else:
                print(f"Error: {result.get('errors')}")
            break

    time.sleep(2)

    # Create new CNAME record
    print("Creating new CNAME record...")
    create_r = requests.post(
        f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records",
        headers=headers,
        json={
            "type": "CNAME",
            "name": "@",
            "content": "affiliateprograms-wiki.pages.dev",
            "proxied": True,
            "ttl": 1
        }
    )
    result = create_r.json()
    if result.get("success"):
        print("✓ Created new CNAME record")
    else:
        print(f"Error: {result.get('errors')}")

if __name__ == "__main__":
    main()
