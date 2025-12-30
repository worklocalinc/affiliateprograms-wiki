#!/usr/bin/env python3
"""
Fetch logos for affiliate programs and networks.

Uses multiple sources:
1. Clearbit Logo API (high quality, free for basic use)
2. Google Favicon Service (reliable fallback)
3. DuckDuckGo Icons (another fallback)

Usage:
    python tools/fetch_logos.py --limit 1000 --parallel 50
    python tools/fetch_logos.py --networks  # Fetch network logos only
"""

import argparse
import os
import sys
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

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

    # Remove protocol if present
    if "://" in domain:
        domain = urlparse(domain).netloc or domain.split("://")[1]

    # Remove www prefix
    if domain.startswith("www."):
        domain = domain[4:]

    # Remove trailing slash and path
    domain = domain.split("/")[0]

    return domain.lower().strip()


def check_logo_url(url: str, timeout: int = 5) -> bool:
    """Check if a logo URL is valid and returns an image."""
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        if response.status_code == 200:
            content_type = response.headers.get("content-type", "")
            return "image" in content_type or "icon" in content_type
        return False
    except:
        return False


def get_logo_url(domain: str) -> dict:
    """Try multiple sources to get a logo URL for a domain."""
    domain = clean_domain(domain)
    if not domain:
        return {"logo_url": None, "logo_source": None}

    # Try Clearbit first (highest quality)
    clearbit_url = f"https://logo.clearbit.com/{domain}"
    if check_logo_url(clearbit_url):
        return {"logo_url": clearbit_url, "logo_source": "clearbit"}

    # Try Google Favicon (128px)
    google_url = f"https://www.google.com/s2/favicons?domain={domain}&sz=128"
    if check_logo_url(google_url):
        return {"logo_url": google_url, "logo_source": "google"}

    # Try DuckDuckGo
    ddg_url = f"https://icons.duckduckgo.com/ip3/{domain}.ico"
    if check_logo_url(ddg_url):
        return {"logo_url": ddg_url, "logo_source": "duckduckgo"}

    # Try with www prefix
    www_domain = f"www.{domain}"
    clearbit_www = f"https://logo.clearbit.com/{www_domain}"
    if check_logo_url(clearbit_www):
        return {"logo_url": clearbit_www, "logo_source": "clearbit"}

    return {"logo_url": None, "logo_source": None}


def fetch_program_logo(program: dict) -> tuple[int, dict]:
    """Fetch logo for a single program."""
    program_id = program["id"]
    domain = program.get("domain") or ""

    result = get_logo_url(domain)
    return (program_id, result)


def fetch_programs_without_logos(db_url: str, limit: int) -> list[dict]:
    """Fetch programs that don't have logos yet."""
    import psycopg

    sql = """
        SELECT p.id, p.name, p.domain
        FROM affiliate_wiki.programs p
        WHERE p.domain IS NOT NULL
          AND p.domain != ''
          AND (p.metadata IS NULL OR p.metadata->>'logo_url' IS NULL)
        ORDER BY p.id
        LIMIT %s
    """

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (limit,))
            rows = cur.fetchall()

    return [{"id": r[0], "name": r[1], "domain": r[2]} for r in rows]


def fetch_networks_without_logos(db_url: str) -> list[dict]:
    """Fetch networks that don't have logos yet."""
    import psycopg

    sql = """
        SELECT n.id, n.name, n.website
        FROM affiliate_wiki.cpa_networks n
        WHERE n.website IS NOT NULL
          AND n.website != ''
          AND (n.raw IS NULL OR n.raw->>'logo_url' IS NULL)
        ORDER BY n.id
    """

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()

    return [{"id": r[0], "name": r[1], "domain": r[2]} for r in rows]


def update_program_logo(db_url: str, program_id: int, logo_data: dict) -> None:
    """Update program with logo information."""
    import psycopg
    from psycopg.types.json import Json

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            # Get existing metadata
            cur.execute("SELECT metadata FROM affiliate_wiki.programs WHERE id = %s", (program_id,))
            row = cur.fetchone()
            existing = row[0] if row and row[0] else {}

            # Merge logo data
            merged = {**existing, **logo_data}

            cur.execute(
                "UPDATE affiliate_wiki.programs SET metadata = %s WHERE id = %s",
                (Json(merged), program_id)
            )
        conn.commit()


