#!/usr/bin/env python3
"""
Set up category database schema and populate from taxonomy.
"""

import os
import re
import subprocess
import sys
from pathlib import Path

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent))

from category_taxonomy import TAXONOMY


def get_db_url() -> str:
    """Get database URL from environment or gcloud."""
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        return db_url

    try:
        result = subprocess.run(
            ["/home/skynet/google-cloud-sdk/bin/gcloud", "secrets", "versions", "access",
             "latest", "--secret=database_url_affiliate_wiki", "--project=superapp-466313"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        print(f"Failed to get DB URL from gcloud: {e}")

    raise RuntimeError("DATABASE_URL not set and gcloud lookup failed")


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = text.strip('-')
    return text


def insert_categories(cur, taxonomy: dict, parent_id: int = None, parent_path: str = "", depth: int = 0):
    """Recursively insert categories from taxonomy."""
    for name, children in taxonomy.items():
        slug = slugify(name)
        path = f"{parent_path} > {name}" if parent_path else name

        # Check if exists
        if parent_id is None:
            cur.execute(
                "SELECT id FROM affiliate_wiki.categories WHERE slug = %s AND parent_id IS NULL",
                (slug,)
            )
        else:
            cur.execute(
                "SELECT id FROM affiliate_wiki.categories WHERE slug = %s AND parent_id = %s",
                (slug, parent_id)
            )
        row = cur.fetchone()

        if row:
            cat_id = row[0]
            print(f"  {'  ' * depth}[exists] {name}")
        else:
            cur.execute(
                """
                INSERT INTO affiliate_wiki.categories (name, slug, parent_id, path, depth)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (name, slug, parent_id, path, depth)
            )
            cat_id = cur.fetchone()[0]
            print(f"  {'  ' * depth}[new] {name}")

        # Insert children
        if children:
            insert_categories(cur, children, cat_id, path, depth + 1)


def main():
    import psycopg

    db_url = get_db_url()

    print("=== Setting up Category Schema ===\n")

    # Read and execute schema SQL
    schema_file = Path(__file__).parent.parent / "scripts" / "create_category_schema.sql"
    if schema_file.exists():
        schema_sql = schema_file.read_text()

        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                print("Creating tables...")
                cur.execute(schema_sql)
                conn.commit()
                print("✓ Schema created\n")

    # Insert categories from taxonomy
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            print("Inserting categories from taxonomy...")
            insert_categories(cur, TAXONOMY)
            conn.commit()

            # Count categories
            cur.execute("SELECT COUNT(*) FROM affiliate_wiki.categories")
            count = cur.fetchone()[0]
            print(f"\n✓ {count} categories in database")


if __name__ == "__main__":
    main()
