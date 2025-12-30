#!/usr/bin/env python3
"""Fix DNS proxy settings for affiliateprograms.wiki"""

import subprocess
import requests

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

    # Find the main CNAME record and check proxy settings
    for rec in records:
        if rec["name"] == "affiliateprograms.wiki" and rec["type"] == "CNAME":
            print(f"Current record:")
            print(f"  Content: {rec['content']}")
            print(f"  Proxied: {rec['proxied']}")
            print(f"  ID: {rec['id']}")

            # For Cloudflare Pages, the domain should be proxied
            # But let's verify the setup is correct
            if rec["content"] != "affiliateprograms-wiki.pages.dev":
                print(f"\nFixing CNAME content...")
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
            else:
                print("\nRecord looks correct. Checking Pages DNS activation...")

if __name__ == "__main__":
    main()
