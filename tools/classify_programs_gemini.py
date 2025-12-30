#!/usr/bin/env python3
"""
Classify affiliate programs into categories using Gemini API.
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
from pathlib import Path
from typing import Optional

import google.generativeai as genai

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

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


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
            extracted_info += f"Notes: {program.extracted['notes'][:200]}\n"

    # Build condensed category list
    category_list = []
    for cat in categories:
        if cat["depth"] <= 2:  # Only show top 3 levels
            indent = "  " * cat["depth"]
            category_list.append(f"{indent}{cat['path']}")

    categories_text = "\n".join(category_list[:150])

    return f"""Classify this affiliate program into categories. Respond with JSON only.

PROGRAM: {name}
DOMAIN: {domain}
{extracted_info}

CATEGORIES:
{categories_text}

Return JSON:
{{"categories": [{{"path": "Full > Category > Path", "relevance": 0.9, "primary": true}}]}}

Assign 1-5 categories. Set one as primary. Relevance 0.0-1.0."""


def parse_classification_response(response: str) -> list[dict]:
    """Parse AI response into category assignments."""
    try:
        json_match = re.search(r'\{[\s\S]*"categories"[\s\S]*\}', response)
        if json_match:
            data = json.loads(json_match.group())
            return data.get("categories", [])
    except json.JSONDecodeError:
        pass
    return []


def classify_program(program: Program, categories: list[dict], model) -> tuple[int, list[dict], str]:
    """Classify a single program using Gemini."""
    prompt = build_classification_prompt(program, categories)

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.3,
                max_output_tokens=500,
            )
        )

        content = response.text or ""
        assignments = parse_classification_response(content)

        return program.id, assignments, None

    except Exception as e:
        return program.id, [], str(e)


def save_classifications(db_url: str, program_id: int, assignments: list[dict], categories: list[dict]):
    """Save category assignments to database."""
    import psycopg

    path_to_id = {cat["path"]: cat["id"] for cat in categories}

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            for assignment in assignments:
                path = assignment.get("path", "")
                relevance = min(1.0, max(0.0, float(assignment.get("relevance", 0.5))))
                is_primary = bool(assignment.get("primary", False))

                category_id = path_to_id.get(path)

                if not category_id:
                    for cat_path, cat_id in path_to_id.items():
                        if path.lower() in cat_path.lower() or cat_path.lower().endswith(path.lower().split(" > ")[-1]):
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
                        print(f"  DB error: {e}", file=sys.stderr)

            conn.commit()


def main():
    parser = argparse.ArgumentParser(description="Classify programs into categories using Gemini")
    parser.add_argument("--limit", type=int, default=100, help="Number of programs")
    parser.add_argument("--parallel", type=int, default=5, help="Parallel workers")
    args = parser.parse_args()

    if not GEMINI_API_KEY:
        print("GEMINI_API_KEY not set!")
        sys.exit(1)

    db_url = get_db_url()

    # Initialize Gemini model
    model = genai.GenerativeModel('gemini-2.0-flash')

    print("Loading categories...")
    categories = fetch_categories(db_url)
    print(f"  {len(categories)} categories")

    print(f"\nFetching {args.limit} programs...")
    programs = fetch_programs_for_classification(db_url, args.limit)
    print(f"  {len(programs)} programs to classify")

    if not programs:
        print("No programs need classification!")
        return

    print(f"\nClassifying with Gemini Flash using {args.parallel} workers...")
    start = time.time()

    success = 0
    failed = 0
    total_assignments = 0

    def process_program(program):
        """Process a single program with rate limiting."""
        time.sleep(0.1)  # Small delay to avoid rate limits
        return classify_program(program, categories, model)

    # Parallel processing
    with ThreadPoolExecutor(max_workers=args.parallel) as executor:
        futures = {executor.submit(process_program, p): p for p in programs}

        for i, future in enumerate(as_completed(futures), 1):
            program = futures[future]
            try:
                program_id, assignments, error = future.result()

                if error:
                    print(f"  [{i}/{len(programs)}] ERROR: {program.name[:30]} - {error[:50]}")
                    failed += 1
                elif assignments:
                    save_classifications(db_url, program_id, assignments, categories)
                    cats = [a["path"].split(" > ")[-1] for a in assignments[:3]]
                    print(f"  [{i}/{len(programs)}] OK: {program.name[:30]} -> {', '.join(cats)}")
                    success += 1
                    total_assignments += len(assignments)
                else:
                    print(f"  [{i}/{len(programs)}] NO MATCH: {program.name[:30]}")
                    failed += 1

            except Exception as e:
                print(f"  [{i}/{len(programs)}] EXCEPTION: {program.name[:30]} - {e}")
                failed += 1

    elapsed = time.time() - start

    print(f"\n{'='*50}")
    print(f"Classification Complete")
    print(f"{'='*50}")
    print(f"Success:     {success}")
    print(f"Failed:      {failed}")
    print(f"Assignments: {total_assignments}")
    print(f"Time:        {elapsed:.1f}s")


if __name__ == "__main__":
    main()
