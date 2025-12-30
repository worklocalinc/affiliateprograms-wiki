#!/usr/bin/env python3
"""
Ensure every program has a program_research row.

After loading seed programs, run:
  affiliateprograms-wiki/scripts/affiliate_wiki/.venv/bin/python \
    affiliateprograms-wiki/scripts/affiliate_wiki/init_research_queue.py \
    --db-url "$DATABASE_URL"
"""

from __future__ import annotations

import argparse
import os
import sys


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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db-url", default=os.environ.get("DATABASE_URL", ""))
    args = ap.parse_args()

    if not args.db_url:
        _eprint("DATABASE_URL not set (or pass --db-url).")
        return 2

    psycopg = _must_import_psycopg()

    sql = """
    INSERT INTO affiliate_wiki.program_research (program_id)
    SELECT p.id
    FROM affiliate_wiki.programs p
    LEFT JOIN affiliate_wiki.program_research r ON r.program_id = p.id
    WHERE r.program_id IS NULL
    """

    with psycopg.connect(args.db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            inserted = cur.rowcount
        conn.commit()

    print(f"Inserted program_research rows: {inserted}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

