#!/usr/bin/env python3
"""
Generate XML sitemap for AffiliatePrograms.wiki

Generates sitemaps for:
- Program pages: /programs/{slug}
- Network pages: /networks/{slug}
- Category pages: /categories/{slug}
- Country pages: /countries/{country}

Run periodically to keep sitemap fresh.
"""

import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def get_db_url() -> str:
    """Get database URL from environment or gcloud."""
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        return db_url

    try:
        result = subprocess.run(
            ["/home/skynet/google-cloud-sdk/bin/gcloud", "secrets", "versions", "access",
             "latest", "--secret=database_url_affiliate_wiki", "--project=superapp-466313"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        print(f"Failed to get DB URL from gcloud: {e}")

    raise RuntimeError("DATABASE_URL not set")


def slugify(name: str) -> str:
    """Convert name to URL slug."""
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', name.lower())
    slug = re.sub(r'^-|-$', '', slug)
    return slug


def generate_sitemap(output_dir: str = "/home/skynet/affiliateprograms-wiki/web/affiliate-compass-ui/public"):
    """Generate XML sitemap files."""
    import psycopg

    db_url = get_db_url()
    base_url = "https://affiliateprograms.wiki"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    urls = []

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            # Static pages
            static_pages = [
                ("", "1.0", "daily"),
                ("/programs", "0.9", "daily"),
                ("/networks", "0.8", "weekly"),
                ("/categories", "0.8", "weekly"),
                ("/countries", "0.8", "weekly"),
            ]
            for path, priority, freq in static_pages:
                urls.append({
                    "loc": f"{base_url}{path}",
                    "lastmod": now,
                    "changefreq": freq,
                    "priority": priority,
                })

            # Program pages (only deep-researched ones)
            cur.execute("""
                SELECT p.name, r.extracted->>'deep_researched_at'
                FROM affiliate_wiki.programs p
                JOIN affiliate_wiki.program_research r ON r.program_id = p.id
                WHERE r.extracted->>'deep_researched_at' IS NOT NULL
                ORDER BY r.extracted->>'deep_researched_at' DESC
                LIMIT 50000
            """)
            for name, researched_at in cur.fetchall():
                slug = slugify(name)
                lastmod = researched_at[:10] if researched_at else now
                urls.append({
                    "loc": f"{base_url}/programs/{slug}",
                    "lastmod": lastmod,
                    "changefreq": "weekly",
                    "priority": "0.7",
                })

            # Network pages
            cur.execute("SELECT name FROM affiliate_wiki.cpa_networks ORDER BY name")
            for (name,) in cur.fetchall():
                slug = slugify(name)
                urls.append({
                    "loc": f"{base_url}/networks/{slug}",
                    "lastmod": now,
                    "changefreq": "monthly",
                    "priority": "0.6",
                })

            # Category pages
            cur.execute("SELECT slug FROM affiliate_wiki.categories ORDER BY path")
            for (slug,) in cur.fetchall():
                urls.append({
                    "loc": f"{base_url}/categories/{slug}",
                    "lastmod": now,
                    "changefreq": "weekly",
                    "priority": "0.8",
                })

            # Country pages (top 50)
            cur.execute("""
                WITH country_counts AS (
                    SELECT unnest(countries) as country, COUNT(*) as cnt
                    FROM affiliate_wiki.programs
                    WHERE countries IS NOT NULL
                    GROUP BY unnest(countries)
                )
                SELECT country FROM country_counts ORDER BY cnt DESC LIMIT 50
            """)
            for (country,) in cur.fetchall():
                # URL encode country name
                country_slug = country.replace(" ", "%20")
                urls.append({
                    "loc": f"{base_url}/countries/{country_slug}",
                    "lastmod": now,
                    "changefreq": "weekly",
                    "priority": "0.6",
                })

    # Generate sitemap XML
    sitemap_xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    sitemap_xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    for url in urls:
        sitemap_xml.append("  <url>")
        sitemap_xml.append(f"    <loc>{url['loc']}</loc>")
        sitemap_xml.append(f"    <lastmod>{url['lastmod']}</lastmod>")
        sitemap_xml.append(f"    <changefreq>{url['changefreq']}</changefreq>")
        sitemap_xml.append(f"    <priority>{url['priority']}</priority>")
        sitemap_xml.append("  </url>")

    sitemap_xml.append("</urlset>")

    # Write sitemap
    output_path = Path(output_dir) / "sitemap.xml"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(sitemap_xml))

    print(f"Generated sitemap with {len(urls)} URLs")
    print(f"Saved to: {output_path}")

    # Also generate robots.txt
    robots_txt = f"""User-agent: *
Allow: /

Sitemap: {base_url}/sitemap.xml

# API endpoints are crawlable
Allow: /api/

# Rate limit API requests
Crawl-delay: 1
"""
    robots_path = Path(output_dir) / "robots.txt"
    robots_path.write_text(robots_txt)
    print(f"Generated robots.txt: {robots_path}")

    return len(urls)


if __name__ == "__main__":
    generate_sitemap()
