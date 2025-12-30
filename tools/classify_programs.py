#!/usr/bin/env python3
"""
Classify affiliate programs into categories using AI.

Uses OpenRouter models to analyze program data and assign to appropriate categories.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Load environment
env_file = Path.home() / "ai-shared" / "secrets" / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, _, value = line.partition('=')
                value = value.strip('"').strip("'")
                os.environ.setdefault(key.strip(), value)

from openai import OpenAI

import itertools

# Load all OpenRouter API keys
OPENROUTER_KEYS = [
    os.getenv("OPENROUTER_API_KEY"),
    os.getenv("OPENROUTER_API_KEY_2"),
    os.getenv("OPENROUTER_API_KEY_3"),
    os.getenv("OPENROUTER_API_KEY_4"),
    os.getenv("OPENROUTER_API_KEY_5"),
]
OPENROUTER_KEYS = [k for k in OPENROUTER_KEYS if k]  # Filter out None
KEY_CYCLE = itertools.cycle(OPENROUTER_KEYS)

MODELS = {
    "kimi": "moonshotai/kimi-k2-thinking",
    "kimi-free": "moonshotai/kimi-k2:free",
    "deepresearch-free": "alibaba/tongyi-deepresearch-30b-a3b:free",
    "haiku": "anthropic/claude-3-haiku",
    "flash": "google/gemini-2.0-flash-001",
}


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
        print(f"Failed to get DB URL: {e}", file=sys.stderr)

    raise RuntimeError("DATABASE_URL not set")


def get_openrouter_client(api_key=None):
    """Get OpenRouter client with rotating keys."""
    if api_key is None:
        api_key = next(KEY_CYCLE)

    if not api_key:
        raise RuntimeError("No OPENROUTER_API_KEY available")

    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        default_headers={
            "HTTP-Referer": "https://affiliateprograms.wiki",
            "X-Title": "AffiliateWiki CategoryClassifier"
        }
    )


@dataclass
class Program:
    id: int
    name: str
    domain: Optional[str]
    extracted: Optional[dict]


def fetch_categories(db_url: str) -> list[dict]:
    """Fetch all categories from database."""
    import psycopg

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, slug, path, depth
                FROM affiliate_wiki.categories
                ORDER BY path
            """)
            return [
                {"id": row[0], "name": row[1], "slug": row[2], "path": row[3], "depth": row[4]}
                for row in cur.fetchall()
            ]


def fetch_programs_for_classification(db_url: str, limit: int) -> list[Program]:
    """Fetch programs that need category classification."""
    import psycopg

    sql = """
        SELECT p.id, p.name, p.domain, r.extracted
        FROM affiliate_wiki.programs p
        JOIN affiliate_wiki.program_research r ON r.program_id = p.id
        LEFT JOIN affiliate_wiki.program_categories pc ON pc.program_id = p.id
        WHERE pc.id IS NULL  -- Not yet classified
        ORDER BY r.extracted->>'deep_researched_at' DESC NULLS LAST, p.id
        LIMIT %s
    """

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (limit,))
            return [
                Program(
                    id=row[0],
                    name=row[1],
                    domain=row[2],
                    extracted=row[3] if isinstance(row[3], dict) else None
                )
                for row in cur.fetchall()
            ]


def build_classification_prompt(program: Program, categories: list[dict]) -> str:
    """Build prompt for category classification."""
    name = program.name
    domain = program.domain or ""

    # Get commission/product info from extracted data
    extracted_info = ""
    if program.extracted:
        if program.extracted.get("commission_rate"):
            extracted_info += f"Commission: {program.extracted['commission_rate']}\n"
        if program.extracted.get("notes"):
            extracted_info += f"Notes: {program.extracted['notes']}\n"

    # Build category list grouped by top-level
    category_list = []
    current_top = None
    for cat in categories:
        if cat["depth"] == 0:
            current_top = cat["name"]
            category_list.append(f"\n{cat['name']}:")
        elif cat["depth"] == 1:
            category_list.append(f"  - {cat['name']}")
        elif cat["depth"] == 2:
            category_list.append(f"    - {cat['name']}")

    categories_text = "\n".join(category_list[:200])  # Limit size

    return f"""Classify this affiliate program into categories.

PROGRAM:
Name: {name}
Domain: {domain}
{extracted_info}

AVAILABLE CATEGORIES (hierarchical):
{categories_text}

TASK:
1. Identify ALL categories this program fits into (can be multiple)
2. For each category, rate relevance from 0.0 to 1.0 (1.0 = perfect fit)
3. Mark one category as PRIMARY (best fit)

Respond ONLY with JSON in this format:
{{
  "categories": [
    {{"path": "Category > Subcategory > Sub-subcategory", "relevance": 0.9, "primary": true}},
    {{"path": "Another Category > Subcategory", "relevance": 0.7, "primary": false}}
  ],
  "reasoning": "Brief explanation of why these categories"
}}

If the program type is unclear, use your best judgment based on the domain name.
If it's a general retailer, assign to multiple relevant categories."""


