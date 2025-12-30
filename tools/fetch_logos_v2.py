#!/usr/bin/env python3
"""
Fetch REAL logos (not favicons) for affiliate programs and networks.

Sources (in order):
1. Scrape og:image from website (often the logo)
2. Scrape apple-touch-icon (high quality)
3. Brandfetch API (real logos)
4. Clearbit Logo API (fallback)

Usage:
    python tools/fetch_logos_v2.py --limit 1000 --parallel 30
"""

import argparse
import os
import re
import sys
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse, urljoin

# Load environment
env_file = Path.home() / "ai-shared" / "secrets" / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, _, value = line.partition('=')
                value = value.strip('"').strip("'")
                os.environ.setdefault(key.strip(), value)


def _eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


def get_db_url() -> str:
    """Get database URL from environment or gcloud."""
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        return db_url

    import subprocess
    try:
        result = subprocess.run(
            ["/home/skynet/google-cloud-sdk/bin/gcloud", "secrets", "versions", "access",
             "latest", "--secret=database_url_affiliate_wiki", "--project=superapp-466313"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        _eprint(f"Failed to get DB URL from gcloud: {e}")

    raise RuntimeError("DATABASE_URL not set and gcloud lookup failed")


def clean_domain(domain: str) -> str:
    """Clean domain for logo lookup."""
    if not domain:
        return ""

    if "://" in domain:
        domain = urlparse(domain).netloc or domain.split("://")[1]

    if domain.startswith("www."):
        domain = domain[4:]

    domain = domain.split("/")[0]
    return domain.lower().strip()


def check_image_url(url: str, timeout: int = 5, min_size: int = 1000) -> bool:
    """Check if URL returns a valid image of reasonable size."""
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        if response.status_code != 200:
            return False

        content_type = response.headers.get("content-type", "")
        if "image" not in content_type:
            return False

        # Check size - we want real logos, not tiny icons
        content_length = response.headers.get("content-length")
        if content_length and int(content_length) < min_size:
            return False  # Too small, probably a favicon

        return True
    except:
        return False


def scrape_og_image(domain: str, timeout: int = 10) -> str | None:
    """Scrape og:image from website - often contains the logo."""
    try:
        url = f"https://{domain}"
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; LogoBot/1.0; +https://affiliateprograms.wiki)"
        }
        response = requests.get(url, timeout=timeout, headers=headers, allow_redirects=True)

        if response.status_code != 200:
            return None

        html = response.text[:50000]  # Only check first 50KB

        # Look for og:image
        og_match = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
        if not og_match:
            og_match = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', html, re.I)

        if og_match:
            img_url = og_match.group(1)
            # Make absolute URL
            if img_url.startswith("//"):
                img_url = "https:" + img_url
            elif img_url.startswith("/"):
                img_url = f"https://{domain}{img_url}"
            elif not img_url.startswith("http"):
                img_url = f"https://{domain}/{img_url}"

            if check_image_url(img_url, min_size=2000):
                return img_url

        return None
    except:
        return None


def scrape_apple_touch_icon(domain: str, timeout: int = 10) -> str | None:
    """Scrape apple-touch-icon - usually high quality."""
    try:
        url = f"https://{domain}"
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; LogoBot/1.0; +https://affiliateprograms.wiki)"
        }
        response = requests.get(url, timeout=timeout, headers=headers, allow_redirects=True)

        if response.status_code != 200:
            return None

        html = response.text[:50000]

        # Look for apple-touch-icon (prefer larger sizes)
        patterns = [
            r'<link[^>]+rel=["\']apple-touch-icon["\'][^>]+href=["\']([^"\']+)["\']',
            r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']apple-touch-icon["\']',
        ]

        for pattern in patterns:
            match = re.search(pattern, html, re.I)
            if match:
                img_url = match.group(1)
                if img_url.startswith("//"):
                    img_url = "https:" + img_url
                elif img_url.startswith("/"):
                    img_url = f"https://{domain}{img_url}"
                elif not img_url.startswith("http"):
                    img_url = f"https://{domain}/{img_url}"

                if check_image_url(img_url, min_size=1000):
                    return img_url

        # Try common paths
        common_paths = [
            "/apple-touch-icon.png",
            "/apple-touch-icon-180x180.png",
            "/apple-touch-icon-152x152.png",
        ]
        for path in common_paths:
            img_url = f"https://{domain}{path}"
            if check_image_url(img_url, min_size=1000):
                return img_url

        return None
    except:
        return None


def get_clearbit_logo(domain: str) -> str | None:
    """Get logo from Clearbit."""
    url = f"https://logo.clearbit.com/{domain}"
    if check_image_url(url, min_size=1000):
        return url
    return None


def get_brandfetch_logo(domain: str) -> str | None:
    """Get logo from Brandfetch (free tier)."""
    try:
        # Brandfetch has a free lookup
        url = f"https://api.brandfetch.io/v2/brands/{domain}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            logos = data.get("logos", [])
            for logo in logos:
                if logo.get("type") == "logo":
                    formats = logo.get("formats", [])
                    for fmt in formats:
                        if fmt.get("format") in ["png", "svg"]:
                            return fmt.get("src")
        return None
    except:
        return None


