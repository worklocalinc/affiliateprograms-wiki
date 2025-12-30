#!/usr/bin/env python3
"""
Affiliate Programs Deep Research Tool

Uses OpenRouter models (Kimi K2, DeepResearch, Sonar) via ~/ai-shared/tools/deepresearch.py
to collect comprehensive affiliate program data in parallel batches.

Usage:
    python tools/deepresearch.py --limit 100 --parallel 20
    python tools/deepresearch.py --model sonar --parallel 50
    python tools/deepresearch.py --program-id 12345
"""

import argparse
import json
import os
import sys
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

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

# OpenRouter setup
from openai import OpenAI

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

MODELS = {
    "kimi": "moonshotai/kimi-k2-thinking",
    "kimi-free": "moonshotai/kimi-k2:free",
    "deepresearch": "alibaba/tongyi-deepresearch-30b-a3b",
    "deepresearch-free": "alibaba/tongyi-deepresearch-30b-a3b:free",
    "sonar": "perplexity/sonar-pro",
}


def _eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def get_openrouter_client():
    """Get OpenRouter client."""
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY not set in ~/ai-shared/secrets/.env")

    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
        default_headers={
            "HTTP-Referer": "https://affiliateprograms.wiki",
            "X-Title": "AffiliateWiki DeepResearch"
        }
    )


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


@dataclass
class Program:
    id: int
    name: str
    domain: Optional[str]
    extracted: Optional[dict]


def fetch_programs_for_research(db_url: str, limit: int, statuses: list[str]) -> list[Program]:
    """Fetch programs that need deep research."""
    import psycopg

    sql = """
        SELECT p.id, p.name, p.domain, r.extracted
        FROM affiliate_wiki.program_research r
        JOIN affiliate_wiki.programs p ON p.id = r.program_id
        WHERE r.status = ANY(%s)
          AND (r.extracted IS NULL OR r.extracted->>'deep_researched_at' IS NULL)
        ORDER BY p.id ASC
        LIMIT %s
    """

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (statuses, limit))
            rows = cur.fetchall()

    programs = []
    for r in rows:
        extracted = r[3] if isinstance(r[3], dict) else None
        programs.append(Program(
            id=int(r[0]),
            name=str(r[1]),
            domain=str(r[2]) if r[2] else None,
            extracted=extracted
        ))

    return programs


def build_research_query(program: Program) -> str:
    """Build a focused research query for an affiliate program."""
    name = program.name
    domain = program.domain or ""

    return f"""Research the affiliate/partner program for "{name}" (website: {domain}).

Extract these specific details in a structured format:
1. Commission rate (percentage or flat fee amount)
2. Cookie duration (in days)
3. Payout model type (CPA, CPS, CPL, RevShare, Recurring)
4. Minimum payout threshold (e.g., $50)
5. Payment methods accepted (PayPal, bank transfer, check, etc.)
6. Payment frequency (weekly, monthly, net-30, etc.)
7. Tracking platform (Impact, ShareASale, CJ, Awin, Rakuten, in-house, etc.)
8. Application requirements
9. Promotional restrictions (PPC, coupon sites, etc.)
10. Official affiliate signup URL
11. Languages supported by the affiliate program
12. Countries/regions where the affiliate program is available
13. Regional affiliate links (if the program has different signup URLs for different countries/languages)

Format your response as:
COMMISSION: [value]
COOKIE_DAYS: [number]
PAYOUT_MODEL: [type]
MIN_PAYOUT: [amount]
PAYMENT_METHODS: [list]
PAYMENT_FREQ: [frequency]
TRACKING: [platform]
REQUIREMENTS: [text]
RESTRICTIONS: [list]
SIGNUP_URL: [url]
LANGUAGES: [comma-separated list of supported languages, e.g., English, Spanish, French]
COUNTRIES: [comma-separated list of available countries/regions, e.g., US, UK, DE, Global]
REGIONAL_LINKS: [JSON format: {{"US": "url", "UK": "url"}} or "none" if single global link]
NOTES: [any other relevant info]

If the affiliate program doesn't exist or you can't find it, respond with:
NO_PROGRAM: true
REASON: [why]"""


