#!/usr/bin/env python3
"""
Editorial Researcher Agent

LLM-powered research agent that proposes changes through the editorial pipeline
instead of direct database writes.

Key differences from deepresearch.py:
- Returns proposals, not direct DB updates
- Captures current state for diff generation
- Stores full evidence chain
- Submits through /editorial/proposals API
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any

import requests


# ============================================
# Configuration
# ============================================

DEFAULT_API_BASE = "http://localhost:8120"
DEFAULT_AGENT_KEY = "ak_researcher_default"

# OpenRouter models for research
MODELS = {
    "kimi-k2": "moonshotai/kimi-k2-thinking",
    "kimi-k2-free": "moonshotai/kimi-k2:free",
    "deepresearch": "alibaba/tongyi-deepresearch-30b-a3b",
    "sonar": "perplexity/sonar-pro",
}

# Research prompt template
RESEARCH_PROMPT = """Research the affiliate program for: {name}
Domain: {domain}

Find and extract these specific details:

1. COMMISSION: Commission rate (percentage or flat fee)
2. COOKIE_DAYS: Cookie duration in days
3. PAYOUT_MODEL: Payment model (CPA, CPS, CPL, RevShare, Recurring, Hybrid)
4. MINIMUM_PAYOUT: Minimum payout threshold
5. PAYMENT_METHODS: Available payment methods (comma-separated)
6. PAYMENT_FREQUENCY: Payment frequency (weekly, monthly, net-30, etc.)
7. TRACKING_PLATFORM: Tracking platform or network (Impact, ShareASale, CJ, Awin, Rakuten, in-house, etc.)
8. REQUIREMENTS: Application requirements or restrictions
9. RESTRICTIONS: Promotional restrictions (no PPC, no coupon sites, etc.)
10. SIGNUP_URL: Official affiliate signup URL
11. LANGUAGES: Supported languages (comma-separated)
12. COUNTRIES: Available countries/regions (comma-separated)
13. REGIONAL_LINKS: JSON object mapping regions to affiliate URLs if different by region

Format your response EXACTLY like this:
COMMISSION: [value or "Unknown"]
COOKIE_DAYS: [number or "Unknown"]
PAYOUT_MODEL: [value or "Unknown"]
MINIMUM_PAYOUT: [value or "Unknown"]
PAYMENT_METHODS: [value or "Unknown"]
PAYMENT_FREQUENCY: [value or "Unknown"]
TRACKING_PLATFORM: [value or "Unknown"]
REQUIREMENTS: [value or "None" or "Unknown"]
RESTRICTIONS: [value or "None" or "Unknown"]
SIGNUP_URL: [URL or "Unknown"]
LANGUAGES: [value or "Unknown"]
COUNTRIES: [value or "Unknown"]
REGIONAL_LINKS: [JSON object or "None"]

If this domain does NOT have an affiliate program, respond with:
NO_PROGRAM: [reason]

