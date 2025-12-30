#!/usr/bin/env python3
from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from typing import Any

import psycopg
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

# Import editorial pipeline router
from editorial import router as editorial_router


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _slug_expr_sql(col: str) -> str:
    # PostgreSQL regex: replace non-alnum with '-', then trim leading/trailing '-'
    return f"lower(regexp_replace(regexp_replace({col}, '[^a-zA-Z0-9]+', '-', 'g'), '(^-|-$)', '', 'g'))"


def _require_db_url() -> str:
    db_url = os.environ.get("DATABASE_URL", "").strip()
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set")
    return db_url


def _fetchall(db_url: str, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            cols = [d.name for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def _fetchone(db_url: str, sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    rows = _fetchall(db_url, sql, params)
    return rows[0] if rows else None


app = FastAPI(
    title="AffiliatePrograms.wiki API",
    version="1.0.0",
    description="""
## AffiliatePrograms.wiki API

Public API for accessing affiliate program data. Free to use, no authentication required.

### Available Endpoints

- **Programs**: Browse and search 36,000+ affiliate programs
- **Networks**: Information about affiliate networks (ShareASale, CJ, Impact, etc.)
- **Categories**: Hierarchical category system
- **Countries**: Filter programs by country availability
- **Browse**: Combined filtering (country + category + network)

### Rate Limits

Please be respectful: max 60 requests/minute for reasonable use.

### Data Provenance

Each program includes:
- `deep_researched_at`: When data was last verified
- `tracking_platform`: Source network
- `signup_url`: Official affiliate signup link
""",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Allow all origins for public API access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Public API - allow all origins
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Editorial endpoints need POST
    allow_headers=["*"],
)

# Include editorial pipeline router (authenticated endpoints)
app.include_router(editorial_router)


@app.get("/")
def api_root() -> dict[str, Any]:
    """API root - lists all available endpoints."""
    return {
        "name": "AffiliatePrograms.wiki API",
        "version": "1.0.0",
        "description": "Public API for 36,000+ affiliate programs",
        "documentation": {
            "openapi": "/docs",
            "redoc": "/redoc",
            "openapi_json": "/openapi.json",
        },
        "endpoints": {
            "programs": {
                "list": "GET /programs?limit=50&offset=0&q=search",
                "detail": "GET /programs/{slug}",
                "description": "Browse and search affiliate programs",
            },
            "networks": {
                "list": "GET /networks",
                "detail": "GET /networks/{slug}",
                "description": "Affiliate network information",
            },
            "categories": {
                "list": "GET /categories",
                "detail": "GET /categories/{slug}",
                "description": "Hierarchical program categories",
            },
            "countries": {
                "list": "GET /countries",
                "detail": "GET /countries/{country}",
                "description": "Programs by country availability",
            },
            "browse": {
                "url": "GET /browse?country=Canada&category=beauty-cosmetics&network=ShareASale&q=search",
                "description": "Combined filtering - find programs by country AND category AND network",
            },
            "search": {
                "url": "GET /search?q=query",
                "description": "Quick search across programs and networks",
            },
            "languages": {
                "list": "GET /languages",
                "detail": "GET /languages/{language}",
                "description": "Programs by supported language",
            },
        },
        "data": {
            "total_programs": "36,000+",
            "total_networks": "30+",
            "total_categories": "100+",
            "total_countries": "100+",
        },
        "sitemap": "https://affiliateprograms.wiki/sitemap.xml",
    }


@app.get("/health")
def health() -> dict[str, Any]:
    return {"ok": True, "ts": _now_iso()}


@app.get("/stats")
def stats() -> dict[str, Any]:
    db_url = _require_db_url()
    row = _fetchone(
        db_url,
        """
        select
          (select count(*) from affiliate_wiki.programs) as programs,
          (select count(*) from affiliate_wiki.cpa_networks) as cpa_networks,
          (select count(*) from affiliate_wiki.program_research where status='pending') as pending,
          (select count(*) from affiliate_wiki.program_research where status='success') as success,
          (select count(*) from affiliate_wiki.program_research where status='needs_search') as needs_search,
          (select count(*) from affiliate_wiki.program_research where extracted->>'deep_researched_at' is not null) as deep_researched,
          (select count(*) from affiliate_wiki.program_research where extracted->>'commission_rate' is not null) as has_commission,
          (select count(*) from affiliate_wiki.program_research where extracted->>'tracking_platform' is not null) as has_tracking_platform
        """,
    ) or {}
    row["generated_at"] = _now_iso()
    return row


@app.get("/programs")
def list_programs(
    q: str = Query(default="", max_length=200),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    has_deep_research: bool = Query(default=False),
) -> dict[str, Any]:
    db_url = _require_db_url()
    q = q.strip()
    like = f"%{q}%"
    slug_expr = _slug_expr_sql("p.name")

    where_clauses = []
    params: list[Any] = []
    if q:
        where_clauses.append("(p.name ilike %s or p.domain ilike %s)")
        params.extend([like, like])
    if has_deep_research:
        where_clauses.append("r.extracted->>'deep_researched_at' is not null")

    where = ("where " + " and ".join(where_clauses)) if where_clauses else ""

    rows = _fetchall(
        db_url,
        f"""
        select
          p.id,
          p.name,
          {slug_expr} as slug,
          p.domain,
          p.partner_type,
          p.metadata->>'logo_url' as logo_url,
          r.status as research_status,
          r.last_success_at,
          r.last_attempt_at,
          -- Deep research fields (new)
          r.extracted->>'commission_rate' as commission_rate,
          (r.extracted->>'cookie_duration_days')::int as cookie_duration_days,
          r.extracted->>'payout_model' as payout_model,
          r.extracted->>'tracking_platform' as tracking_platform,
          r.extracted->>'minimum_payout' as minimum_payout,
          r.extracted->>'signup_url' as signup_url,
          r.extracted->>'deep_researched_at' as deep_researched_at,
          -- Legacy fields (fallback)
          coalesce(r.extracted->>'commission_rate', r.extracted->'fields'->>'commission') as commission,
          coalesce((r.extracted->>'cookie_duration_days')::text, r.extracted->'fields'->>'cookie_length_days') as cookie_length_days,
          r.extracted->'fields'->'payout_models' as payout_models
        from affiliate_wiki.programs p
        join affiliate_wiki.program_research r on r.program_id = p.id
        {where}
        order by r.extracted->>'deep_researched_at' desc nulls last, coalesce(r.last_success_at, r.last_attempt_at) desc nulls last, p.id asc
        limit %s offset %s
        """,
        tuple(params + [limit, offset]),
    )

    # best-effort counts (cheap enough for now)
    total_row = _fetchone(
        db_url,
        f"select count(*)::bigint as total from affiliate_wiki.programs p join affiliate_wiki.program_research r on r.program_id = p.id {where}",
        tuple(params),
    ) or {"total": 0}

    return {"items": rows, "total": int(total_row["total"]), "limit": limit, "offset": offset}


@app.get("/programs/{slug}")
def get_program(slug: str) -> dict[str, Any]:
    slug = slug.strip().lower()
    if not re.match(r"^[a-z0-9][a-z0-9-]{0,200}$", slug):
        raise HTTPException(status_code=400, detail="invalid slug")

    db_url = _require_db_url()
    slug_expr = _slug_expr_sql("p.name")

    row = _fetchone(
        db_url,
        f"""
        select
          p.id,
          p.name,
          {slug_expr} as slug,
          p.domain,
          p.domains,
          p.countries,
          p.partner_type,
          p.verticals,
          p.metadata,
          r.status as research_status,
          r.last_success_at,
          r.last_attempt_at,
          -- Deep research fields
          r.extracted->>'commission_rate' as commission_rate,
          (r.extracted->>'cookie_duration_days')::int as cookie_duration_days,
          r.extracted->>'payout_model' as payout_model,
          r.extracted->>'tracking_platform' as tracking_platform,
          r.extracted->>'minimum_payout' as minimum_payout,
          r.extracted->'payment_methods' as payment_methods,
          r.extracted->>'payment_frequency' as payment_frequency,
          r.extracted->>'requirements' as requirements,
          r.extracted->'restrictions' as restrictions,
          r.extracted->>'signup_url' as signup_url,
          r.extracted->>'notes' as notes,
          r.extracted->>'deep_researched_at' as deep_researched_at,
          r.extracted->>'deep_research_model' as deep_research_model,
          -- Full extracted data for reference
          r.extracted,
          r.evidence
        from affiliate_wiki.programs p
        join affiliate_wiki.program_research r on r.program_id = p.id
        where {slug_expr} = %s
        limit 1
        """,
        (slug,),
    )
    if not row:
        raise HTTPException(status_code=404, detail="program not found")
    return row


@app.get("/networks")
def list_networks(limit: int = Query(default=100, ge=1, le=200)) -> dict[str, Any]:
    db_url = _require_db_url()
    slug_expr = _slug_expr_sql("n.name")
    rows = _fetchall(
        db_url,
        f"""
        select
          n.id,
          n.name,
          {slug_expr} as slug,
          n.website,
          n.raw->>'logo_url' as logo_url,
          n.raw->>'type' as network_type,
          n.raw->>'description' as description,
          r.status as research_status,
          r.last_success_at,
          r.last_attempt_at
        from affiliate_wiki.cpa_networks n
        left join affiliate_wiki.cpa_network_research r on r.cpa_network_id = n.id
        order by n.name asc
        limit %s
        """,
        (limit,),
    )
    return {"items": rows}


@app.get("/networks/{slug}")
def get_network(slug: str) -> dict[str, Any]:
    slug = slug.strip().lower()
    if not re.match(r"^[a-z0-9][a-z0-9-]{0,200}$", slug):
        raise HTTPException(status_code=400, detail="invalid slug")

    db_url = _require_db_url()
    slug_expr = _slug_expr_sql("n.name")
    row = _fetchone(
        db_url,
        f"""
        select
          n.id,
          n.name,
          {slug_expr} as slug,
          n.website,
          n.countries,
          n.raw,
          r.status as research_status,
          r.last_success_at,
          r.last_attempt_at,
          r.extracted,
          r.evidence
        from affiliate_wiki.cpa_networks n
        left join affiliate_wiki.cpa_network_research r on r.cpa_network_id = n.id
        where {slug_expr} = %s
        limit 1
        """,
        (slug,),
    )
    if not row:
        raise HTTPException(status_code=404, detail="network not found")
    return row


@app.get("/categories")
def list_categories() -> dict[str, Any]:
    """Get hierarchical category tree."""
    db_url = _require_db_url()

    rows = _fetchall(
        db_url,
        """
        SELECT id, name, slug, parent_id, path, depth, program_count
        FROM affiliate_wiki.categories
        ORDER BY path
        """,
    )

    # Build tree structure
    categories = []
    id_to_cat = {}

    for row in rows:
        cat = {
            "id": row["id"],
            "name": row["name"],
            "slug": row["slug"],
            "path": row["path"],
            "depth": row["depth"],
            "program_count": row["program_count"] or 0,
            "children": [],
        }
        id_to_cat[row["id"]] = cat

        if row["parent_id"] is None:
            categories.append(cat)
        elif row["parent_id"] in id_to_cat:
            id_to_cat[row["parent_id"]]["children"].append(cat)

    return {"items": categories, "total": len(rows)}


@app.get("/categories/{slug}")
def get_category(
    slug: str,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    """Get category with programs, sorted by relevance."""
    slug = slug.strip().lower()
    if not re.match(r"^[a-z0-9][a-z0-9-]{0,200}$", slug):
        raise HTTPException(status_code=400, detail="invalid slug")

    db_url = _require_db_url()
    slug_expr = _slug_expr_sql("p.name")

    # Get category info
    category = _fetchone(
        db_url,
        """
        SELECT c.id, c.name, c.slug, c.path, c.depth, c.parent_id, c.program_count,
               parent.name as parent_name, parent.slug as parent_slug
        FROM affiliate_wiki.categories c
        LEFT JOIN affiliate_wiki.categories parent ON parent.id = c.parent_id
        WHERE c.slug = %s
        LIMIT 1
        """,
        (slug,),
    )
    if not category:
        raise HTTPException(status_code=404, detail="category not found")

    # Get subcategories
    subcategories = _fetchall(
        db_url,
        """
        SELECT id, name, slug, program_count
        FROM affiliate_wiki.categories
        WHERE parent_id = %s
        ORDER BY name
        """,
        (category["id"],),
    )

    # Get programs in this category, sorted by relevance
    programs = _fetchall(
        db_url,
        f"""
        SELECT
          p.id,
          p.name,
          {slug_expr} as slug,
          p.domain,
          pc.relevance_score,
          pc.is_primary,
          r.extracted->>'commission_rate' as commission_rate,
          (r.extracted->>'cookie_duration_days')::int as cookie_duration_days,
          r.extracted->>'payout_model' as payout_model,
          r.extracted->>'tracking_platform' as tracking_platform,
          r.extracted->>'deep_researched_at' as deep_researched_at
        FROM affiliate_wiki.program_categories pc
        JOIN affiliate_wiki.programs p ON p.id = pc.program_id
        JOIN affiliate_wiki.program_research r ON r.program_id = p.id
        WHERE pc.category_id = %s
        ORDER BY pc.relevance_score DESC, pc.is_primary DESC, p.name
        LIMIT %s OFFSET %s
        """,
        (category["id"], limit, offset),
    )

    # Get total count
    total_row = _fetchone(
        db_url,
        "SELECT COUNT(*) as total FROM affiliate_wiki.program_categories WHERE category_id = %s",
        (category["id"],),
    ) or {"total": 0}

    # Get breadcrumb path
    breadcrumbs = []
    if category["path"]:
        parts = category["path"].split(" > ")
        current_path = ""
        for part in parts:
            current_path = f"{current_path} > {part}" if current_path else part
            bc = _fetchone(
                db_url,
                "SELECT name, slug FROM affiliate_wiki.categories WHERE path = %s",
                (current_path,),
            )
            if bc:
                breadcrumbs.append(bc)

    return {
        "category": category,
        "subcategories": subcategories,
        "breadcrumbs": breadcrumbs,
        "programs": programs,
        "total": int(total_row["total"]),
        "limit": limit,
        "offset": offset,
    }


@app.get("/countries")
def list_countries() -> dict[str, Any]:
    """Get list of countries with program counts."""
    db_url = _require_db_url()

    # Get unique countries with counts
    rows = _fetchall(
        db_url,
        """
        WITH country_expanded AS (
            SELECT unnest(countries) as country
            FROM affiliate_wiki.programs
            WHERE countries IS NOT NULL AND countries != '{}'
        )
        SELECT country, COUNT(*) as program_count
        FROM country_expanded
        GROUP BY country
        ORDER BY program_count DESC
        """,
    )

    return {"items": rows, "total": len(rows)}


@app.get("/countries/{country}")
def get_country(
    country: str,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    """Get programs available in a specific country."""
    country = country.strip()
    db_url = _require_db_url()
    slug_expr = _slug_expr_sql("p.name")

    # Get programs for this country
    programs = _fetchall(
        db_url,
        f"""
        SELECT
          p.id,
          p.name,
          {slug_expr} as slug,
          p.domain,
          p.countries,
          r.extracted->>'commission_rate' as commission_rate,
          (r.extracted->>'cookie_duration_days')::int as cookie_duration_days,
          r.extracted->>'payout_model' as payout_model,
          r.extracted->>'tracking_platform' as tracking_platform,
          r.extracted->>'deep_researched_at' as deep_researched_at
        FROM affiliate_wiki.programs p
        JOIN affiliate_wiki.program_research r ON r.program_id = p.id
        WHERE %s = ANY(p.countries)
        ORDER BY r.extracted->>'deep_researched_at' DESC NULLS LAST, p.name
        LIMIT %s OFFSET %s
        """,
        (country, limit, offset),
    )

    # Get total count
    total_row = _fetchone(
        db_url,
        "SELECT COUNT(*) as total FROM affiliate_wiki.programs WHERE %s = ANY(countries)",
        (country,),
    ) or {"total": 0}

    return {
        "country": country,
        "programs": programs,
        "total": int(total_row["total"]),
        "limit": limit,
        "offset": offset,
    }


@app.get("/languages")
def list_languages() -> dict[str, Any]:
    """Get list of languages with program counts (from deep research data)."""
    db_url = _require_db_url()

    # Get unique languages with counts from the extracted languages array
    rows = _fetchall(
        db_url,
        """
        WITH language_expanded AS (
            SELECT unnest(
                CASE
                    WHEN jsonb_typeof(extracted->'languages') = 'array'
                    THEN ARRAY(SELECT jsonb_array_elements_text(extracted->'languages'))
                    WHEN extracted->>'languages' IS NOT NULL
                    THEN string_to_array(extracted->>'languages', ',')
                    ELSE ARRAY[]::text[]
                END
            ) as language
            FROM affiliate_wiki.program_research
            WHERE extracted->>'languages' IS NOT NULL
        )
        SELECT trim(language) as language, COUNT(*) as program_count
        FROM language_expanded
        WHERE language IS NOT NULL AND trim(language) != ''
        GROUP BY trim(language)
        ORDER BY program_count DESC
        """,
    )

    return {"items": rows, "total": len(rows)}


@app.get("/languages/{language}")
def get_language(
    language: str,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    """Get programs supporting a specific language."""
    language = language.strip()
    db_url = _require_db_url()
    slug_expr = _slug_expr_sql("p.name")

    # Get programs that support this language
    programs = _fetchall(
        db_url,
        f"""
        SELECT
          p.id,
          p.name,
          {slug_expr} as slug,
          p.domain,
          r.extracted->>'languages' as languages,
          r.extracted->>'regional_links' as regional_links,
          r.extracted->>'commission_rate' as commission_rate,
          (r.extracted->>'cookie_duration_days')::int as cookie_duration_days,
          r.extracted->>'payout_model' as payout_model,
          r.extracted->>'tracking_platform' as tracking_platform,
          r.extracted->>'deep_researched_at' as deep_researched_at
        FROM affiliate_wiki.programs p
        JOIN affiliate_wiki.program_research r ON r.program_id = p.id
        WHERE (
            (jsonb_typeof(r.extracted->'languages') = 'array'
             AND EXISTS (SELECT 1 FROM jsonb_array_elements_text(r.extracted->'languages') lang WHERE trim(lang) ILIKE %s))
            OR r.extracted->>'languages' ILIKE %s
        )
        ORDER BY r.extracted->>'deep_researched_at' DESC NULLS LAST, p.name
        LIMIT %s OFFSET %s
        """,
        (language, f"%{language}%", limit, offset),
    )

    # Get total count
    total_row = _fetchone(
        db_url,
        """
        SELECT COUNT(*) as total
        FROM affiliate_wiki.program_research r
        WHERE (
            (jsonb_typeof(r.extracted->'languages') = 'array'
             AND EXISTS (SELECT 1 FROM jsonb_array_elements_text(r.extracted->'languages') lang WHERE trim(lang) ILIKE %s))
            OR r.extracted->>'languages' ILIKE %s
        )
        """,
        (language, f"%{language}%"),
    ) or {"total": 0}

    return {
        "language": language,
        "programs": programs,
        "total": int(total_row["total"]),
        "limit": limit,
        "offset": offset,
    }


@app.get("/search")
def search(q: str = Query(default="", max_length=200), limit: int = Query(default=10, ge=1, le=25)) -> dict[str, Any]:
    db_url = _require_db_url()
    q = q.strip()
    if len(q) < 2:
        return {"items": []}
    like = f"%{q}%"

    program_slug = _slug_expr_sql("p.name")
    network_slug = _slug_expr_sql("n.name")

    programs = _fetchall(
        db_url,
        f"""
        select p.name, {program_slug} as slug, p.domain
        from affiliate_wiki.programs p
        where p.name ilike %s
        order by p.name asc
        limit %s
        """,
        (like, limit),
    )
    networks = _fetchall(
        db_url,
        f"""
        select n.name, {network_slug} as slug, n.website
        from affiliate_wiki.cpa_networks n
        where n.name ilike %s
        order by n.name asc
        limit %s
        """,
        (like, limit),
    )

    items: list[dict[str, Any]] = []
    for p in programs:
        items.append({"type": "program", "name": p["name"], "slug": p["slug"], "description": p.get("domain")})
    for n in networks:
        items.append({"type": "network", "name": n["name"], "slug": n["slug"], "description": n.get("website")})

    return {"items": items[:limit]}


@app.get("/browse")
def browse_programs(
    country: str | None = Query(default=None, description="Filter by country (e.g., Canada, US, UK)"),
    category: str | None = Query(default=None, description="Filter by category slug (e.g., beauty-cosmetics)"),
    network: str | None = Query(default=None, description="Filter by network/tracking platform"),
    language: str | None = Query(default=None, description="Filter by supported language (e.g., English, French)"),
    q: str | None = Query(default=None, max_length=200, description="Search query"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    """
    Browse programs with combined filters.

    Examples:
    - /browse?country=Canada&category=beauty-cosmetics  (Canadian Beauty offers)
    - /browse?country=US&network=ShareASale
    - /browse?category=fashion&language=French  (French Fashion programs)
    - /browse?language=German&category=technology
    """
    db_url = _require_db_url()
    slug_expr = _slug_expr_sql("p.name")

    where_clauses = []
    params: list[Any] = []

    # Country filter (case-insensitive)
    if country:
        where_clauses.append("EXISTS (SELECT 1 FROM unnest(p.countries) c WHERE c ILIKE %s)")
        params.append(country)

    # Category filter
    if category:
        where_clauses.append("""
            EXISTS (
                SELECT 1 FROM affiliate_wiki.program_categories pc
                JOIN affiliate_wiki.categories c ON c.id = pc.category_id
                WHERE pc.program_id = p.id AND c.slug = %s
            )
        """)
        params.append(category.lower())

    # Network/tracking platform filter
    if network:
        where_clauses.append("r.extracted->>'tracking_platform' ILIKE %s")
        params.append(f"%{network}%")

    # Language filter
    if language:
        where_clauses.append("""
            (
                (jsonb_typeof(r.extracted->'languages') = 'array'
                 AND EXISTS (SELECT 1 FROM jsonb_array_elements_text(r.extracted->'languages') lang WHERE trim(lang) ILIKE %s))
                OR r.extracted->>'languages' ILIKE %s
            )
        """)
        params.extend([language, f"%{language}%"])

    # Search query
    if q and len(q) >= 2:
        where_clauses.append("(p.name ILIKE %s OR p.domain ILIKE %s)")
        params.extend([f"%{q}%", f"%{q}%"])

    where = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    programs = _fetchall(
        db_url,
        f"""
        SELECT
          p.id,
          p.name,
          {slug_expr} as slug,
          p.domain,
          p.countries,
          p.metadata->>'logo_url' as logo_url,
          r.extracted->>'commission_rate' as commission_rate,
          (r.extracted->>'cookie_duration_days')::int as cookie_duration_days,
          r.extracted->>'payout_model' as payout_model,
          r.extracted->>'tracking_platform' as tracking_platform,
          r.extracted->>'signup_url' as signup_url,
          r.extracted->>'deep_researched_at' as deep_researched_at,
          r.extracted->>'languages' as languages,
          (
            SELECT array_agg(c.name)
            FROM affiliate_wiki.program_categories pc
            JOIN affiliate_wiki.categories c ON c.id = pc.category_id
            WHERE pc.program_id = p.id AND pc.is_primary = true
            LIMIT 3
          ) as categories
        FROM affiliate_wiki.programs p
        JOIN affiliate_wiki.program_research r ON r.program_id = p.id
        {where}
        ORDER BY r.extracted->>'deep_researched_at' DESC NULLS LAST, p.name
        LIMIT %s OFFSET %s
        """,
        tuple(params + [limit, offset]),
    )

    # Get total count
    total_row = _fetchone(
        db_url,
        f"""
        SELECT COUNT(*) as total
        FROM affiliate_wiki.programs p
        JOIN affiliate_wiki.program_research r ON r.program_id = p.id
        {where}
        """,
        tuple(params),
    ) or {"total": 0}

    return {
        "filters": {
            "country": country,
            "category": category,
            "network": network,
            "language": language,
            "q": q,
        },
        "programs": programs,
        "total": int(total_row["total"]),
        "limit": limit,
        "offset": offset,
    }


if __name__ == "__main__":
    # For local dev only:
    #   export DATABASE_URL="..."
    #   affiliateprograms-wiki/api/.venv/bin/python affiliateprograms-wiki/api/server.py
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8120")))