def parse_research_response(response: str, program: Program) -> dict:
    """Parse structured response into fields dict."""
    fields = {}

    # Parse structured fields
    patterns = {
        "commission_rate": r"COMMISSION:\s*(.+)",
        "cookie_duration_days": r"COOKIE_DAYS:\s*(\d+)",
        "payout_model": r"PAYOUT_MODEL:\s*(.+)",
        "minimum_payout": r"MIN_PAYOUT:\s*(.+)",
        "payment_methods": r"PAYMENT_METHODS:\s*(.+)",
        "payment_frequency": r"PAYMENT_FREQ:\s*(.+)",
        "tracking_platform": r"TRACKING:\s*(.+)",
        "requirements": r"REQUIREMENTS:\s*(.+)",
        "restrictions": r"RESTRICTIONS:\s*(.+)",
        "signup_url": r"SIGNUP_URL:\s*(https?://\S+)",
        "languages": r"LANGUAGES:\s*(.+)",
        "countries": r"COUNTRIES:\s*(.+)",
        "regional_links": r"REGIONAL_LINKS:\s*(.+)",
        "notes": r"NOTES:\s*(.+)",
    }

    for field, pattern in patterns.items():
        m = re.search(pattern, response, re.I | re.M)
        if m:
            value = m.group(1).strip()
            if value.lower() not in ["n/a", "not found", "unknown", "none", "-"]:
                # Convert cookie days to int
                if field == "cookie_duration_days":
                    try:
                        fields[field] = int(value)
                    except ValueError:
                        pass
                # Parse lists
                elif field in ["payment_methods", "restrictions", "languages", "countries"]:
                    items = [x.strip() for x in re.split(r'[,;]', value) if x.strip()]
                    if items:
                        fields[field] = items
                # Parse regional links as JSON
                elif field == "regional_links":
                    if value.lower() not in ["none", "n/a", "single", "global"]:
                        try:
                            # Try to parse as JSON
                            links_data = json.loads(value)
                            if isinstance(links_data, dict) and links_data:
                                fields[field] = links_data
                        except json.JSONDecodeError:
                            # Try to extract URLs from the string
                            url_matches = re.findall(r'(\w{2,3}):\s*(https?://\S+)', value)
                            if url_matches:
                                fields[field] = dict(url_matches)
                else:
                    fields[field] = value

    # Check for no program
    if re.search(r"NO_PROGRAM:\s*true", response, re.I):
        fields["program_status"] = "not_found"
        reason_m = re.search(r"REASON:\s*(.+)", response, re.I | re.M)
        if reason_m:
            fields["not_found_reason"] = reason_m.group(1).strip()

    # Store full response for reference
    fields["deep_research_response"] = response[:5000]

    return fields


def run_single_research(
    program: Program,
    client: OpenAI,
    model_id: str,
    verbose: bool = False
) -> tuple[Program, dict, Optional[str]]:
    """Run deep research for a single program."""
    query = build_research_query(program)

    try:
        if verbose:
            _eprint(f"  Researching: {program.name} ({program.domain})")

        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {
                    "role": "system",
                    "content": "You are an affiliate marketing research assistant. Extract specific, structured data about affiliate programs. Be precise and factual. If information is not available, say so clearly."
                },
                {
                    "role": "user",
                    "content": query
                }
            ],
            max_tokens=2048,
            temperature=0.3,
        )

        result_text = response.choices[0].message.content or ""
        fields = parse_research_response(result_text, program)
        fields["deep_researched_at"] = _now_iso()
        fields["deep_research_model"] = model_id

        return (program, fields, None)

    except Exception as e:
        return (program, {}, str(e))


def update_program_research(db_url: str, program_id: int, fields: dict, error: Optional[str] = None) -> None:
    """Update program research with deep research results."""
    import psycopg
    from psycopg.types.json import Json

    fetch_sql = "SELECT extracted FROM affiliate_wiki.program_research WHERE program_id = %s"

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(fetch_sql, (program_id,))
            row = cur.fetchone()
            existing = row[0] if row and isinstance(row[0], dict) else {}

            merged = {**existing, **fields}
            if error:
                merged["deep_research_error"] = error

            update_sql = """
                UPDATE affiliate_wiki.program_research
                SET extracted = %s,
                    last_attempt_at = NOW()
                WHERE program_id = %s
            """
            cur.execute(update_sql, (Json(merged), program_id))
        conn.commit()