Be precise and factual. Only include information you can verify.
"""


@dataclass
class Program:
    """Program data from database."""
    id: int
    name: str
    domain: str
    current_extracted: dict | None


@dataclass
class ResearchResult:
    """Result of researching a program."""
    program_id: int
    changes: dict
    sources: list[dict]
    reasoning: str
    raw_response: str
    model_used: str
    no_program: bool = False
    error: str | None = None


class EditorialResearcher:
    """
    LLM Researcher that proposes changes instead of direct writes.

    Usage:
        researcher = EditorialResearcher(
            api_base="http://localhost:8120",
            agent_key="ak_researcher_default"
        )

        # Research a single program
        result = researcher.research_program(program_id=123)

        # Research in batch
        results = researcher.research_batch(limit=100)
    """

    def __init__(
        self,
        api_base: str = DEFAULT_API_BASE,
        agent_key: str = DEFAULT_AGENT_KEY,
        openrouter_key: str | None = None,
        model: str = "kimi-k2"
    ):
        self.api_base = api_base.rstrip("/")
        self.agent_key = agent_key
        self.openrouter_key = openrouter_key or self._get_openrouter_key()
        self.model = MODELS.get(model, model)

    def _get_openrouter_key(self) -> str:
        """Get OpenRouter API key from environment or gcloud."""
        key = os.environ.get("OPENROUTER_API_KEY")
        if key:
            return key

        try:
            result = subprocess.run(
                ["/home/skynet/google-cloud-sdk/bin/gcloud", "secrets", "versions", "access",
                 "latest", "--secret=openrouter_api_key", "--project=superapp-466313"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass

        raise RuntimeError("OPENROUTER_API_KEY not set")

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

    def _fetch_programs_to_research(self, limit: int = 100) -> list[Program]:
        """Fetch programs that need research."""
        import psycopg

        db_url = self._get_db_url()

        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT p.id, p.name, p.domain, r.extracted
                    FROM affiliate_wiki.programs p
                    LEFT JOIN affiliate_wiki.program_research r ON r.program_id = p.id
                    WHERE p.domain IS NOT NULL
                      AND (r.extracted IS NULL OR r.extracted->>'deep_researched_at' IS NULL)
                      AND (r.status IS NULL OR r.status IN ('pending', 'success', 'needs_search'))
                    ORDER BY p.id ASC
                    LIMIT %s
                """, (limit,))

                programs = []
                for row in cur.fetchall():
                    programs.append(Program(
                        id=row[0],
                        name=row[1],
                        domain=row[2],
                        current_extracted=row[3] or {}
                    ))

                return programs

    def _fetch_program(self, program_id: int) -> Program | None:
        """Fetch a single program by ID."""
        import psycopg

        db_url = self._get_db_url()

        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT p.id, p.name, p.domain, r.extracted
                    FROM affiliate_wiki.programs p
                    LEFT JOIN affiliate_wiki.program_research r ON r.program_id = p.id
                    WHERE p.id = %s
                """, (program_id,))

                row = cur.fetchone()
                if not row:
                    return None

                return Program(
                    id=row[0],
                    name=row[1],
                    domain=row[2],
                    current_extracted=row[3] or {}
                )

    def _call_llm(self, prompt: str) -> tuple[str, str]:
        """Call LLM via OpenRouter. Returns (response_text, model_used)."""
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.openrouter_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are an affiliate marketing research assistant. Extract specific, structured data about affiliate programs. Be precise and factual. If information is not available, say so clearly."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 2048,
                "temperature": 0.3,
            },
            timeout=120
        )

        if response.status_code == 429:
            raise Exception("Rate limited by OpenRouter")

        response.raise_for_status()
        data = response.json()

        text = data["choices"][0]["message"]["content"]
        model = data.get("model", self.model)

        return text, model

    def _parse_response(self, text: str) -> dict:
        """Parse structured LLM response into field dict."""
        fields = {}

        # Check for NO_PROGRAM
        no_program_match = re.search(r"NO_PROGRAM:\s*(.+)", text, re.IGNORECASE)
        if no_program_match:
            return {"_no_program": True, "_no_program_reason": no_program_match.group(1).strip()}

        # Parse each field
        patterns = {
            "commission_rate": r"COMMISSION:\s*(.+?)(?:\n|$)",
            "cookie_duration_days": r"COOKIE_DAYS:\s*(\d+)",
            "payout_model": r"PAYOUT_MODEL:\s*(.+?)(?:\n|$)",
            "minimum_payout": r"MINIMUM_PAYOUT:\s*(.+?)(?:\n|$)",
            "payment_methods": r"PAYMENT_METHODS:\s*(.+?)(?:\n|$)",
            "payment_frequency": r"PAYMENT_FREQUENCY:\s*(.+?)(?:\n|$)",
            "tracking_platform": r"TRACKING_PLATFORM:\s*(.+?)(?:\n|$)",
            "requirements": r"REQUIREMENTS:\s*(.+?)(?:\n|$)",
            "restrictions": r"RESTRICTIONS:\s*(.+?)(?:\n|$)",
            "signup_url": r"SIGNUP_URL:\s*(https?://[^\s]+)",
            "languages": r"LANGUAGES:\s*(.+?)(?:\n|$)",
            "countries": r"COUNTRIES:\s*(.+?)(?:\n|$)",
            "regional_links": r"REGIONAL_LINKS:\s*(\{.+?\}|\[.+?\]|None)",
        }

        for field, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                value = match.group(1).strip()
                if value.lower() not in ("unknown", "none", "n/a", ""):
                    # Parse cookie days as int
                    if field == "cookie_duration_days":
                        try:
                            fields[field] = int(value)
                        except ValueError:
                            pass
                    # Parse regional links as JSON
                    elif field == "regional_links":
                        try:
                            fields[field] = json.loads(value)
                        except json.JSONDecodeError:
                            pass
                    # Parse comma-separated lists
                    elif field in ("payment_methods", "languages", "countries"):
                        items = [x.strip() for x in re.split(r"[,;]", value) if x.strip()]
                        if items:
                            fields[field] = items
                    else:
                        fields[field] = value

        return fields

    def _compute_diff(self, current: dict, new: dict) -> dict:
        """Compute which fields changed."""
        changes = {}
        for field, new_value in new.items():
            if field.startswith("_"):
                continue  # Skip internal fields
            current_value = current.get(field)
            if current_value != new_value:
                changes[field] = new_value
        return changes

    def research_program(self, program_id: int) -> ResearchResult | None:
        """
        Research a single program and return result.

        Does NOT submit to API - call submit_proposal() separately.
        """
        program = self._fetch_program(program_id)
        if not program:
            return None

        if not program.domain:
            return ResearchResult(
                program_id=program_id,
                changes={},
                sources=[],
                reasoning="Program has no domain",
                raw_response="",
                model_used="",
                error="No domain"
            )

        try:
            # Build prompt
            prompt = RESEARCH_PROMPT.format(name=program.name, domain=program.domain)

            # Call LLM
            response_text, model_used = self._call_llm(prompt)

            # Parse response
            parsed = self._parse_response(response_text)

            # Check for NO_PROGRAM
            if parsed.get("_no_program"):
                return ResearchResult(
                    program_id=program_id,
                    changes={"_no_program": True, "_no_program_reason": parsed.get("_no_program_reason")},
                    sources=[],
                    reasoning=f"No affiliate program: {parsed.get('_no_program_reason')}",
                    raw_response=response_text[:5000],
                    model_used=model_used,
                    no_program=True
                )

            # Compute changes
            changes = self._compute_diff(program.current_extracted or {}, parsed)

            # Add timestamp
            if changes:
                from datetime import datetime, timezone
                changes["deep_researched_at"] = datetime.now(timezone.utc).isoformat()

            return ResearchResult(
                program_id=program_id,
                changes=changes,
                sources=[{"url": f"https://{program.domain}", "type": "primary_domain"}],
                reasoning=f"Research update for {program.name} ({program.domain})",
                raw_response=response_text[:5000],
                model_used=model_used
            )

        except Exception as e:
            return ResearchResult(
                program_id=program_id,
                changes={},
                sources=[],
                reasoning="",
                raw_response="",
                model_used="",
                error=str(e)
            )

    def submit_proposal(self, result: ResearchResult) -> dict | None:
        """Submit research result as proposal to editorial API."""
        if not result.changes or result.error:
            return None

        try:
            response = requests.post(
                f"{self.api_base}/editorial/proposals",
                headers={
                    "X-Agent-Key": self.agent_key,
                    "Content-Type": "application/json",
                },
                json={
                    "entity_type": "program",
                    "entity_id": result.program_id,
                    "changes": result.changes,
                    "sources": result.sources,
                    "reasoning": result.reasoning,
                    "raw_llm_response": result.raw_response,
                    "model_used": result.model_used,
                },
                timeout=30
            )

            if response.status_code == 201 or response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to submit proposal: {response.status_code} {response.text}")
                return None

        except Exception as e:
            print(f"Error submitting proposal: {e}")
            return None

    def research_and_submit(self, program_id: int) -> dict | None:
        """Research a program and submit proposal in one call."""
        result = self.research_program(program_id)
        if result and result.changes and not result.error:
            return self.submit_proposal(result)
        return None

    def research_batch(
        self,
        limit: int = 100,
        workers: int = 5,
        submit: bool = True
    ) -> list[ResearchResult]:
        """
        Research multiple programs in parallel.

        Args:
            limit: Maximum number of programs to research
            workers: Number of parallel workers
            submit: Whether to submit proposals after research

        Returns:
            List of research results
        """
        programs = self._fetch_programs_to_research(limit)
        print(f"Found {len(programs)} programs to research")

        results = []
        submitted = 0
        errors = 0

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(self.research_program, p.id): p
                for p in programs
            }

            for future in as_completed(futures):
                program = futures[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)

                        if result.error:
                            errors += 1
                            print(f"  ✗ {program.name}: {result.error}")
                        elif result.no_program:
                            print(f"  - {program.name}: No affiliate program")
                        elif result.changes:
                            print(f"  ✓ {program.name}: {len(result.changes)} changes")

                            if submit:
                                proposal = self.submit_proposal(result)
                                if proposal:
                                    submitted += 1

                except Exception as e:
                    errors += 1
                    print(f"  ✗ {program.name}: {e}")

        print(f"\nResearch complete: {len(results)} total, {submitted} submitted, {errors} errors")
        return results


# CLI
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Editorial Researcher Agent")
    parser.add_argument("--program-id", type=int, help="Research specific program ID")
    parser.add_argument("--batch", type=int, default=0, help="Research batch of N programs")
    parser.add_argument("--workers", type=int, default=5, help="Parallel workers for batch")
    parser.add_argument("--no-submit", action="store_true", help="Don't submit proposals")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE, help="API base URL")
    parser.add_argument("--agent-key", default=DEFAULT_AGENT_KEY, help="Agent API key")
    parser.add_argument("--model", default="kimi-k2", help="LLM model to use")

    args = parser.parse_args()

    researcher = EditorialResearcher(
        api_base=args.api_base,
        agent_key=args.agent_key,
        model=args.model
    )

    if args.program_id:
        print(f"Researching program {args.program_id}...")
        result = researcher.research_program(args.program_id)

        if result:
            if result.error:
                print(f"Error: {result.error}")
            elif result.no_program:
                print(f"No affiliate program: {result.reasoning}")
            else:
                print(f"Changes found: {json.dumps(result.changes, indent=2)}")

                if not args.no_submit:
                    proposal = researcher.submit_proposal(result)
                    if proposal:
                        print(f"Submitted proposal: {proposal['proposal_id']}")

    elif args.batch > 0:
        print(f"Running batch research for {args.batch} programs...")
        results = researcher.research_batch(
            limit=args.batch,
            workers=args.workers,
            submit=not args.no_submit
        )

    else:
        parser.print_help()
