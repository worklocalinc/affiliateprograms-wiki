#!/usr/bin/env python3
"""
Staleness Patrol

Automated system that:
1. Re-checks high-value program URLs periodically
2. Auto-proposes fixes when URLs break
3. Flags programs needing re-research
4. Maintains URL verification database

This is the "living wiki" component - it automatically opens proposals
when things change or break.
"""
from __future__ import annotations

import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import requests


# ============================================
# Configuration
# ============================================

DEFAULT_API_BASE = "http://localhost:8120"
DEFAULT_RESEARCHER_KEY = "ak_researcher_default"
DEFAULT_REVIEWER_KEY = "ak_reviewer_default"

# URL check configuration
URL_CHECK_TIMEOUT = 10
BATCH_SIZE = 100
PARALLEL_WORKERS = 10

# Staleness thresholds (in days)
HIGH_VALUE_CHECK_INTERVAL = 1    # Check daily
NORMAL_CHECK_INTERVAL = 7        # Check weekly
STALE_RESEARCH_THRESHOLD = 30    # Re-research after 30 days


@dataclass
class URLCheckResult:
    """Result of checking a single URL."""
    program_id: int
    program_name: str
    url: str
    url_type: str
    status: str  # success, redirect, broken, timeout
    http_code: int | None
    final_url: str | None
    response_time_ms: int | None


@dataclass
class PatrolReport:
    """Summary of a patrol run."""
    checked: int
    success: int
    broken: int
    timeout: int
    proposals_created: int
    errors: list[str]