def update_network_logo(db_url: str, network_id: int, logo_data: dict) -> None:
    """Update network with logo information."""
    import psycopg
    from psycopg.types.json import Json

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            # Get existing raw data
            cur.execute("SELECT raw FROM affiliate_wiki.cpa_networks WHERE id = %s", (network_id,))
            row = cur.fetchone()
            existing = row[0] if row and row[0] else {}

            # Merge logo data
            merged = {**existing, **logo_data}

            cur.execute(
                "UPDATE affiliate_wiki.cpa_networks SET raw = %s WHERE id = %s",
                (Json(merged), network_id)
            )
        conn.commit()


def run_parallel_logo_fetch(
    items: list[dict],
    db_url: str,
    item_type: str = "program",
    parallel: int = 50,
    verbose: bool = True
) -> dict:
    """Fetch logos in parallel."""
    stats = {"total": len(items), "found": 0, "not_found": 0, "errors": 0}

    if verbose:
        _eprint(f"\nFetching logos for {len(items)} {item_type}s")
        _eprint(f"Parallel workers: {parallel}\n")

    update_fn = update_program_logo if item_type == "program" else update_network_logo

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
                    if verbose:
                        _eprint(f"  [{i}/{len(items)}] OK: {item['name']} -> {logo_data['logo_source']}")
                else:
                    stats["not_found"] += 1
                    logo_data = {"logo_url": None, "logo_source": "not_found"}
                    if verbose:
                        _eprint(f"  [{i}/{len(items)}] NOT FOUND: {item['name']}")

                # Update database
                update_fn(db_url, item_id, logo_data)

            except Exception as e:
                stats["errors"] += 1
                if verbose:
                    _eprint(f"  [{i}/{len(items)}] ERROR: {item['name']} - {e}")

    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch logos for affiliate programs and networks")
    parser.add_argument("--limit", type=int, default=1000, help="Max programs to process")
    parser.add_argument("--parallel", type=int, default=50, help="Parallel workers")
    parser.add_argument("--networks", action="store_true", help="Fetch network logos only")
    parser.add_argument("--programs", action="store_true", help="Fetch program logos only")
    parser.add_argument("--db-url", help="Database URL (or use DATABASE_URL env)")
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

    start_time = time.time()
    total_stats = {"found": 0, "not_found": 0, "errors": 0}

    # Fetch network logos
    if args.networks or not args.programs:
        networks = fetch_networks_without_logos(db_url)
        if networks:
            stats = run_parallel_logo_fetch(
                items=networks,
                db_url=db_url,
                item_type="network",
                parallel=min(args.parallel, len(networks)),
                verbose=not args.quiet
            )
            total_stats["found"] += stats["found"]
            total_stats["not_found"] += stats["not_found"]
            total_stats["errors"] += stats["errors"]
        else:
            _eprint("No networks without logos found.")

    # Fetch program logos
    if args.programs or not args.networks:
        programs = fetch_programs_without_logos(db_url, args.limit)
        if programs:
            stats = run_parallel_logo_fetch(
                items=programs,
                db_url=db_url,
                item_type="program",
                parallel=args.parallel,
                verbose=not args.quiet
            )
            total_stats["found"] += stats["found"]
            total_stats["not_found"] += stats["not_found"]
            total_stats["errors"] += stats["errors"]
        else:
            _eprint("No programs without logos found.")

    elapsed = time.time() - start_time

    print(f"\n{'='*50}")
    print(f"Logo Fetch Complete")
    print(f"{'='*50}")
    print(f"Found:     {total_stats['found']}")
    print(f"Not Found: {total_stats['not_found']}")
    print(f"Errors:    {total_stats['errors']}")
    print(f"Time:      {elapsed:.1f}s")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
