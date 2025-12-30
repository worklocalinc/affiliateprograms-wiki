#!/usr/bin/env python3
"""Set up Cloudflare DNS and tunnels for affiliateprograms.wiki"""

import subprocess
import requests
import json
import sys

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
    account_id = get_secret("CLOUDFLARE_ACCOUNT_ID")

    headers = {
        "Authorization": f"Bearer {cf_token}",
        "Content-Type": "application/json"
    }

    # Get DNS records
    print("=== Current DNS Records ===")
    r = requests.get(
        f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records",
        headers=headers
    )
    data = r.json()

    if data.get("success"):
        for rec in data.get("result", []):
            print(f"{rec['name']:40} {rec['type']:6} {rec['content']}")
    else:
        print(f"Error: {data.get('errors')}")

    # Check if api subdomain exists
    print("\n=== Checking api.affiliateprograms.wiki ===")
    api_records = [r for r in data.get("result", []) if r["name"] == "api.affiliateprograms.wiki"]
    if api_records:
        print(f"API record exists: {api_records[0]['content']}")
    else:
        print("No API record found - need to set up tunnel or CNAME")

if __name__ == "__main__":
    main()