class StalenessPatrol:
    """
    Automated staleness detection and proposal generation.

    Usage:
        patrol = StalenessPatrol()

        # Run full patrol
        report = patrol.run()

        # Check specific programs
        patrol.check_program_urls([123, 456, 789])

        # Find stale research
        stale = patrol.find_stale_research(days=30)
    """

    def __init__(
        self,
        api_base: str = DEFAULT_API_BASE,
        researcher_key: str = DEFAULT_RESEARCHER_KEY,
        reviewer_key: str = DEFAULT_REVIEWER_KEY
    ):
        self.api_base = api_base.rstrip("/")
        self.researcher_key = researcher_key
        self.reviewer_key = reviewer_key

    def _get_db_url(self) -> str:
        """Get database URL."""
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
        except Exception:
            pass

        raise RuntimeError("DATABASE_URL not set")

    def _api_get(self, path: str, agent_key: str) -> dict:
        """Make authenticated GET request."""
        response = requests.get(
            f"{self.api_base}{path}",
            headers={"X-Agent-Key": agent_key},
            timeout=30
        )
        response.raise_for_status()
        return response.json()

    def _api_post(self, path: str, data: dict, agent_key: str) -> dict:
        """Make authenticated POST request."""
        response = requests.post(
            f"{self.api_base}{path}",
            headers={
                "X-Agent-Key": agent_key,
                "Content-Type": "application/json",
            },
            json=data,
            timeout=30
        )
        response.raise_for_status()
        return response.json()

    def check_url(self, url: str) -> tuple[str, int | None, str | None, int | None]:
        """
        Check if a URL is accessible.

        Returns: (status, http_code, final_url, response_time_ms)
        """
        try:
            start = datetime.now()
            response = requests.head(
                url,
                timeout=URL_CHECK_TIMEOUT,
                allow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 (compatible; AffiliateWiki/1.0)"}
            )
            elapsed = int((datetime.now() - start).total_seconds() * 1000)

            if response.status_code < 400:
                if response.url != url:
                    return "redirect", response.status_code, str(response.url), elapsed
                return "success", response.status_code, str(response.url), elapsed
            else:
                return "broken", response.status_code, None, elapsed

        except requests.Timeout:
            return "timeout", None, None, None
        except requests.RequestException:
            return "broken", None, None, None

    def get_programs_to_check(self, limit: int = BATCH_SIZE) -> list[dict]:
        """
        Get programs that need URL verification.

        Priority:
        1. Programs with broken URLs that haven't been fixed
        2. Programs not checked in CHECK_INTERVAL days
        3. High-value programs (most categories, most views)
        """
        import psycopg

        db_url = self._get_db_url()

        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    WITH programs_to_check AS (
                        -- Programs with signup URLs that haven't been verified recently
                        SELECT
                            p.id,
                            p.name,
                            p.domain,
                            r.extracted->>'signup_url' as signup_url,
                            COALESCE(
                                (SELECT MAX(verified_at) FROM affiliate_wiki.verification_runs v
                                 WHERE v.program_id = p.id AND v.url_type = 'signup'),
                                '1970-01-01'::timestamptz
                            ) as last_checked
                        FROM affiliate_wiki.programs p
                        JOIN affiliate_wiki.program_research r ON r.program_id = p.id
                        WHERE r.extracted->>'signup_url' IS NOT NULL
                          AND r.extracted->>'signup_url' LIKE 'http%%'
                        ORDER BY last_checked ASC
                        LIMIT %s
                    )
                    SELECT id, name, domain, signup_url, last_checked
                    FROM programs_to_check
                """, (limit,))

                programs = []
                for row in cur.fetchall():
                    programs.append({
                        "id": row[0],
                        "name": row[1],
                        "domain": row[2],
                        "signup_url": row[3],
                        "last_checked": row[4]
                    })

                return programs

    def check_program_urls(self, program_ids: list[int]) -> list[URLCheckResult]:
        """Check URLs for specific programs."""
        import psycopg

        db_url = self._get_db_url()
        results = []

        # Fetch program data
        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT p.id, p.name, r.extracted->>'signup_url' as signup_url
                    FROM affiliate_wiki.programs p
                    JOIN affiliate_wiki.program_research r ON r.program_id = p.id
                    WHERE p.id = ANY(%s)
                      AND r.extracted->>'signup_url' IS NOT NULL
                """, (program_ids,))

                programs = list(cur.fetchall())

        # Check each URL
        for program_id, name, url in programs:
            if not url or not url.startswith("http"):
                continue

            status, http_code, final_url, response_time = self.check_url(url)

            results.append(URLCheckResult(
                program_id=program_id,
                program_name=name,
                url=url,
                url_type="signup",
                status=status,
                http_code=http_code,
                final_url=final_url,
                response_time_ms=response_time
            ))

        return results

    def store_verification_result(self, result: URLCheckResult):
        """Store URL check result in database."""
        import psycopg
        import json

        db_url = self._get_db_url()

        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO affiliate_wiki.verification_runs
                    (program_id, url, url_type, status, http_code, final_url, response_time_ms)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    result.program_id,
                    result.url,
                    result.url_type,
                    result.status,
                    result.http_code,
                    result.final_url,
                    result.response_time_ms
                ))
            conn.commit()

    def create_fix_proposal(self, program_id: int, old_url: str, issue: str) -> dict | None:
        """
        Create a proposal to fix a broken URL.

        If we can't find a new URL, we mark the program as needing attention.
        """
        try:
            # Try to find a working affiliate page
            import psycopg

            db_url = self._get_db_url()

            with psycopg.connect(db_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT domain FROM affiliate_wiki.programs WHERE id = %s
                    """, (program_id,))
                    row = cur.fetchone()
                    domain = row[0] if row else None

            if not domain:
                return None

            # Try common affiliate page paths
            alternatives = [
                f"https://{domain}/affiliate",
                f"https://{domain}/affiliates",
                f"https://{domain}/partners",
                f"https://{domain}/partner",
                f"https://www.{domain}/affiliate",
            ]

            new_url = None
            for alt_url in alternatives:
                status, _, final_url, _ = self.check_url(alt_url)
                if status in ("success", "redirect"):
                    new_url = final_url or alt_url
                    break

            if new_url:
                # Submit proposal with new URL
                return self._api_post("/editorial/proposals", {
                    "entity_type": "program",
                    "entity_id": program_id,
                    "changes": {"signup_url": new_url},
                    "sources": [{"url": new_url, "verified": True, "type": "url_fix"}],
                    "reasoning": f"Original URL ({old_url}) is {issue}. Found replacement at {new_url}",
                }, self.researcher_key)
            else:
                # Submit proposal to mark as needs attention
                return self._api_post("/editorial/proposals", {
                    "entity_type": "program",
                    "entity_id": program_id,
                    "changes": {"_needs_attention": True, "_url_issue": issue},
                    "sources": [],
                    "reasoning": f"Signup URL ({old_url}) is {issue}. No alternative found.",
                }, self.researcher_key)

        except Exception as e:
            print(f"  Error creating proposal: {e}")
            return None

    def find_stale_research(self, days: int = STALE_RESEARCH_THRESHOLD) -> list[dict]:
        """Find programs with stale research data."""
        import psycopg

        db_url = self._get_db_url()

        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT p.id, p.name, p.domain,
                           r.extracted->>'deep_researched_at' as researched_at
                    FROM affiliate_wiki.programs p
                    JOIN affiliate_wiki.program_research r ON r.program_id = p.id
                    WHERE r.extracted->>'deep_researched_at' IS NOT NULL
                      AND (r.extracted->>'deep_researched_at')::timestamptz
                          < NOW() - INTERVAL '%s days'
                    ORDER BY (r.extracted->>'deep_researched_at')::timestamptz ASC
                    LIMIT 100
                """, (days,))

                return [
                    {"id": row[0], "name": row[1], "domain": row[2], "researched_at": row[3]}
                    for row in cur.fetchall()
                ]

    def run(
        self,
        batch_size: int = BATCH_SIZE,
        workers: int = PARALLEL_WORKERS,
        create_proposals: bool = True
    ) -> PatrolReport:
        """
        Run the staleness patrol.

        1. Get programs to check
        2. Verify URLs in parallel
        3. Store results
        4. Create fix proposals for broken URLs

        Returns:
            PatrolReport with summary
        """
        print(f"Starting staleness patrol (batch_size={batch_size})...")

        # Get programs to check
        programs = self.get_programs_to_check(limit=batch_size)
        print(f"Found {len(programs)} programs to check")

        results = []
        broken_programs = []
        errors = []

        # Check URLs in parallel
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {}
            for prog in programs:
                url = prog["signup_url"]
                if url and url.startswith("http"):
                    futures[executor.submit(self.check_url, url)] = prog

            for future in as_completed(futures):
                prog = futures[future]
                try:
                    status, http_code, final_url, response_time = future.result()

                    result = URLCheckResult(
                        program_id=prog["id"],
                        program_name=prog["name"],
                        url=prog["signup_url"],
                        url_type="signup",
                        status=status,
                        http_code=http_code,
                        final_url=final_url,
                        response_time_ms=response_time
                    )
                    results.append(result)

                    # Store result
                    self.store_verification_result(result)

                    # Track broken URLs
                    if status in ("broken", "timeout"):
                        broken_programs.append((prog, result))
                        print(f"  ✗ {prog['name']}: {status}")
                    else:
                        print(f"  ✓ {prog['name']}: {status}")

                except Exception as e:
                    errors.append(f"{prog['name']}: {e}")

        # Create proposals for broken URLs
        proposals_created = 0
        if create_proposals and broken_programs:
            print(f"\nCreating proposals for {len(broken_programs)} broken URLs...")

            for prog, result in broken_programs:
                proposal = self.create_fix_proposal(
                    program_id=prog["id"],
                    old_url=prog["signup_url"],
                    issue=f"{result.status} (HTTP {result.http_code})" if result.http_code else result.status
                )
                if proposal:
                    proposals_created += 1
                    print(f"  → Created proposal for {prog['name']}")

        # Summary
        report = PatrolReport(
            checked=len(results),
            success=sum(1 for r in results if r.status == "success"),
            broken=sum(1 for r in results if r.status == "broken"),
            timeout=sum(1 for r in results if r.status == "timeout"),
            proposals_created=proposals_created,
            errors=errors
        )

        print(f"\nPatrol complete:")
        print(f"  Checked: {report.checked}")
        print(f"  Success: {report.success}")
        print(f"  Broken: {report.broken}")
        print(f"  Timeout: {report.timeout}")
        print(f"  Proposals: {report.proposals_created}")
        if report.errors:
            print(f"  Errors: {len(report.errors)}")

        return report


