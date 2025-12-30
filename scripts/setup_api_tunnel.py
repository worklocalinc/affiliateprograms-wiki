#!/usr/bin/env python3
"""Set up API tunnel DNS record"""

import subprocess
import requests

ZONE_ID = "799ff7f21bfb64d97055faf5b496fd97"
TUNNEL_ID = "c9691ae8-478b-457d-bc5e-75997e9275de"

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

    # Create CNAME record for api.affiliateprograms.wiki pointing to tunnel
    print("Creating DNS record for api.affiliateprograms.wiki...")

    r = requests.post(
        f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records",
        headers=headers,
        json={
            "type": "CNAME",
            "name": "api",
            "content": f"{TUNNEL_ID}.cfargotunnel.com",
            "proxied": True
        }
    )

    result = r.json()
    if result.get("success"):
        print("✓ Created api.affiliateprograms.wiki -> tunnel")
    else:
        print(f"Error: {result.get('errors')}")
        # If already exists, try to update
        if "already exist" in str(result.get("errors", [])):
            print("Record may already exist")

if __name__ == "__main__":
    main()
