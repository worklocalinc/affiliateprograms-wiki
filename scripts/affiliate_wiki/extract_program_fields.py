#!/usr/bin/env python3
"""
Extract structured fields from program research evidence (Stage E-lite).

This is a first-pass deterministic extractor that looks for common patterns in the
`html_snippet` captured by `research_runner.py`.

Writes back into:
  affiliate_wiki.program_research.extracted

Usage:
  export DATABASE_URL="postgresql://.../db?sslmode=require"
  affiliateprograms-wiki/scripts/affiliate_wiki/.venv/bin/python \
    affiliateprograms-wiki/scripts/affiliate_wiki/extract_program_fields.py \
    --db-url "$DATABASE_URL" \
    --limit 200
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

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


COOKIE_RE = re.compile(r"(cookie(?:\s+length|\s+duration)?)[^\d]{0,120}(\d{1,3})\s*(day|days|hour|hours)", re.I)
PAYOUT_MODEL_RE = re.compile(r"\b(recurring|rev\s*share|revenue\s*share|cpa|cpl|cpc|cps)\b", re.I)

# Rough "commission" patterns; kept conservative.
PERCENT_RE = re.compile(r"(\d{1,3}(?:\.\d+)?)\s*%", re.I)
DOLLAR_RE = re.compile(r"\$\s*(\d{1,6}(?:\.\d{1,2})?)", re.I)
EARN_UP_TO_RE = re.compile(r"earn\s+up\s+to[^%]{0,40}(\d{1,3}(?:\.\d+)?)\s*%", re.I)
PERCENT_CONTEXT_RE = re.compile(r"(\d{1,3}(?:\.\d+)?)\s*%[^\n]{0,40}(commission|rev\s*share|revenue\s*share)", re.I)
KEYWORD_RE = re.compile(r"\b(commission|commissions|payout|earn|earning|rate)\b", re.I)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _pick_best_html(extracted: dict[str, Any] | None, evidence: list[dict[str, Any]]) -> tuple[str | None, str]:
    if not evidence:
        return None, ""

    best_url = None
    if extracted and isinstance(extracted, dict):
        v = extracted.get("best_url")
        if isinstance(v, str) and v:
            best_url = v

    # Prefer evidence item matching best_url; else pick first "ok" item with html_snippet.
    if best_url:
        for e in evidence:
            if not isinstance(e, dict):
                continue
            if e.get("final_url") == best_url or e.get("url") == best_url:
                snippet = str(e.get("html_snippet") or "")
                if snippet:
                    return best_url, snippet

    for e in evidence:
        if not isinstance(e, dict):
            continue
        if not e.get("ok"):
            continue
        snippet = str(e.get("html_snippet") or "")
        if snippet:
            return str(e.get("final_url") or e.get("url") or ""), snippet

    return None, ""


def _extract_cookie_days(text: str) -> tuple[int | None, float]:
    m = COOKIE_RE.search(text)
    if not m:
        return None, 0.0
    n = int(m.group(2))
    unit = m.group(3).lower()
    if "hour" in unit:
        # Convert hours to days conservatively.
        days = max(1, round(n / 24))
        return days, 0.55
    return n, 0.7


def _extract_payout_models(text: str) -> tuple[list[str], float]:
    hits = {h.lower().replace(" ", "") for h in PAYOUT_MODEL_RE.findall(text)}
    out: list[str] = []
    score = 0.0
    if any("recurring" in h for h in hits):
        out.append("Recurring")
        score = max(score, 0.6)
    if any("rev" in h or "revenue" in h for h in hits):
        out.append("RevShare")
        score = max(score, 0.6)
    if "cpa" in hits:
        out.append("CPA")
        score = max(score, 0.7)
    if "cpl" in hits:
        out.append("CPL")
        score = max(score, 0.7)
    if "cpc" in hits:
        out.append("CPC")
        score = max(score, 0.6)
    if "cps" in hits:
        out.append("CPS")
        score = max(score, 0.6)
    return out, score


def _extract_commission(text: str) -> tuple[str | None, float]:
    m = EARN_UP_TO_RE.search(text)
    if m:
        return f"{m.group(1)}%", 0.6
    m = PERCENT_CONTEXT_RE.search(text)
    if m:
        return f"{m.group(1)}%", 0.6
    # Windowed search around commission-ish keywords
    lower = text.lower()
    for km in KEYWORD_RE.finditer(lower):
        start = max(0, km.start() - 200)
        end = min(len(text), km.end() + 400)
        window = text[start:end]
        pm = PERCENT_RE.search(window)
        if pm:
            return f"{pm.group(1)}%", 0.55
        dm = DOLLAR_RE.search(window)
        if dm:
            return f"${dm.group(1)}", 0.5
    return None, 0.0


def merge_extracted(existing: dict[str, Any] | None, patch: dict[str, Any]) -> dict[str, Any]:
    out = dict(existing or {})
    out.update(patch)
    return out


@dataclass(frozen=True)
class FetchResult:
    ok: bool
    final_url: str
    status: int
    content_type: str
    text: str
    error: str | None = None


def _fetch_html(url: str, timeout_s: int, max_chars: int) -> FetchResult:
    try:
        r = requests.get(
            url,
            timeout=timeout_s,
            allow_redirects=True,
            headers={
                "user-agent": "affiliate-wiki-bot/0.1 (+contact: ops@local)",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        ct = (r.headers.get("content-type") or "").lower()
        text = r.text if "text/html" in ct else ""
        return FetchResult(
            ok=True,
            final_url=str(r.url),
            status=int(r.status_code),
            content_type=ct,
            text=(text[:max_chars] if text else ""),
        )
    except Exception as e:
        return FetchResult(ok=False, final_url=url, status=0, content_type="", text="", error=str(e))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db-url", default=os.environ.get("DATABASE_URL", ""))
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--only-status", default="success", help="Comma-separated: success,needs_search,pending")
    ap.add_argument("--refetch", action="store_true", help="Refetch best URL and parse full HTML (recommended).")
    ap.add_argument("--timeout", type=int, default=12)
    ap.add_argument("--max-html-chars", type=int, default=200_000)
    args = ap.parse_args()

    if not args.db_url:
        _eprint("DATABASE_URL not set (or pass --db-url).")
        return 2

    statuses = [s.strip() for s in args.only_status.split(",") if s.strip()]
    if not statuses:
        _eprint("No statuses specified")
        return 2

    psycopg = _must_import_psycopg()
    from psycopg.types.json import Json  # type: ignore

    fetch_sql = """
      select r.program_id, r.status, r.extracted, r.evidence, r.last_attempt_at
      from affiliate_wiki.program_research r
      where r.status = any(%s)
      order by coalesce(r.last_success_at, r.last_attempt_at) desc nulls last, r.program_id asc
      limit %s
    """

    update_sql = """
      update affiliate_wiki.program_research
      set extracted = %s
      where program_id = %s
    """

    processed = 0
    updated = 0

    with psycopg.connect(args.db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(fetch_sql, (statuses, args.limit))
            rows = cur.fetchall()

            for program_id, status, extracted, evidence, last_attempt_at in rows:
                processed += 1

                extracted_dict: dict[str, Any] | None = extracted if isinstance(extracted, dict) else None
                evidence_list: list[dict[str, Any]] = evidence if isinstance(evidence, list) else []

                best_url, html = _pick_best_html(extracted_dict, evidence_list)
                if args.refetch and best_url:
                    fr = _fetch_html(best_url, timeout_s=args.timeout, max_chars=args.max_html_chars)
                    if fr.ok and fr.text:
                        html = f"{html}\n\n{fr.text}"
                if not html:
                    continue

                cookie_days, cookie_conf = _extract_cookie_days(html)
                payout_models, payout_conf = _extract_payout_models(html)
                commission, commission_conf = _extract_commission(html)

                fields: dict[str, Any] = {}
                confidence: dict[str, float] = {}

                if best_url:
                    fields["affiliate_page_url"] = best_url
                    confidence["affiliate_page_url"] = 0.8
                if cookie_days is not None:
                    fields["cookie_length_days"] = cookie_days
                    confidence["cookie_length_days"] = cookie_conf
                if payout_models:
                    fields["payout_models"] = payout_models
                    confidence["payout_models"] = payout_conf
                if commission:
                    fields["commission"] = commission
                    confidence["commission"] = commission_conf

                if not fields:
                    continue

                patch = {
                    "fields": fields,
                    "fields_confidence": confidence,
                    "fields_source_url": best_url,
                    "fields_captured_at": (last_attempt_at.isoformat() if last_attempt_at else None),
                    "fields_refetch_enabled": bool(args.refetch),
                    "fields_extracted_at": _now_iso(),
                    "fields_extractor": "regex-v0",
                    "status_at_extraction": status,
                }

                merged = merge_extracted(extracted_dict, patch)
                cur.execute(update_sql, (Json(merged), int(program_id)))
                updated += 1

        conn.commit()

    print(f"Processed: {processed}, updated: {updated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