def get_logo_url(domain: str) -> dict:
    """Try multiple sources to get a REAL logo URL."""
    domain = clean_domain(domain)
    if not domain:
        return {"logo_url": None, "logo_source": None}

    # 1. Try og:image first (often has logo)
    og_img = scrape_og_image(domain)
    if og_img:
        return {"logo_url": og_img, "logo_source": "og:image"}

    # 2. Try apple-touch-icon (high quality)
    apple_icon = scrape_apple_touch_icon(domain)
    if apple_icon:
        return {"logo_url": apple_icon, "logo_source": "apple-touch-icon"}

    # 3. Try Clearbit (real logos)
    clearbit = get_clearbit_logo(domain)
    if clearbit:
        return {"logo_url": clearbit, "logo_source": "clearbit"}

    # 4. Try with www prefix
    www_domain = f"www.{domain}"
    og_img = scrape_og_image(www_domain)
    if og_img:
        return {"logo_url": og_img, "logo_source": "og:image"}

    clearbit = get_clearbit_logo(www_domain)
    if clearbit:
        return {"logo_url": clearbit, "logo_source": "clearbit"}

    return {"logo_url": None, "logo_source": None}


def fetch_program_logo(program: dict) -> tuple[int, dict]:
    """Fetch logo for a single program."""
    program_id = program["id"]
    domain = program.get("domain") or ""
    result = get_logo_url(domain)
    return (program_id, result)


def fetch_programs_needing_logos(db_url: str, limit: int) -> list[dict]:
    """Fetch programs that need real logos."""
    import psycopg

    sql = """
        SELECT p.id, p.name, p.domain
        FROM affiliate_wiki.programs p
        WHERE p.domain IS NOT NULL
          AND p.domain != ''
          AND (
            p.metadata IS NULL
            OR p.metadata->>'logo_url' IS NULL
            OR p.metadata->>'logo_source' IN ('google', 'duckduckgo')
          )
        ORDER BY p.id
        LIMIT %s
    """

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (limit,))
            rows = cur.fetchall()

    return [{"id": r[0], "name": r[1], "domain": r[2]} for r in rows]


def update_program_logo(db_url: str, program_id: int, logo_data: dict) -> None:
    """Update program with logo information."""
    import psycopg
    from psycopg.types.json import Json

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT metadata FROM affiliate_wiki.programs WHERE id = %s", (program_id,))
            row = cur.fetchone()
            existing = row[0] if row and row[0] else {}
            merged = {**existing, **logo_data}
            cur.execute(
                "UPDATE affiliate_wiki.programs SET metadata = %s WHERE id = %s",
                (Json(merged), program_id)
            )
        conn.commit()


def run_parallel_logo_fetch(
    items: list[dict],
    db_url: str,
    parallel: int = 30,
    verbose: bool = True
) -> dict:
    """Fetch logos in parallel."""
    stats = {"total": len(items), "found": 0, "not_found": 0, "errors": 0}
    source_counts = {}

    if verbose:
        _eprint(f"\nFetching REAL logos for {len(items)} programs")
        _eprint(f"Parallel workers: {parallel}\n")

    with ThreadPoolExecutor(max_workers=parallel) as executor:
        futures = {
            executor.submit(fetch_program_logo, item): item
            for item in items
        }

        for i, future in enumerate(as_completed(futures), 1):
            item = futures[future]
            try:
                item_id, logo_data = future.result()

                if logo_data.get("logo_url"):
                    stats["found"] += 1
                    source = logo_data.get("logo_source", "unknown")
                    source_counts[source] = source_counts.get(source, 0) + 1
                    if verbose:
                        _eprint(f"  [{i}/{len(items)}] OK: {item['name']} -> {source}")
                else:
                    stats["not_found"] += 1
                    logo_data = {"logo_url": None, "logo_source": "not_found"}
                    if verbose:
                        _eprint(f"  [{i}/{len(items)}] NOT FOUND: {item['name']}")

                update_program_logo(db_url, item_id, logo_data)

            except Exception as e:
                stats["errors"] += 1
                if verbose:
                    _eprint(f"  [{i}/{len(items)}] ERROR: {item['name']} - {e}")

    stats["sources"] = source_counts
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch REAL logos for affiliate programs")
    parser.add_argument("--limit", type=int, default=1000, help="Max programs to process")
    parser.add_argument("--parallel", type=int, default=30, help="Parallel workers")
    parser.add_argument("--db-url", help="Database URL")
    parser.add_argument("--quiet", action="store_true", help="Less output")

    args = parser.parse_args()

    try:
        db_url = args.db_url or get_db_url()
    except Exception as e:
        _eprint(f"Error: {e}")
        return 2

    try:
        import psycopg
    except ImportError:
        _eprint("Missing psycopg. Install with: pip install psycopg[binary]")
        return 2

    programs = fetch_programs_needing_logos(db_url, args.limit)
    if not programs:
        print("All programs have real logos!")
        return 0

    start_time = time.time()
    stats = run_parallel_logo_fetch(
        items=programs,
        db_url=db_url,
        parallel=args.parallel,
        verbose=not args.quiet
    )
    elapsed = time.time() - start_time

    print(f"\n{'='*50}")
    print(f"Logo Fetch Complete")
    print(f"{'='*50}")
    print(f"Found:     {stats['found']}")
    print(f"Not Found: {stats['not_found']}")
    print(f"Errors:    {stats['errors']}")
    print(f"Time:      {elapsed:.1f}s")
    print(f"\nSources:")
    for source, count in sorted(stats.get("sources", {}).items(), key=lambda x: -x[1]):
        print(f"  {source}: {count}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
