#!/usr/bin/env python3
"""Update DNS for affiliateprograms.wiki"""

import subprocess
import requests
import json

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

    # Find and update the main CNAME record to point to Cloudflare Pages
    for rec in records:
        if rec["name"] == "affiliateprograms.wiki" and rec["type"] == "CNAME":
            print(f"Updating CNAME from {rec['content']} to affiliateprograms-wiki.pages.dev")

            update_r = requests.patch(
                f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records/{rec['id']}",
                headers=headers,
                json={
                    "type": "CNAME",
                    "name": "affiliateprograms.wiki",
                    "content": "affiliateprograms-wiki.pages.dev",
                    "proxied": True
                }
            )
            result = update_r.json()
            if result.get("success"):
                print("✓ Updated successfully!")
            else:
                print(f"Error: {result.get('errors')}")
            break

    print("\nDone!")

if __name__ == "__main__":
    main()
