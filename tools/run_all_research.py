#!/usr/bin/env python3
"""
Continuous Deep Research Runner

Runs deepresearch.py in batches until all programs are processed.
"""

import subprocess
import sys
import time
from pathlib import Path

BATCH_SIZE = 500
PARALLEL = 30
MODEL = "kimi"
VENV_PYTHON = "/home/skynet/affiliateprograms-wiki/scripts/affiliate_wiki/.venv/bin/python"
DEEPRESEARCH = "/home/skynet/affiliateprograms-wiki/tools/deepresearch.py"

STATUSES = "pending,success,needs_search"


def get_pending_count():
    """Get count of programs still needing research."""
    code = """
import os, subprocess, psycopg
result = subprocess.run(
    ['/home/skynet/google-cloud-sdk/bin/gcloud', 'secrets', 'versions', 'access',
     'latest', '--secret=database_url_affiliate_wiki', '--project=superapp-466313'],
    capture_output=True, text=True, timeout=30
)
db_url = result.stdout.strip()
with psycopg.connect(db_url) as conn:
    with conn.cursor() as cur:
        cur.execute('''
            SELECT COUNT(*) FROM affiliate_wiki.program_research r
            WHERE r.status IN ('pending', 'success', 'needs_search')
              AND (r.extracted IS NULL OR r.extracted->>'deep_researched_at' IS NULL)
        ''')
        print(cur.fetchone()[0])
"""
    result = subprocess.run([VENV_PYTHON, "-c", code], capture_output=True, text=True)
    return int(result.stdout.strip()) if result.returncode == 0 else 0


def run_batch(batch_num: int):
    """Run a single batch."""
    print(f"\n{'='*60}")
    print(f"BATCH {batch_num} - Starting {BATCH_SIZE} programs with {PARALLEL} workers")
    print(f"{'='*60}\n")

    result = subprocess.run(
        [VENV_PYTHON, DEEPRESEARCH,
         "--limit", str(BATCH_SIZE),
         "--parallel", str(PARALLEL),
         "--model", MODEL,
         "--status", STATUSES],
        cwd="/home/skynet/affiliateprograms-wiki"
    )
    return result.returncode == 0


def main():
    batch = 1
    total_start = time.time()

    while True:
        pending = get_pending_count()
        print(f"\n>>> {pending} programs still pending deep research")

        if pending == 0:
            print("\n" + "="*60)
            print("ALL PROGRAMS RESEARCHED!")
            print("="*60)
            break

        success = run_batch(batch)

        if not success:
            print(f"Batch {batch} failed, waiting 60s before retry...")
            time.sleep(60)
            continue

        batch += 1

        # Small delay between batches
        print("\nWaiting 10s before next batch...")
        time.sleep(10)

    elapsed = time.time() - total_start
    print(f"\nTotal time: {elapsed/60:.1f} minutes ({batch-1} batches)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
