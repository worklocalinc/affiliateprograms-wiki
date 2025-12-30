#!/usr/bin/env python3
"""
Stage C (cheap): discover likely official affiliate/partner pages via DuckDuckGo HTML.

This is a pragmatic bridge to get better URLs than probing common paths.
It:
  - takes programs in `status='needs_search'`
  - searches DDG for "{brand} affiliate program"
  - chooses a candidate URL (prefers same-domain + affiliate-ish paths)
  - stores it in `program_research.extracted.best_url`
  - resets status to 'pending' so `research_runner.py` will fetch it

Usage:
  export DATABASE_URL="postgresql://.../db?sslmode=require"
  affiliateprograms-wiki/scripts/affiliate_wiki/.venv/bin/python \
    affiliateprograms-wiki/scripts/affiliate_wiki/discover_program_pages_ddg.py \
    --db-url "$DATABASE_URL" \
    --limit 25
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse, unquote

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


HREF_RE = re.compile(r'href="([^"]+)"', re.I)
AFFILIATE_HINT_RE = re.compile(r"(affiliate|affiliates|partner|partners|referral|refer-a-friend)", re.I)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _normalize_domain(domain: str) -> str:
    d = domain.strip().lower()
    d = d.removeprefix("http://").removeprefix("https://")
    d = d.split("/")[0]
    d = d.removeprefix("www.")
    return d


def _ddg_search_html(query: str, timeout_s: int) -> str:
    # DuckDuckGo HTML endpoint (simple, no JS)
    url = "https://duckduckgo.com/html/"
    r = requests.get(
        url,
        params={"q": query},
        timeout=timeout_s,
        headers={
            "user-agent": "affiliate-wiki-bot/0.1 (+contact: ops@local)",
            "accept": "text/html",
        },
    )
    r.raise_for_status()
    return r.text


def _extract_result_urls(html: str, limit: int = 10) -> list[str]:
    urls: list[str] = []
    for m in HREF_RE.finditer(html):
        href = m.group(1)
        # DDG wraps results as /l/?uddg=<encoded>
        if "duckduckgo.com/l/?" in href and "uddg=" in href:
            parsed = urlparse(href)
            qs = parsed.query or ""
            for part in qs.split("&"):
                if part.startswith("uddg="):
                    target = unquote(part.split("=", 1)[1])
                    urls.append(target)
                    break
        elif href.startswith("http"):
            urls.append(href)
        if len(urls) >= limit:
            break
    # de-dupe preserve order
    seen = set()
    out = []
    for u in urls:
        if u in seen:
            continue
        seen.add(u)
        out.append(u)
    return out


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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db-url", default=os.environ.get("DATABASE_URL", ""))
    ap.add_argument("--limit", type=int, default=25)
    ap.add_argument("--sleep", type=float, default=1.0)
    ap.add_argument("--timeout", type=int, default=20)
    args = ap.parse_args()

    if not args.db_url:
        _eprint("DATABASE_URL not set (or pass --db-url).")
        return 2

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

    with psycopg.connect(args.db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(fetch_sql, (args.limit,))
            rows = cur.fetchall()

            for program_id, name, domain, extracted in rows:
                processed += 1
                query = f"{name} affiliate program"
                try:
                    html = _ddg_search_html(query, timeout_s=args.timeout)
                    urls = _extract_result_urls(html, limit=12)
                    best = _choose_best(urls, domain)
                except Exception as e:
                    best = None
                    urls = []
                    _eprint(f"DDG failed for {name}: {e}")

                if not best:
                    time.sleep(max(0.0, args.sleep))
                    continue

                extracted_dict = extracted if isinstance(extracted, dict) else None
                patch = {
                    "best_url": best,
                    "discovery": {
                        "engine": "ddg-html",
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