def parse_classification_response(response: str) -> list[dict]:
    """Parse AI response into category assignments."""
    # Try to extract JSON
    try:
        # Look for JSON block
        json_match = re.search(r'\{[\s\S]*"categories"[\s\S]*\}', response)
        if json_match:
            data = json.loads(json_match.group())
            return data.get("categories", [])
    except json.JSONDecodeError:
        pass

    return []


def classify_program(program: Program, categories: list[dict], model: str, client=None) -> tuple[int, list[dict], str]:
    """Classify a single program using AI with rotating keys."""
    prompt = build_classification_prompt(program, categories)

    # Get a fresh client with rotated key for each request
    client = get_openrouter_client()

    try:
        response = client.chat.completions.create(
            model=MODELS.get(model, model),
            messages=[
                {"role": "system", "content": "You are an expert at categorizing affiliate programs. Respond only with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000,
        )

        content = response.choices[0].message.content or ""
        assignments = parse_classification_response(content)

        return program.id, assignments, None

    except Exception as e:
        return program.id, [], str(e)


def save_classifications(db_url: str, program_id: int, assignments: list[dict], categories: list[dict]):
    """Save category assignments to database."""
    import psycopg

    # Build path -> category_id lookup
    path_to_id = {cat["path"]: cat["id"] for cat in categories}

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            for assignment in assignments:
                path = assignment.get("path", "")
                relevance = assignment.get("relevance", 0.5)
                is_primary = assignment.get("primary", False)

                # Find category ID by path
                category_id = path_to_id.get(path)

                # Try partial match if exact not found
                if not category_id:
                    for cat_path, cat_id in path_to_id.items():
                        if path.lower() in cat_path.lower() or cat_path.lower().endswith(path.lower()):
                            category_id = cat_id
                            break

                if category_id:
                    try:
                        cur.execute("""
                            INSERT INTO affiliate_wiki.program_categories
                            (program_id, category_id, relevance_score, is_primary, assigned_by)
                            VALUES (%s, %s, %s, %s, 'ai')
                            ON CONFLICT (program_id, category_id) DO UPDATE
                            SET relevance_score = EXCLUDED.relevance_score,
                                is_primary = EXCLUDED.is_primary
                        """, (program_id, category_id, relevance, is_primary))
                    except Exception as e:
                        print(f"  Error saving category {path}: {e}", file=sys.stderr)

            conn.commit()


def main():
    parser = argparse.ArgumentParser(description="Classify programs into categories")
    parser.add_argument("--limit", type=int, default=100, help="Number of programs to classify")
    parser.add_argument("--parallel", type=int, default=10, help="Parallel workers")
    parser.add_argument("--model", default="kimi", choices=list(MODELS.keys()), help="Model to use")
    args = parser.parse_args()

    db_url = get_db_url()
    client = get_openrouter_client()

    # Fetch categories
    print("Loading categories...")
    categories = fetch_categories(db_url)
    print(f"  {len(categories)} categories loaded")

    # Fetch programs needing classification
    print(f"\nFetching {args.limit} programs for classification...")
    programs = fetch_programs_for_classification(db_url, args.limit)
    print(f"  {len(programs)} programs to classify")

    if not programs:
        print("No programs need classification!")
        return

    # Classify in parallel
    print(f"\nClassifying with {args.parallel} workers using {args.model}...")
    start = time.time()

    success = 0
    failed = 0
    total_assignments = 0

    with ThreadPoolExecutor(max_workers=args.parallel) as executor:
        futures = {
            executor.submit(classify_program, p, categories, args.model, client): p
            for p in programs
        }

        for i, future in enumerate(as_completed(futures), 1):
            program = futures[future]
            try:
                program_id, assignments, error = future.result()

                if error:
                    print(f"  [{i}/{len(programs)}] ERROR: {program.name} - {error}")
                    failed += 1
                elif assignments:
                    # Save to database
                    save_classifications(db_url, program_id, assignments, categories)
                    cats = ", ".join(a["path"].split(" > ")[-1] for a in assignments[:3])
                    print(f"  [{i}/{len(programs)}] OK: {program.name} -> {cats}")
                    success += 1
                    total_assignments += len(assignments)
                else:
                    print(f"  [{i}/{len(programs)}] NO MATCH: {program.name}")
                    failed += 1

            except Exception as e:
                print(f"  [{i}/{len(programs)}] EXCEPTION: {program.name} - {e}")
                failed += 1

    elapsed = time.time() - start

    print(f"\n{'='*50}")
    print(f"Classification Complete")
    print(f"{'='*50}")
    print(f"Total:       {len(programs)}")
    print(f"Success:     {success}")
    print(f"Failed:      {failed}")
    print(f"Assignments: {total_assignments}")
    print(f"Time:        {elapsed:.1f}s ({elapsed/len(programs):.2f}s/program)")


if __name__ == "__main__":
    main()