# CLI
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Staleness Patrol")
    parser.add_argument("--run", action="store_true", help="Run full patrol")
    parser.add_argument("--check-program", type=int, nargs="+", help="Check specific program IDs")
    parser.add_argument("--find-stale", type=int, default=0, help="Find research older than N days")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE, help="Batch size")
    parser.add_argument("--workers", type=int, default=PARALLEL_WORKERS, help="Parallel workers")
    parser.add_argument("--no-proposals", action="store_true", help="Don't create proposals")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE, help="API base URL")

    args = parser.parse_args()

    patrol = StalenessPatrol(api_base=args.api_base)

    if args.run:
        report = patrol.run(
            batch_size=args.batch_size,
            workers=args.workers,
            create_proposals=not args.no_proposals
        )

    elif args.check_program:
        print(f"Checking {len(args.check_program)} programs...")
        results = patrol.check_program_urls(args.check_program)
        for r in results:
            print(f"  {r.program_name}: {r.status} (HTTP {r.http_code})")

    elif args.find_stale > 0:
        print(f"Finding research older than {args.find_stale} days...")
        stale = patrol.find_stale_research(days=args.find_stale)
        print(f"Found {len(stale)} stale programs:")
        for p in stale[:20]:
            print(f"  {p['name']}: researched {p['researched_at']}")

    else:
        parser.print_help()