def run_single_research_with_retry(
    program: Program,
    client: OpenAI,
    model_id: str,
    verbose: bool = False,
    max_retries: int = 3
) -> tuple[Program, dict, Optional[str]]:
    """Run deep research with retry on rate limit."""
    for attempt in range(max_retries):
        program, fields, error = run_single_research(program, client, model_id, verbose)
        if error and "429" in error:
            wait_time = (attempt + 1) * 5  # Exponential backoff: 5, 10, 15 seconds
            time.sleep(wait_time)
            continue
        return program, fields, error
    return program, fields, error


def run_parallel_research(
    programs: list[Program],
    db_url: str,
    model_key: str = "kimi",
    parallel: int = 20,
    verbose: bool = True
) -> dict:
    """Run deep research in parallel batches."""
    stats = {"total": len(programs), "success": 0, "failed": 0, "no_program": 0}

    model_id = MODELS.get(model_key, model_key)

    if verbose:
        _eprint(f"\nStarting deep research for {len(programs)} programs")
        _eprint(f"Model: {model_id}")
        _eprint(f"Parallel workers: {parallel}\n")

    client = get_openrouter_client()

    with ThreadPoolExecutor(max_workers=parallel) as executor:
        futures = {
            executor.submit(run_single_research_with_retry, p, client, model_id, verbose): p
            for p in programs
        }

        for i, future in enumerate(as_completed(futures), 1):
            program, fields, error = future.result()

            if error:
                stats["failed"] += 1
                if verbose:
                    _eprint(f"  [{i}/{len(programs)}] FAILED: {program.name} - {error[:60]}")
            elif fields.get("program_status") == "not_found":
                stats["no_program"] += 1
                if verbose:
                    _eprint(f"  [{i}/{len(programs)}] NO PROGRAM: {program.name}")
            else:
                stats["success"] += 1
                if verbose:
                    commission = fields.get("commission_rate", "?")
                    cookie = fields.get("cookie_duration_days", "?")
                    platform = fields.get("tracking_platform", "?")
                    _eprint(f"  [{i}/{len(programs)}] OK: {program.name} - {commission}, {cookie}d, {platform}")

            # Update database
            update_program_research(db_url, program.id, fields, error)

    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description="Deep research affiliate programs via OpenRouter")
    parser.add_argument("--limit", type=int, default=100, help="Max programs to research")
    parser.add_argument("--parallel", type=int, default=20, help="Parallel workers")
    parser.add_argument("--model", default="kimi",
                        choices=list(MODELS.keys()),
                        help="Model to use (default: kimi)")
    parser.add_argument("--status", default="success,needs_search",
                        help="Comma-separated statuses to research")
    parser.add_argument("--program-id", type=int, help="Research a specific program")
    parser.add_argument("--db-url", help="Database URL (or use DATABASE_URL env)")
    parser.add_argument("--quiet", action="store_true", help="Less output")
    parser.add_argument("--list-models", action="store_true", help="List available models")

    args = parser.parse_args()

    if args.list_models:
        print("\nAvailable Models:")
        for key, model_id in MODELS.items():
            print(f"  {key:20} -> {model_id}")
        return 0

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

    statuses = [s.strip() for s in args.status.split(",")]

    if args.program_id:
        sql = """
            SELECT p.id, p.name, p.domain, r.extracted
            FROM affiliate_wiki.programs p
            LEFT JOIN affiliate_wiki.program_research r ON r.program_id = p.id
            WHERE p.id = %s
        """
        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (args.program_id,))
                row = cur.fetchone()
                if not row:
                    _eprint(f"Program {args.program_id} not found")
                    return 1
                programs = [Program(
                    id=int(row[0]),
                    name=str(row[1]),
                    domain=str(row[2]) if row[2] else None,
                    extracted=row[3] if isinstance(row[3], dict) else None
                )]
    else:
        programs = fetch_programs_for_research(db_url, args.limit, statuses)

    if not programs:
        print("No programs to research.")
        return 0

    start_time = time.time()
    stats = run_parallel_research(
        programs=programs,
        db_url=db_url,
        model_key=args.model,
        parallel=args.parallel,
        verbose=not args.quiet
    )
    elapsed = time.time() - start_time

    print(f"\n{'='*50}")
    print(f"Deep Research Complete")
    print(f"{'='*50}")
    print(f"Total:      {stats['total']}")
    print(f"Success:    {stats['success']}")
    print(f"No Program: {stats['no_program']}")
    print(f"Failed:     {stats['failed']}")
    print(f"Time:       {elapsed:.1f}s ({elapsed/max(1,stats['total']):.2f}s/program)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
