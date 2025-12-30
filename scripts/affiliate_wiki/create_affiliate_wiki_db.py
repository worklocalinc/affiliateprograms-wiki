#!/usr/bin/env python3
"""
Create a dedicated Postgres database for the Affiliate Wiki on your Neon cluster
and apply the Affiliate Wiki schema.

This script intentionally avoids printing secrets. It pulls credentials from
GCP Secret Manager via `gcp_secrets.py` (from `~/bio-domains/`; falls back to gcloud CLI if needed).

Default secret source for the cluster connection:
  - database_url_saas_os

Usage:
  bash affiliateprograms-wiki/scripts/affiliate_wiki/bootstrap_venv.sh
  affiliateprograms-wiki/scripts/affiliate_wiki/.venv/bin/python affiliateprograms-wiki/scripts/affiliate_wiki/create_affiliate_wiki_db.py

Optional: store the resulting DB URL back into Secret Manager:
  affiliateprograms-wiki/scripts/affiliate_wiki/.venv/bin/python affiliateprograms-wiki/scripts/affiliate_wiki/create_affiliate_wiki_db.py \
    --write-secret database_url_affiliate_wiki
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse, urlunparse


def _eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


def _mask(v: str) -> str:
    if not v:
        return "[missing]"
    if len(v) <= 8:
        return "*" * len(v)
    return f"{v[:4]}…{v[-4:]} (len={len(v)})"


def _must_import_psycopg():
    try:
        import psycopg  # type: ignore

        return psycopg
    except Exception as e:
        _eprint("Missing dependency: psycopg[binary]")
        _eprint("Install with:")
        _eprint("  bash affiliateprograms-wiki/scripts/affiliate_wiki/bootstrap_venv.sh")
        raise SystemExit(2) from e


def _import_gcp_secrets():
    home = Path.home()
    candidates = [home / "bio-domains", home / "bio"]
    for base in candidates:
        if base.exists():
            sys.path.insert(0, str(base))
            try:
                from gcp_secrets import GCPSecrets  # type: ignore

                return GCPSecrets
            except Exception:
                continue
    raise ImportError("Could not import GCPSecrets from ~/bio-domains or ~/bio")


def _with_db(url: str, dbname: str) -> str:
    p = urlparse(url)
    return urlunparse((p.scheme, p.netloc, "/" + dbname, p.params, p.query, p.fragment))


def _read_schema_sql() -> str:
    return Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")


def ensure_database_exists(psycopg, admin_url: str, db_name: str) -> None:
    postgres_url = _with_db(admin_url, "postgres")
    with psycopg.connect(postgres_url, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            exists = cur.fetchone() is not None
            if exists:
                print(f"✓ Database already exists: {db_name}")
                return
            cur.execute(f'CREATE DATABASE "{db_name}"')
            print(f"✓ Created database: {db_name}")


def apply_schema(psycopg, db_url: str) -> None:
    sql = _read_schema_sql()
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
    print("✓ Applied schema: affiliate_wiki")


def write_secret(secrets, name: str, value: str) -> None:
    client = getattr(secrets, "client", None)
    if client is not None:
        ok = secrets.create_secret(name, value)
        if not ok:
            ok = secrets.update_secret(name, value)
        if not ok:
            raise RuntimeError("Secret upsert failed via Secret Manager client")
        print(f"✓ Upserted secret: {name} (value={_mask(value)})")
        return

    gcloud = getattr(secrets, "_gcloud_path", None) or shutil.which("gcloud")
    if not gcloud:
        raise RuntimeError("Cannot write secret: Secret Manager client unavailable and gcloud not found")

    project = getattr(secrets, "project_id", "")
    if not project:
        raise RuntimeError("Cannot write secret: missing GCP project_id")

    desc = subprocess.run(
        [gcloud, "secrets", "describe", name, "--project", project],
        check=False,
        capture_output=True,
        text=True,
    )
    if desc.returncode != 0:
        create = subprocess.run(
            [gcloud, "secrets", "create", name, "--replication-policy=automatic", "--project", project],
            check=False,
            capture_output=True,
            text=True,
        )
        if create.returncode != 0:
            raise RuntimeError(f"gcloud secrets create failed: {(create.stderr or create.stdout).strip()}")

    add = subprocess.run(
        [gcloud, "secrets", "versions", "add", name, "--data-file=-", "--project", project],
        input=value,
        check=False,
        capture_output=True,
        text=True,
    )
    if add.returncode != 0:
        raise RuntimeError(f"gcloud secrets versions add failed: {(add.stderr or add.stdout).strip()}")

    print(f"✓ Upserted secret: {name} (value={_mask(value)}) via gcloud")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default="superapp-466313")
    ap.add_argument("--cluster-url-secret", default="database_url_saas_os")
    ap.add_argument("--db-name", default="affiliate_wiki")
    ap.add_argument("--write-secret", default="", help="Optional secret name to store the new DB URL")
    args = ap.parse_args()

    psycopg = _must_import_psycopg()
    GCPSecrets = _import_gcp_secrets()
    secrets = GCPSecrets(project_id=args.project)

    base_url = secrets.get_secret(args.cluster_url_secret) or ""
    if not base_url:
        _eprint(f"Could not read secret: {args.cluster_url_secret}")
        return 2

    ensure_database_exists(psycopg, base_url, args.db_name)
    target_url = _with_db(base_url, args.db_name)
    apply_schema(psycopg, target_url)

    if args.write_secret:
        try:
            write_secret(secrets, args.write_secret, target_url)
        except Exception as e:
            _eprint(f"Warning: could not write secret {args.write_secret}: {e}")

    p = urlparse(target_url)
    sslmode = ""
    try:
        sslmode = dict([kv.split("=", 1) for kv in p.query.split("&") if "=" in kv]).get("sslmode", "")
    except Exception:
        sslmode = ""
    print(f"✓ Ready: host={p.hostname} db={args.db_name} sslmode={sslmode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

