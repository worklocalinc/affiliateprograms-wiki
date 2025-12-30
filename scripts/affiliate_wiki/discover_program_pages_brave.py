#!/usr/bin/env python3
"""
Stage C (cheap, robust): discover likely official affiliate/partner pages via Brave Search API.

This is the preferred discovery method (DDG HTML often returns 202 without results).

Behavior:
  - pulls programs in `status='needs_search'`
  - searches Brave for "{brand} affiliate program"
  - chooses a candidate URL (prefers same-domain + affiliate-ish paths)
  - stores it in `program_research.extracted.best_url` + discovery metadata
  - resets status to 'pending' so `research_runner.py` will fetch it

Requires:
  - BRAVE_API_KEY (from ~/ai-shared/secrets/.env)
  - Optional fallback: GOOGLE_PSE_API_KEY + GOOGLE_PSE_ENGINE_ID (Google Programmable Search Engine)

Usage:
  export DATABASE_URL="postgresql://.../db?sslmode=require"
  export BRAVE_API_KEY="..."
  export GOOGLE_PSE_API_KEY="..."
  export GOOGLE_PSE_ENGINE_ID="..."
  affiliateprograms-wiki/scripts/affiliate_wiki/.venv/bin/python \
    affiliateprograms-wiki/scripts/affiliate_wiki/discover_program_pages_brave.py \
    --db-url "$DATABASE_URL" \
    --limit 50
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import requests


def _eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


def _must_import_psycopg():
    try:
        import psycopg  # type: ignore

        return psycopg
    except Exception as e:
        _eprint("Missing dependency: psycopg[binary]")
        _eprint("Install with:")
        _eprint("  bash affiliateprograms-wiki/scripts/affiliate_wiki/bootstrap_venv.sh")
        raise SystemExit(2) from e


AFFILIATE_HINT_RE = re.compile(r"(affiliate|affiliates|partner|partners|referral|refer-a-friend)", re.I)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _normalize_domain(domain: str) -> str:
    d = domain.strip().lower()
    d = d.removeprefix("http://").removeprefix("https://")
    d = d.split("/")[0]
    d = d.removeprefix("www.")
    return d


def _score_url(url: str, domain: str | None) -> int:
    u = url.lower()
    score = 0
    if AFFILIATE_HINT_RE.search(u):
        score += 5
    if domain:
        nd = _normalize_domain(domain)
        try:
            host = (urlparse(url).hostname or "").lower().removeprefix("www.")
        except Exception:
            host = ""
        if host == nd or host.endswith("." + nd):
            score += 4
    if "terms" in u or "policy" in u:
        score += 1
    if "login" in u or "signup" in u:
        score += 1
    return score


def _choose_best(urls: list[str], domain: str | None) -> str | None:
    if not urls:
        return None
    scored = sorted(((_score_url(u, domain), u) for u in urls), key=lambda x: x[0], reverse=True)
    best_score, best = scored[0]
    if best_score < 3:
        return None
    return best


def merge_extracted(existing: dict[str, Any] | None, patch: dict[str, Any]) -> dict[str, Any]:
    out = dict(existing or {})
    out.update(patch)
    return out


def _maybe_load_google_pse_from_gcloud() -> tuple[str, str]:
    gcloud = "/home/skynet/google-cloud-sdk/bin/gcloud"
    project = "superapp-466313"

    def _read(secret_name: str) -> str:
        p = subprocess.run(
            [gcloud, "secrets", "versions", "access", "latest", f"--secret={secret_name}", f"--project={project}"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return (p.stdout or "").strip() if p.returncode == 0 else ""

    api_key = _read("GOOGLE_PSE_API_KEY")
    engine_id = _read("GOOGLE_PSE_ENGINE_ID")
    return api_key, engine_id


def brave_search(api_key: str, query: str, count: int, timeout_s: int) -> list[str]:
    r = requests.get(
        "https://api.search.brave.com/res/v1/web/search",
        params={"q": query, "count": count, "safesearch": "moderate", "text_decorations": "false"},
        headers={
            "accept": "application/json",
            "x-subscription-token": api_key,
            "user-agent": "affiliate-wiki-bot/0.1 (+contact: ops@local)",
        },
        timeout=timeout_s,
    )
    if r.status_code == 429:
        retry_after = r.headers.get("retry-after") or ""
        raise RuntimeError(f"rate_limited_429 retry_after={retry_after}".strip())
    r.raise_for_status()
    data = r.json()
    web = (data.get("web") or {}).get("results") or []
    urls: list[str] = []
    for item in web:
        url = item.get("url")
        if isinstance(url, str) and url.startswith("http"):
            urls.append(url)
    # de-dupe preserve order
    seen = set()
    out = []
    for u in urls:
        if u in seen:
            continue
        seen.add(u)
        out.append(u)
    return out


def google_search(api_key: str, engine_id: str, query: str, count: int, timeout_s: int) -> list[str]:
    # Google Custom Search JSON API (Programmable Search Engine)
    # https://developers.google.com/custom-search/v1/using_rest
    num = max(1, min(10, int(count)))
    r = requests.get(
        "https://www.googleapis.com/customsearch/v1",
        params={"q": query, "key": api_key, "cx": engine_id, "num": num, "safe": "active"},
        headers={"user-agent": "affiliate-wiki-bot/0.1 (+contact: ops@local)"},
        timeout=timeout_s,
    )
    r.raise_for_status()
    data = r.json()
    items = data.get("items") or []
    urls: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        url = item.get("link")
        if isinstance(url, str) and url.startswith("http"):
            urls.append(url)
    # de-dupe preserve order
    seen = set()
    out = []
    for u in urls:
        if u in seen:
            continue
        seen.add(u)
        out.append(u)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db-url", default=os.environ.get("DATABASE_URL", ""))
    ap.add_argument("--brave-api-key", default=os.environ.get("BRAVE_API_KEY", ""))
    ap.add_argument("--google-api-key", default=os.environ.get("GOOGLE_PSE_API_KEY", ""))
    ap.add_argument("--google-engine-id", default=os.environ.get("GOOGLE_PSE_ENGINE_ID", ""))
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--sleep", type=float, default=1.5)
    ap.add_argument("--timeout", type=int, default=25)
    ap.add_argument("--results", type=int, default=10)
    args = ap.parse_args()

    if not args.db_url:
        _eprint("DATABASE_URL not set (or pass --db-url).")
        return 2
    if not args.brave_api_key:
        _eprint("BRAVE_API_KEY not set (or pass --brave-api-key).")
        return 2

    google_ready = bool(args.google_api_key and args.google_engine_id)

    psycopg = _must_import_psycopg()
    from psycopg.types.json import Json  # type: ignore

    fetch_sql = """
      select r.program_id, p.name, p.domain, r.extracted
      from affiliate_wiki.program_research r
      join affiliate_wiki.programs p on p.id = r.program_id
      where r.status = 'needs_search'
      order by coalesce(r.last_attempt_at, r.last_success_at) desc nulls last, r.program_id asc
      limit %s
    """

    update_sql = """
      update affiliate_wiki.program_research
      set status = 'pending',
          error = null,
          extracted = %s
      where program_id = %s
    """

    processed = 0
    updated = 0
    use_google_only = False

    with psycopg.connect(args.db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(fetch_sql, (args.limit,))
            rows = cur.fetchall()

            for program_id, name, domain, extracted in rows:
                processed += 1
                query = f"{name} affiliate program"
                best = None
                urls: list[str] = []
                engine = "brave"

                if not use_google_only:
                    try:
                        urls = brave_search(args.brave_api_key, query, count=args.results, timeout_s=args.timeout)
                        best = _choose_best(urls, domain)
                    except Exception as e:
                        _eprint(f"Brave search failed for {name}: {e}")
                        if "rate_limited_429" in str(e):
                            if not google_ready:
                                api_key, engine_id = _maybe_load_google_pse_from_gcloud()
                                if api_key and engine_id:
                                    args.google_api_key = api_key
                                    args.google_engine_id = engine_id
                                    google_ready = True

                            if google_ready:
                                _eprint("Brave is rate-limited; switching discovery to Google PSE for this run.")
                                use_google_only = True
                            else:
                                _eprint(
                                    "Google PSE fallback not configured (set GOOGLE_PSE_API_KEY + GOOGLE_PSE_ENGINE_ID)."
                                )
                                time.sleep(60)
                                return 4

                if use_google_only:
                    engine = "google_pse"
                    try:
                        urls = google_search(
                            args.google_api_key, args.google_engine_id, query, count=args.results, timeout_s=args.timeout
                        )
                        best = _choose_best(urls, domain)
                    except Exception as e:
                        _eprint(f"Google search failed for {name}: {e}")
                        best = None
                        urls = []

                if not best:
                    time.sleep(max(0.0, args.sleep))
                    continue

                extracted_dict = extracted if isinstance(extracted, dict) else None
                patch = {
                    "best_url": best,
                    "discovery": {
                        "engine": engine,
                        "query": query,
                        "candidate_urls": urls[:10],
                        "chosen_url": best,
                        "discovered_at": _now_iso(),
                    },
                }
                merged = merge_extracted(extracted_dict, patch)
                cur.execute(update_sql, (Json(merged), int(program_id)))
                updated += 1

                time.sleep(max(0.0, args.sleep))

        conn.commit()

    print(f"Processed: {processed}, updated: {updated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
