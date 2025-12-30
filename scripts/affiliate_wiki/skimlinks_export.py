#!/usr/bin/env python3
"""
Export Skimlinks merchants (program seed list) and optionally load into Postgres.

Endpoint:
  https://merchants.skimlinks.com/public/merchants?include_count=1&offset=0&limit=2000

Usage:
  python3 skimlinks_export.py

Optional load to Postgres:
  export DATABASE_URL="postgresql://.../db?sslmode=require"
  python3 skimlinks_export.py --db-url "$DATABASE_URL"
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import requests


API_URL = "https://merchants.skimlinks.com/public/merchants"
SOURCE_NAME = "skimlinks"
DEFAULT_OUT_DIR = str(Path(__file__).resolve().parents[2] / "data" / "affiliate_wiki" / "skimlinks")


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


def _json_dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


@dataclass(frozen=True)
class ExportPaths:
    out_dir: Path
    jsonl_path: Path
    checkpoint_path: Path
    stats_path: Path


def _paths(out_dir: Path) -> ExportPaths:
    out_dir.mkdir(parents=True, exist_ok=True)
    return ExportPaths(
        out_dir=out_dir,
        jsonl_path=out_dir / "skimlinks_merchants.jsonl",
        checkpoint_path=out_dir / "checkpoint.json",
        stats_path=out_dir / "stats.json",
    )


def _load_checkpoint(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_checkpoint(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def fetch_page(offset: int, limit: int, include_count: bool) -> dict[str, Any]:
    params = {
        "offset": offset,
        "limit": limit,
        "include_count": 1 if include_count else 0,
    }
    r = requests.get(API_URL, params=params, timeout=90)
    r.raise_for_status()
    return r.json()


def append_jsonl(jsonl_path: Path, records: Iterable[dict[str, Any]]) -> tuple[int, str]:
    count = 0
    sha = hashlib.sha256()
    with jsonl_path.open("ab") as f:
        for rec in records:
            line = (_json_dumps(rec) + "\n").encode("utf-8")
            f.write(line)
            sha.update(line)
            count += 1
    return count, sha.hexdigest()


def _program_row_from_merchant(m: dict[str, Any]) -> dict[str, Any]:
    try:
        from psycopg.types.json import Json  # type: ignore
    except Exception:
        Json = None  # type: ignore

    def _j(v: Any) -> Any:
        if Json is None:
            return v
        return Json(v)

    return {
        "source": SOURCE_NAME,
        "source_advertiser_id": int(m.get("advertiser_id") or m.get("id")),
        "name": m.get("name") or "",
        "domain": m.get("domain"),
        "domains": m.get("domains"),
        "countries": m.get("countries"),
        "partner_type": m.get("partner_type"),
        "merchant_ids": m.get("merchant_ids"),
        "verticals": _j(m.get("verticals")),
        "metadata": _j(m.get("metadata")),
        "raw": _j(m),
    }


def upsert_programs(db_url: str, merchants: list[dict[str, Any]]) -> int:
    psycopg = _must_import_psycopg()

    rows = [_program_row_from_merchant(m) for m in merchants]
    if not rows:
        return 0

    sql = """
    INSERT INTO affiliate_wiki.programs
      (source, source_advertiser_id, name, domain, domains, countries, partner_type, merchant_ids, verticals, metadata, raw)
    VALUES
      (%(source)s, %(source_advertiser_id)s, %(name)s, %(domain)s, %(domains)s, %(countries)s, %(partner_type)s, %(merchant_ids)s, %(verticals)s, %(metadata)s, %(raw)s)
    ON CONFLICT (source, source_advertiser_id) DO UPDATE SET
      name = EXCLUDED.name,
      domain = EXCLUDED.domain,
      domains = EXCLUDED.domains,
      countries = EXCLUDED.countries,
      partner_type = EXCLUDED.partner_type,
      merchant_ids = EXCLUDED.merchant_ids,
      verticals = EXCLUDED.verticals,
      metadata = EXCLUDED.metadata,
      raw = EXCLUDED.raw,
      updated_at = NOW()
    """

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.executemany(sql, rows)
        conn.commit()
    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    parser.add_argument("--limit", type=int, default=2000)
    parser.add_argument("--start-offset", type=int, default=-1, help="Default: resume from checkpoint")
    parser.add_argument("--max-rows", type=int, default=0, help="0 = no limit")
    parser.add_argument("--sleep", type=float, default=0.25, help="Seconds between page fetches")
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Delete existing jsonl/checkpoint and start from offset=0 (or --start-offset).",
    )
    parser.add_argument("--db-url", default=os.environ.get("DATABASE_URL", ""))

    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    p = _paths(out_dir)

    if args.fresh:
        for fp in [p.jsonl_path, p.checkpoint_path, p.stats_path]:
            if fp.exists():
                fp.unlink()

    cp = _load_checkpoint(p.checkpoint_path)
    checkpoint_offset = int(cp.get("next_offset", 0))
    start_offset = args.start_offset if args.start_offset >= 0 else checkpoint_offset
    max_rows = None if args.max_rows <= 0 else int(args.max_rows)

    _eprint(f"Skimlinks export -> {p.jsonl_path}")
    _eprint(f"Starting offset: {start_offset} (limit={args.limit})")

    stats: dict[str, Any] = {
        "source": SOURCE_NAME,
        "api_url": API_URL,
        "started_at": time.time(),
        "limit": args.limit,
        "start_offset": start_offset,
    }

    buffer: list[dict[str, Any]] = []
    written_total = 0
    loaded_total = 0
    running_hash = hashlib.sha256()

    next_offset = start_offset
    include_count = True

    while True:
        payload = fetch_page(offset=next_offset, limit=args.limit, include_count=include_count)
        include_count = False
        merchants = payload.get("merchants") or []
        if not merchants:
            break

        page_len = len(merchants)
        buffer.extend(merchants)
        next_offset += page_len

        if max_rows is not None and (written_total + len(buffer)) >= max_rows:
            keep = max_rows - written_total
            buffer = buffer[:keep]
            next_offset = next_offset - page_len + keep

        count, page_hash = append_jsonl(p.jsonl_path, buffer)
        written_total += count
        running_hash.update(page_hash.encode("utf-8"))

        if args.db_url:
            loaded_total += upsert_programs(args.db_url, buffer)

        buffer = []

        stats["last_page"] = {
            "offset_end": next_offset,
            "num_written": count,
            "has_more": bool(payload.get("has_more")),
            "reported_total": payload.get("total"),
        }
        stats["written_total"] = written_total
        stats["loaded_total"] = loaded_total

        _save_checkpoint(p.checkpoint_path, {"next_offset": next_offset, "written_total": written_total})
        p.stats_path.write_text(json.dumps(stats, indent=2), encoding="utf-8")

        if max_rows is not None and written_total >= max_rows:
            break
        if not payload.get("has_more"):
            break

        time.sleep(max(0.0, args.sleep))

    stats["finished_at"] = time.time()
    stats["sha256"] = running_hash.hexdigest()
    p.stats_path.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    _save_checkpoint(p.checkpoint_path, {"next_offset": next_offset, "written_total": written_total})

    _eprint(f"Done. Written: {written_total}. Loaded: {loaded_total}. Next offset: {next_offset}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

