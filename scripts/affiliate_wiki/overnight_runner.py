#!/usr/bin/env python3
"""
Overnight AffiliatePrograms.wiki pipeline runner.

Runs in an infinite loop with backoff and checkpoints in the DB:
  - Discover better URLs for needs_search (Brave Search API)
  - Research pending programs (fetch + evidence capture)
  - Extract basic fields from success programs (refetch + regex extraction)

This is designed to be run under nohup/tmux/systemd and to survive restarts.

Usage:
  source ~/ai-shared/secrets/.env
  export DATABASE_URL="$(gcloud secrets versions access latest --secret=database_url_affiliate_wiki --project superapp-466313)"
  affiliateprograms-wiki/scripts/affiliate_wiki/.venv/bin/python \
    affiliateprograms-wiki/scripts/affiliate_wiki/overnight_runner.py
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import psycopg


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _eprint(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def _run(cmd: list[str], env: dict[str, str]) -> int:
    # Avoid leaking secrets (DB URLs / API keys) in logs.
    _eprint(f"[{_now()}] $ {cmd[0]} {cmd[1]}")
    p = subprocess.run(cmd, env=env, check=False)
    return int(p.returncode)


def _counts(db_url: str) -> dict[str, int]:
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select
                  (select count(*) from affiliate_wiki.programs) as programs,
                  (select count(*) from affiliate_wiki.program_research where status='pending') as pending,
                  (select count(*) from affiliate_wiki.program_research where status='success') as success,
                  (select count(*) from affiliate_wiki.program_research where status='needs_search') as needs_search
                """
            )
            row = cur.fetchone()
    return {"programs": int(row[0]), "pending": int(row[1]), "success": int(row[2]), "needs_search": int(row[3])}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db-url", default=os.environ.get("DATABASE_URL", ""))
    ap.add_argument("--brave-api-key", default=os.environ.get("BRAVE_API_KEY", ""))
    ap.add_argument("--sleep", type=float, default=10.0, help="Sleep between cycles (seconds).")
    ap.add_argument("--discover-batch", type=int, default=20)
    ap.add_argument("--research-batch", type=int, default=50)
    ap.add_argument("--extract-batch", type=int, default=200)
    args = ap.parse_args()

    if not args.db_url:
        _eprint("Missing DATABASE_URL")
        return 2
    if not args.brave_api_key:
        _eprint("Missing BRAVE_API_KEY")
        return 2

    root = Path(__file__).resolve().parent
    env = dict(os.environ)
    env["DATABASE_URL"] = args.db_url
    env["BRAVE_API_KEY"] = args.brave_api_key

    discover = str(root / "discover_program_pages_brave.py")
    research = str(root / "research_runner.py")
    extract = str(root / "extract_program_fields.py")

    backoff = 5.0

    while True:
        try:
            c = _counts(args.db_url)
            _eprint(f"[{_now()}] counts: {c}")

            if c["needs_search"] > 0:
                rc = _run(
                    [
                        sys.executable,
                        discover,
                        "--limit",
                        str(args.discover_batch),
                        "--sleep",
                        "1.5",
                    ],
                    env=env,
                )
                if rc != 0:
                    _eprint(f"[{_now()}] discover failed rc={rc}")

            if c["pending"] > 0:
                rc = _run(
                    [
                        sys.executable,
                        research,
                        "--limit",
                        str(args.research_batch),
                        "--timeout",
                        "8",
                        "--max-probes",
                        "5",
                        "--max-link-probes",
                        "2",
                        "--sleep",
                        "0.05",
                    ],
                    env=env,
                )
                if rc != 0:
                    _eprint(f"[{_now()}] research failed rc={rc}")

            if c["success"] > 0:
                rc = _run(
                    [
                        sys.executable,
                        extract,
                        "--only-status",
                        "success",
                        "--limit",
                        str(args.extract_batch),
                        "--refetch",
                    ],
                    env=env,
                )
                if rc != 0:
                    _eprint(f"[{_now()}] extract failed rc={rc}")

            backoff = 5.0
            time.sleep(max(0.0, args.sleep))
        except KeyboardInterrupt:
            _eprint("Exiting (KeyboardInterrupt)")
            return 0
        except Exception as e:
            _eprint(f"[{_now()}] loop error: {e}")
            time.sleep(backoff)
            backoff = min(300.0, backoff * 2)


if __name__ == "__main__":
    raise SystemExit(main())
