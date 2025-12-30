#!/usr/bin/env python3
"""
Seed a starter list of CPA networks into affiliate_wiki.cpa_networks and create pending research rows.

Usage:
  affiliateprograms-wiki/scripts/affiliate_wiki/.venv/bin/python \
    affiliateprograms-wiki/scripts/affiliate_wiki/seed_cpa_networks.py \
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


SEEDS: list[dict[str, str]] = [
    {"name": "MaxBounty", "website": "https://www.maxbounty.com/"},
    {"name": "ClickDealer", "website": "https://www.clickdealer.com/"},
    {"name": "CPAlead", "website": "https://www.cpalead.com/"},
    {"name": "AdWork Media", "website": "https://www.adworkmedia.com/"},
    {"name": "CrakRevenue", "website": "https://www.crakrevenue.com/"},
    {"name": "PeerFly", "website": "https://www.peerfly.com/"},
    {"name": "CJ (Commission Junction)", "website": "https://www.cj.com/"},
    {"name": "Impact", "website": "https://impact.com/"},
    {"name": "PartnerStack", "website": "https://partnerstack.com/"},
    {"name": "ShareASale", "website": "https://www.shareasale.com/"},
    {"name": "Awin", "website": "https://www.awin.com/"},
    {"name": "Rakuten Advertising", "website": "https://rakutenadvertising.com/"},
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db-url", default=os.environ.get("DATABASE_URL", ""))
    args = ap.parse_args()

    if not args.db_url:
        _eprint("DATABASE_URL not set (or pass --db-url).")
        return 2

    psycopg = _must_import_psycopg()
    from psycopg.types.json import Json  # type: ignore

    upsert_sql = """
    INSERT INTO affiliate_wiki.cpa_networks (name, website, raw)
    VALUES (%(name)s, %(website)s, %(raw)s)
    ON CONFLICT (name) DO UPDATE SET
      website = EXCLUDED.website,
      raw = EXCLUDED.raw,
      updated_at = NOW()
    RETURNING id
    """

    inserted = 0
    with psycopg.connect(args.db_url) as conn:
        with conn.cursor() as cur:
            for rec in SEEDS:
                cur.execute(upsert_sql, {"name": rec["name"], "website": rec["website"], "raw": Json(rec)})
                _id = cur.fetchone()[0]
                inserted += 1
                cur.execute(
                    """
                    INSERT INTO affiliate_wiki.cpa_network_research (cpa_network_id)
                    VALUES (%s)
                    ON CONFLICT (cpa_network_id) DO NOTHING
                    """,
                    (_id,),
                )
        conn.commit()

    print(f"Upserted CPA networks: {inserted}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
