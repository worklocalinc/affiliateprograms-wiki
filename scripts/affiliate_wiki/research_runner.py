#!/usr/bin/env python3
"""
Affiliate Wiki Research Runner (Stage C/D-lite)

Goal:
  For each program (from Skimlinks seed list), discover likely public pages for:
    - affiliate program
    - partner program
    - referral program

This runner is intentionally conservative:
  - No brute-force crawling
  - No search engine dependency
  Uses heuristic URL probing on the program's primary domain and simple HTML link extraction.

Writes results into:
  - affiliate_wiki.program_research.status
  - affiliate_wiki.program_research.extracted (JSON)
  - affiliate_wiki.program_research.evidence (JSON)
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin

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
HREF_RE = re.compile(r'href=[\"\\\']([^\"\\\']+)[\"\\\']', re.I)


@dataclass(frozen=True)
class Program:
    id: int
    name: str
    domain: str | None
    extracted: dict[str, Any] | None


def _normalize_domain(domain: str) -> str:
    d = domain.strip().lower()
    d = d.removeprefix("http://").removeprefix("https://")
    d = d.split("/")[0]
    d = d.removeprefix("www.")
    return d


def _candidate_urls(domain: str) -> list[str]:
    base = f"https://{domain}/"
    paths = [
        "affiliate",
        "affiliates",
        "affiliate-program",
        "affiliate-programs",
        "partners",
        "partner",
        "partner-program",
        "partnerships",
        "referral",
        "referrals",
        "refer",
        "refer-a-friend",
        "ambassador",
        "influencer",
    ]
    return [urljoin(base, p) for p in paths] + [base]


def _fetch(session: requests.Session, url: str, timeout_s: int) -> dict[str, Any]:
    try:
        r = session.get(
            url,
            timeout=timeout_s,
            allow_redirects=True,
            headers={
                "user-agent": "affiliate-wiki-bot/0.1 (+contact: ops@local)",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        text = r.text if ("text/html" in (r.headers.get("content-type") or "")) else ""
        return {
            "ok": True,
            "url": url,
            "final_url": str(r.url),
            "status": r.status_code,
            "content_type": r.headers.get("content-type"),
            "redirect_chain": [str(h.url) for h in r.history] + ([str(r.url)] if r.history else []),
            "html_snippet": text[:5000] if text else "",
        }
    except Exception as e:
        return {"ok": False, "url": url, "error": str(e)}


def _extract_link_candidates(html_snippet: str, base_url: str, limit: int = 50) -> list[str]:
    out: list[str] = []
    for m in HREF_RE.finditer(html_snippet):
        href = m.group(1)
        if href.startswith("#") or href.startswith("mailto:") or href.startswith("javascript:"):
            continue
        abs_url = urljoin(base_url, href)
        if AFFILIATE_HINT_RE.search(abs_url):
            out.append(abs_url)
        if len(out) >= limit:
            break
    seen = set()
    uniq = []
    for u in out:
        if u in seen:
            continue
        seen.add(u)
        uniq.append(u)
    return uniq


def _score_result(result: dict[str, Any]) -> int:
    if not result.get("ok"):
        return -10
    status = int(result.get("status") or 0)
    if status >= 500:
        return -5
    if status == 404:
        return -4
    if status in (401, 403):
        return -2
    if status in (200, 201, 202):
        score = 5
    elif 300 <= status < 400:
        score = 2
    else:
        score = 0

    final_url = (result.get("final_url") or "").lower()
    if AFFILIATE_HINT_RE.search(final_url):
        score += 3
    return score


def pick_best(evidence: list[dict[str, Any]]) -> dict[str, Any] | None:
    scored = [(_score_result(r), r) for r in evidence]
    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best = scored[0] if scored else (-999, None)
    if best is None or best_score < 1:
        return None
    return best


def fetch_pending_programs(psycopg, db_url: str, limit: int) -> list[Program]:
    sql = """
      select p.id, p.name, p.domain, r.extracted
      from affiliate_wiki.program_research r
      join affiliate_wiki.programs p on p.id = r.program_id
      where r.status = 'pending'
      order by p.id asc
      limit %s
    """
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (limit,))
            rows = cur.fetchall()
    out: list[Program] = []
    for r in rows:
        extracted = r[3] if isinstance(r[3], dict) else None
        out.append(Program(id=int(r[0]), name=str(r[1]), domain=(str(r[2]) if r[2] else None), extracted=extracted))
    return out


def update_research(
    psycopg,
    db_url: str,
    program_id: int,
    status: str,
    extracted: dict[str, Any],
    evidence: list[dict[str, Any]],
    error: str | None = None,
) -> None:
    from psycopg.types.json import Json  # type: ignore

    sql = """
      update affiliate_wiki.program_research
      set status = %s,
          last_attempt_at = now(),
          last_success_at = case when %s = 'success' then now() else last_success_at end,
          error = %s,
          extracted = %s,
          evidence = %s
      where program_id = %s
    """
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (status, status, error, Json(extracted), Json(evidence), program_id))
        conn.commit()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db-url", default=os.environ.get("DATABASE_URL", ""))
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--timeout", type=int, default=8)
    ap.add_argument("--sleep", type=float, default=0.05)
    ap.add_argument("--max-probes", type=int, default=5, help="Max URL probes per program (common paths).")
    ap.add_argument("--max-link-probes", type=int, default=2, help="Max homepage link probes per program.")
    args = ap.parse_args()

    if not args.db_url:
        _eprint("DATABASE_URL not set (or pass --db-url).")
        return 2

    psycopg = _must_import_psycopg()
    programs = fetch_pending_programs(psycopg, args.db_url, args.limit)
    if not programs:
        print("No pending programs.")
        return 0

    session = requests.Session()

    done = 0
    for p in programs:
        done += 1
        # If search discovery provided a best_url, probe it first (even if it’s off-domain).
        forced_url = None
        if p.extracted and isinstance(p.extracted, dict):
            v = p.extracted.get("best_url")
            if isinstance(v, str) and v:
                forced_url = v

        if not p.domain and not forced_url:
            update_research(psycopg, args.db_url, p.id, "skipped", {"reason": "missing_domain"}, [], error="missing domain")
            continue

        domain = _normalize_domain(p.domain) if p.domain else ""
        evidence: list[dict[str, Any]] = []

        if forced_url:
            res = _fetch(session, forced_url, args.timeout)
            evidence.append(res)
            time.sleep(max(0.0, args.sleep))

        for url in _candidate_urls(domain)[: max(1, args.max_probes)]:
            res = _fetch(session, url, args.timeout)
            evidence.append(res)
            if _score_result(res) >= 8:
                break
            time.sleep(max(0.0, args.sleep))

        homepage = next(
            (e for e in evidence if e.get("ok") and str(e.get("final_url", "")).startswith(f"https://{domain}")),
            None,
        )
        if homepage and homepage.get("html_snippet"):
            link_candidates = _extract_link_candidates(
                str(homepage["html_snippet"]),
                str(homepage.get("final_url") or homepage.get("url")),
            )
            for url in link_candidates[: max(0, args.max_link_probes)]:
                res = _fetch(session, url, args.timeout)
                evidence.append(res)
                if _score_result(res) >= 8:
                    break
                time.sleep(max(0.0, args.sleep))

        best = pick_best(evidence)
        if not best:
            update_research(
                psycopg,
                args.db_url,
                p.id,
                "needs_search",
                {"domain": domain, "candidates_tested": len(evidence)},
                evidence,
                error="no strong affiliate/partner/referral page detected",
            )
        else:
            update_research(
                psycopg,
                args.db_url,
                p.id,
                "success",
                {
                    "domain": domain,
                    "best_url": best.get("final_url") or best.get("url"),
                    "best_status": best.get("status"),
                    "candidates_tested": len(evidence),
                },
                evidence,
                error=None,
            )

        if done % 10 == 0:
            _eprint(f"Processed {done}/{len(programs)}")

    print(f"Processed {done} programs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
