#!/usr/bin/env python3
"""
Setup Affiliate Wiki schema in Postgres.

Usage:
  export DATABASE_URL="postgresql://.../db?sslmode=require"
  python3 setup_affiliate_wiki_db.py --db-url "$DATABASE_URL"

Optional: create a dedicated database first (if permitted):
  python3 setup_affiliate_wiki_db.py --create-db affiliate_wiki --admin-url "$DATABASE_URL"
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from urllib.parse import urlparse, urlunparse


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


def _swap_dbname(database_url: str, new_db: str) -> str:
    parsed = urlparse(database_url)
    path = parsed.path or ""
    if not path.startswith("/"):
        path = "/" + path
    return urlunparse(parsed._replace(path="/" + new_db))


def _read_schema_sql() -> str:
    schema_path = Path(__file__).with_name("schema.sql")
    return schema_path.read_text(encoding="utf-8")


def create_database_if_requested(psycopg, admin_url: str, db_name: str) -> None:
    target_url = _swap_dbname(admin_url, "postgres")
    with psycopg.connect(target_url, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            exists = cur.fetchone() is not None
            if exists:
                print(f"Database already exists: {db_name}")
                return
            cur.execute(f'CREATE DATABASE "{db_name}"')
            print(f"Created database: {db_name}")


def apply_schema(psycopg, database_url: str) -> None:
    sql = _read_schema_sql()
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
    print("Applied schema: affiliate_wiki")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--db-url",
        default=os.environ.get("DATABASE_URL", ""),
        help="Target Postgres connection string (default: env DATABASE_URL)",
    )
    parser.add_argument(
        "--create-db",
        default="",
        help='Create this database first (connects to "/postgres"). Requires permissions.',
    )
    parser.add_argument(
        "--admin-url",
        default="",
        help="Admin connection string used for CREATE DATABASE (defaults to --db-url)",
    )

    args = parser.parse_args()
    if not args.db_url:
        _eprint("DATABASE_URL not set (or pass --db-url).")
        return 2

    psycopg = _must_import_psycopg()

    if args.create_db:
        admin_url = args.admin_url or args.db_url
        create_database_if_requested(psycopg, admin_url, args.create_db)
        target_url = _swap_dbname(args.db_url, args.create_db)
        apply_schema(psycopg, target_url)
    else:
        apply_schema(psycopg, args.db_url)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

