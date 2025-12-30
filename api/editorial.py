#!/usr/bin/env python3
"""
AI Editorial Pipeline API Endpoints

Provides authenticated endpoints for:
- LLM Researcher: Submit proposals for changes
- LLM Reviewer: Validate and approve/reject proposals
- LLM SEO Editor: Optimize presentation metadata
- Staleness Patrol: Get broken URLs for auto-fixing

Key design: Models never edit rows directly - all changes go through proposals.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable, Optional
from uuid import UUID

import psycopg
from fastapi import APIRouter, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field


# ============================================
# Database helpers
# ============================================

def _get_db_url() -> str:
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

    raise RuntimeError("DATABASE_URL not set")


def _fetchall(db_url: str, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            if cur.description is None:
                return []
            cols = [d.name for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def _fetchone(db_url: str, sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    rows = _fetchall(db_url, sql, params)
    return rows[0] if rows else None


def _execute(db_url: str, sql: str, params: tuple[Any, ...] = ()) -> None:
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
        conn.commit()


def _execute_returning(db_url: str, sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            if cur.description is None:
                conn.commit()
                return None
            cols = [d.name for d in cur.description]
            row = cur.fetchone()
            conn.commit()
            return dict(zip(cols, row)) if row else None


# ============================================
# Pydantic Models
# ============================================

class ProposalCreate(BaseModel):
    """Request body for creating a proposal."""
    entity_type: str = Field(..., pattern="^(program|category|network)$")
    entity_id: int = Field(..., gt=0)
    changes: dict = Field(..., description="Field changes: {field: new_value}")
    sources: list[dict] = Field(default=[], description="Evidence: [{url, snapshot_hash?, captured_at?}]")
    reasoning: str = Field(default="", max_length=5000)
    raw_llm_response: Optional[str] = Field(default=None, description="Full LLM output for debugging")
    model_used: Optional[str] = Field(default=None, max_length=100)


class ReviewDecision(BaseModel):
    """Request body for reviewing a proposal."""
    decision: str = Field(..., pattern="^(approve|reject|request_changes)$")
    notes: str = Field(default="", max_length=5000)
    validation_results: Optional[dict] = Field(default=None)


class SEOOptimization(BaseModel):
    """Request body for SEO optimization."""
    title: Optional[str] = Field(default=None, max_length=70)
    meta_description: Optional[str] = Field(default=None, max_length=160)
    og_title: Optional[str] = Field(default=None, max_length=70)
    og_description: Optional[str] = Field(default=None, max_length=200)
    og_image: Optional[str] = Field(default=None)
    json_ld: Optional[dict] = Field(default=None)
    internal_links: Optional[list[str]] = Field(default=None)


class URLVerifyRequest(BaseModel):
    """Request body for batch URL verification."""
    urls: list[dict] = Field(..., description="[{program_id, url, url_type}]")


class LinkRuleCreate(BaseModel):
    """Request body for creating a link rewriting rule."""
    match_domain: str = Field(..., max_length=255)
    match_path_pattern: Optional[str] = Field(default=None, max_length=255)
    affiliate_template: str = Field(..., max_length=1000)
    network: Optional[str] = Field(default=None, max_length=100)
    default_tag: Optional[str] = Field(default=None, max_length=100)
    exception_paths: list[str] = Field(default=[])
    priority: int = Field(default=100, ge=0, le=1000)


# ============================================
# Authentication Middleware
# ============================================

def get_agent_key(request: Request, x_agent_key: str = Header(alias="X-Agent-Key")) -> str:
    """Extract agent key from header."""
    return x_agent_key


def validate_agent(allowed_types: list[str], agent_key: str) -> dict:
    """
    Validate agent API key and return agent info.

    Validates X-Agent-Key header against agent_keys table.
    """
    db_url = _get_db_url()

    # Validate agent key
    agent = _fetchone(db_url, """
        SELECT id, name, agent_type, scopes, rate_limit_per_minute
        FROM affiliate_wiki.agent_keys
        WHERE id = %s AND is_enabled = TRUE
          AND (expires_at IS NULL OR expires_at > NOW())
    """, (agent_key,))

    if not agent:
        raise HTTPException(status_code=401, detail="Invalid or expired agent key")

    if agent["agent_type"] not in allowed_types:
        raise HTTPException(
            status_code=403,
            detail=f"Agent type '{agent['agent_type']}' not allowed. Required: {allowed_types}"
        )

    # Update last_used_at and total_requests
    _execute(db_url, """
        UPDATE affiliate_wiki.agent_keys
        SET last_used_at = NOW(), total_requests = total_requests + 1
        WHERE id = %s
    """, (agent_key,))

    return agent


def require_agent_key(allowed_types: list[str]):
    """
    Decorator to require valid agent API key.

    Validates X-Agent-Key header against agent_keys table.
    Sets request.state.agent with agent info if valid.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Get agent key from header
            agent_key = request.headers.get("X-Agent-Key")
            if not agent_key:
                raise HTTPException(status_code=401, detail="Missing X-Agent-Key header")

            # Validate and get agent
            agent = validate_agent(allowed_types, agent_key)

            # Store agent info in request state
            request.state.agent = agent

            return await func(request, *args, **kwargs)
        return wrapper
    return decorator


# ============================================
# Router
# ============================================

router = APIRouter(prefix="/editorial", tags=["Editorial Pipeline"])


# ============================================
# Proposal Endpoints
# ============================================

@router.post("/proposals")
@require_agent_key(["researcher"])
async def create_proposal(request: Request, body: ProposalCreate):
    """
    LLM Researcher submits a proposal for changes.

    Creates a new proposal with status='pending_review'.
    Captures current values for diff generation.
    """
    db_url = _get_db_url()
    agent = request.state.agent

    # Validate entity exists and get current values
    if body.entity_type == "program":
        entity = _fetchone(db_url, """
            SELECT p.id, p.name, r.extracted
            FROM affiliate_wiki.programs p
            LEFT JOIN affiliate_wiki.program_research r ON r.program_id = p.id
            WHERE p.id = %s
        """, (body.entity_id,))
    elif body.entity_type == "category":
        entity = _fetchone(db_url, """
            SELECT id, name, description as extracted
            FROM affiliate_wiki.categories
            WHERE id = %s
        """, (body.entity_id,))
    elif body.entity_type == "network":
        entity = _fetchone(db_url, """
            SELECT n.id, n.name, r.extracted
            FROM affiliate_wiki.cpa_networks n
            LEFT JOIN affiliate_wiki.cpa_network_research r ON r.cpa_network_id = n.id
            WHERE n.id = %s
        """, (body.entity_id,))
    else:
        raise HTTPException(status_code=400, detail=f"Unknown entity_type: {body.entity_type}")

    if not entity:
        raise HTTPException(status_code=404, detail=f"{body.entity_type} not found: {body.entity_id}")

    # Capture previous values for fields being changed
    previous_values = {}
    current_extracted = entity.get("extracted") or {}
    if isinstance(current_extracted, str):
        try:
            current_extracted = json.loads(current_extracted)
        except:
            current_extracted = {}

    for field in body.changes.keys():
        if field in current_extracted:
            previous_values[field] = current_extracted[field]

    # Create proposal
    result = _execute_returning(db_url, """
        INSERT INTO affiliate_wiki.proposals (
            entity_type, entity_id, changes, previous_values,
            sources, reasoning, raw_llm_response,
            researcher_key_id, model_used, status
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending_review')
        RETURNING id, status, created_at
    """, (
        body.entity_type,
        body.entity_id,
        json.dumps(body.changes),
        json.dumps(previous_values),
        json.dumps(body.sources),
        body.reasoning,
        body.raw_llm_response,
        agent["id"],
        body.model_used
    ))

    return {
        "proposal_id": str(result["id"]),
        "status": result["status"],
        "entity": {"type": body.entity_type, "id": body.entity_id, "name": entity["name"]},
        "changes_count": len(body.changes),
        "created_at": result["created_at"].isoformat() if result["created_at"] else None
    }


@router.get("/proposals")
@require_agent_key(["reviewer", "seo_editor", "admin"])
async def list_proposals(
    request: Request,
    status: str = Query(default="pending_review"),
    entity_type: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0)
):
    """Get queue of proposals by status."""
    db_url = _get_db_url()

    where_clauses = ["status = %s"]
    params: list[Any] = [status]

    if entity_type:
        where_clauses.append("entity_type = %s")
        params.append(entity_type)

    where_sql = " AND ".join(where_clauses)

    # Get count
    count_result = _fetchone(db_url, f"""
        SELECT COUNT(*) as total
        FROM affiliate_wiki.proposals
        WHERE {where_sql}
    """, tuple(params))
    total = count_result["total"] if count_result else 0

    # Get proposals with entity info
    params.extend([limit, offset])
    proposals = _fetchall(db_url, f"""
        SELECT
            p.id, p.entity_type, p.entity_id, p.status,
            p.changes, p.previous_values, p.sources, p.reasoning,
            p.researcher_key_id, p.model_used,
            p.reviewer_key_id, p.review_notes, p.validation_results,
            p.seo_metadata,
            p.created_at, p.updated_at,
            CASE
                WHEN p.entity_type = 'program' THEN prog.name
                WHEN p.entity_type = 'category' THEN cat.name
                WHEN p.entity_type = 'network' THEN net.name
            END as entity_name
        FROM affiliate_wiki.proposals p
        LEFT JOIN affiliate_wiki.programs prog ON p.entity_type = 'program' AND p.entity_id = prog.id
        LEFT JOIN affiliate_wiki.categories cat ON p.entity_type = 'category' AND p.entity_id = cat.id
        LEFT JOIN affiliate_wiki.cpa_networks net ON p.entity_type = 'network' AND p.entity_id = net.id
        WHERE {where_sql}
        ORDER BY p.created_at DESC
        LIMIT %s OFFSET %s
    """, tuple(params))

    return {
        "items": [
            {
                "id": str(p["id"]),
                "entity": {"type": p["entity_type"], "id": p["entity_id"], "name": p["entity_name"]},
                "status": p["status"],
                "changes": p["changes"],
                "previous_values": p["previous_values"],
                "sources": p["sources"],
                "reasoning": p["reasoning"],
                "researcher": p["researcher_key_id"],
                "model_used": p["model_used"],
                "reviewer": p["reviewer_key_id"],
                "review_notes": p["review_notes"],
                "validation_results": p["validation_results"],
                "seo_metadata": p["seo_metadata"],
                "created_at": p["created_at"].isoformat() if p["created_at"] else None,
                "updated_at": p["updated_at"].isoformat() if p["updated_at"] else None,
            }
            for p in proposals
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
        "filters": {"status": status, "entity_type": entity_type}
    }


@router.get("/proposals/{proposal_id}")
@require_agent_key(["reviewer", "seo_editor", "admin", "researcher"])
async def get_proposal(request: Request, proposal_id: str):
    """Get a single proposal by ID."""
    db_url = _get_db_url()

    try:
        uuid_val = UUID(proposal_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid proposal ID format")

    proposal = _fetchone(db_url, """
        SELECT
            p.*,
            CASE
                WHEN p.entity_type = 'program' THEN prog.name
                WHEN p.entity_type = 'category' THEN cat.name
                WHEN p.entity_type = 'network' THEN net.name
            END as entity_name
        FROM affiliate_wiki.proposals p
        LEFT JOIN affiliate_wiki.programs prog ON p.entity_type = 'program' AND p.entity_id = prog.id
        LEFT JOIN affiliate_wiki.categories cat ON p.entity_type = 'category' AND p.entity_id = cat.id
        LEFT JOIN affiliate_wiki.cpa_networks net ON p.entity_type = 'network' AND p.entity_id = net.id
        WHERE p.id = %s
    """, (str(uuid_val),))

    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    # Get approval log
    log = _fetchall(db_url, """
        SELECT action, agent_key_id, validation_results, notes, created_at
        FROM affiliate_wiki.approval_log
        WHERE proposal_id = %s
        ORDER BY created_at ASC
    """, (str(uuid_val),))

    return {
        "id": str(proposal["id"]),
        "entity": {"type": proposal["entity_type"], "id": proposal["entity_id"], "name": proposal["entity_name"]},
        "status": proposal["status"],
        "changes": proposal["changes"],
        "previous_values": proposal["previous_values"],
        "sources": proposal["sources"],
        "reasoning": proposal["reasoning"],
        "raw_llm_response": proposal["raw_llm_response"],
        "researcher": proposal["researcher_key_id"],
        "model_used": proposal["model_used"],
        "reviewer": proposal["reviewer_key_id"],
        "review_notes": proposal["review_notes"],
        "validation_results": proposal["validation_results"],
        "seo_editor": proposal["seo_editor_key_id"],
        "seo_metadata": proposal["seo_metadata"],
        "history_id": proposal["history_id"],
        "created_at": proposal["created_at"].isoformat() if proposal["created_at"] else None,
        "updated_at": proposal["updated_at"].isoformat() if proposal["updated_at"] else None,
        "reviewed_at": proposal["reviewed_at"].isoformat() if proposal["reviewed_at"] else None,
        "published_at": proposal["published_at"].isoformat() if proposal["published_at"] else None,
        "approval_log": [
            {
                "action": e["action"],
                "agent": e["agent_key_id"],
                "validation_results": e["validation_results"],
                "notes": e["notes"],
                "at": e["created_at"].isoformat() if e["created_at"] else None
            }
            for e in log
        ]
    }


@router.post("/proposals/{proposal_id}/review")
@require_agent_key(["reviewer", "admin"])
async def review_proposal(request: Request, proposal_id: str, body: ReviewDecision):
    """
    LLM Reviewer validates a proposal.

    Validation gates:
    1. Schema validation (all fields conform to spec)
    2. Provenance check (every claim has source or marked unknown)
    3. URL verification (signup URLs return 200)
    4. Policy check (no cloaking, no JS injection)

    Decision: approve | reject | request_changes
    """
    db_url = _get_db_url()
    agent = request.state.agent

    try:
        uuid_val = UUID(proposal_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid proposal ID format")

    # Get proposal
    proposal = _fetchone(db_url, """
        SELECT id, status, entity_type, entity_id
        FROM affiliate_wiki.proposals
        WHERE id = %s
    """, (str(uuid_val),))

    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    if proposal["status"] not in ("pending_review",):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot review proposal with status '{proposal['status']}'. Must be 'pending_review'."
        )

    # Determine new status
    if body.decision == "approve":
        new_status = "approved"
    elif body.decision == "reject":
        new_status = "rejected"
    else:  # request_changes
        new_status = "pending_review"  # Stays pending but with feedback

    # Update proposal
    _execute(db_url, """
        UPDATE affiliate_wiki.proposals
        SET status = %s,
            reviewer_key_id = %s,
            review_notes = %s,
            validation_results = %s,
            reviewed_at = NOW()
        WHERE id = %s
    """, (
        new_status,
        agent["id"],
        body.notes,
        json.dumps(body.validation_results) if body.validation_results else None,
        str(uuid_val)
    ))

    # Add to approval log
    _execute(db_url, """
        INSERT INTO affiliate_wiki.approval_log (proposal_id, action, agent_key_id, validation_results, notes)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        str(uuid_val),
        body.decision,
        agent["id"],
        json.dumps(body.validation_results) if body.validation_results else None,
        body.notes
    ))

    return {
        "proposal_id": str(uuid_val),
        "decision": body.decision,
        "new_status": new_status,
        "reviewer": agent["id"],
        "reviewed_at": datetime.now(timezone.utc).isoformat()
    }


@router.post("/proposals/{proposal_id}/seo")
@require_agent_key(["seo_editor", "admin"])
async def optimize_seo(request: Request, proposal_id: str, body: SEOOptimization):
    """
    LLM SEO Editor optimizes presentation fields.

    Only allowed to modify presentation metadata:
    - title, meta_description
    - og_title, og_description, og_image
    - json_ld (structured data)
    - internal_links (suggestions)

    Cannot modify core data fields.
    """
    db_url = _get_db_url()
    agent = request.state.agent

    try:
        uuid_val = UUID(proposal_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid proposal ID format")

    # Get proposal
    proposal = _fetchone(db_url, """
        SELECT id, status
        FROM affiliate_wiki.proposals
        WHERE id = %s
    """, (str(uuid_val),))

    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    if proposal["status"] not in ("approved", "pending_seo"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot add SEO to proposal with status '{proposal['status']}'. Must be 'approved' or 'pending_seo'."
        )

    # Build SEO metadata
    seo_metadata = {}
    if body.title:
        seo_metadata["title"] = body.title
    if body.meta_description:
        seo_metadata["meta_description"] = body.meta_description
    if body.og_title:
        seo_metadata["og_title"] = body.og_title
    if body.og_description:
        seo_metadata["og_description"] = body.og_description
    if body.og_image:
        seo_metadata["og_image"] = body.og_image
    if body.json_ld:
        seo_metadata["json_ld"] = body.json_ld
    if body.internal_links:
        seo_metadata["internal_links"] = body.internal_links

    # Update proposal
    _execute(db_url, """
        UPDATE affiliate_wiki.proposals
        SET seo_metadata = %s,
            seo_editor_key_id = %s,
            seo_processed_at = NOW(),
            status = 'pending_seo'
        WHERE id = %s
    """, (
        json.dumps(seo_metadata),
        agent["id"],
        str(uuid_val)
    ))

    # Add to approval log
    _execute(db_url, """
        INSERT INTO affiliate_wiki.approval_log (proposal_id, action, agent_key_id, notes)
        VALUES (%s, 'seo_complete', %s, %s)
    """, (
        str(uuid_val),
        agent["id"],
        f"Added SEO metadata: {list(seo_metadata.keys())}"
    ))

    return {
        "proposal_id": str(uuid_val),
        "seo_metadata": seo_metadata,
        "seo_editor": agent["id"],
        "processed_at": datetime.now(timezone.utc).isoformat()
    }


@router.post("/proposals/{proposal_id}/publish")
@require_agent_key(["reviewer", "admin"])
async def publish_proposal(request: Request, proposal_id: str):
    """
    Apply approved proposal to canonical database.

    Requirements:
    - Proposal status must be 'approved' or 'pending_seo'
    - Creates history record with full diff
    - Updates program_research.extracted
    """
    db_url = _get_db_url()
    agent = request.state.agent

    try:
        uuid_val = UUID(proposal_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid proposal ID format")

    # Get full proposal
    proposal = _fetchone(db_url, """
        SELECT *
        FROM affiliate_wiki.proposals
        WHERE id = %s
    """, (str(uuid_val),))

    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    if proposal["status"] not in ("approved", "pending_seo"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot publish proposal with status '{proposal['status']}'. Must be 'approved' or 'pending_seo'."
        )

    # Get current extracted data
    if proposal["entity_type"] == "program":
        current = _fetchone(db_url, """
            SELECT extracted FROM affiliate_wiki.program_research
            WHERE program_id = %s
        """, (proposal["entity_id"],))
        current_extracted = current["extracted"] if current else {}
    else:
        # For now, only supporting programs
        raise HTTPException(status_code=400, detail="Only program proposals can be published currently")

    # Merge changes
    new_extracted = dict(current_extracted) if current_extracted else {}
    changes = proposal["changes"]
    if isinstance(changes, str):
        changes = json.loads(changes)

    for field, value in changes.items():
        new_extracted[field] = value

    # Add provenance
    new_extracted["last_editorial_update"] = datetime.now(timezone.utc).isoformat()
    new_extracted["editorial_proposal_id"] = str(proposal["id"])

    # Add SEO metadata if present
    if proposal["seo_metadata"]:
        seo = proposal["seo_metadata"]
        if isinstance(seo, str):
            seo = json.loads(seo)
        new_extracted["seo_metadata"] = seo

    # Create history record
    history_result = _execute_returning(db_url, """
        INSERT INTO affiliate_wiki.program_research_history (
            program_id, previous_extracted, new_extracted, diff,
            agent_type, agent_id, model_used, sources, reasoning
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        proposal["entity_id"],
        json.dumps(current_extracted) if current_extracted else None,
        json.dumps(new_extracted),
        json.dumps(changes),
        "editorial",
        agent["id"],
        proposal["model_used"],
        json.dumps(proposal["sources"]) if proposal["sources"] else None,
        proposal["reasoning"]
    ))

    history_id = history_result["id"] if history_result else None

    # Update program_research
    _execute(db_url, """
        UPDATE affiliate_wiki.program_research
        SET extracted = %s, last_success_at = NOW()
        WHERE program_id = %s
    """, (json.dumps(new_extracted), proposal["entity_id"]))

    # Update proposal status
    _execute(db_url, """
        UPDATE affiliate_wiki.proposals
        SET status = 'published',
            published_at = NOW(),
            history_id = %s
        WHERE id = %s
    """, (history_id, str(uuid_val)))

    # Add to approval log
    _execute(db_url, """
        INSERT INTO affiliate_wiki.approval_log (proposal_id, action, agent_key_id, notes)
        VALUES (%s, 'publish', %s, %s)
    """, (
        str(uuid_val),
        agent["id"],
        f"Published to program_research. History ID: {history_id}"
    ))

    return {
        "proposal_id": str(uuid_val),
        "status": "published",
        "history_id": history_id,
        "entity_id": proposal["entity_id"],
        "changes_applied": list(changes.keys()),
        "published_at": datetime.now(timezone.utc).isoformat(),
        "publisher": agent["id"]
    }


# ============================================
# Verification Endpoints
# ============================================

@router.post("/verify/urls")
@require_agent_key(["reviewer", "admin"])
async def verify_urls(request: Request, body: URLVerifyRequest):
    """
    Verify list of URLs, store results in verification_runs.
    Used by reviewer to validate signup URLs before approval.
    """
    import aiohttp
    import asyncio

    db_url = _get_db_url()
    results = []

    async def check_url(item: dict) -> dict:
        program_id = item.get("program_id")
        url = item.get("url")
        url_type = item.get("url_type", "signup")

        if not url:
            return {"program_id": program_id, "url": url, "status": "error", "error": "No URL provided"}

        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                start = datetime.now()
                async with session.head(url, allow_redirects=True) as resp:
                    elapsed = (datetime.now() - start).total_seconds() * 1000

                    # Build redirect chain
                    redirect_chain = []
                    if resp.history:
                        for r in resp.history:
                            redirect_chain.append({"url": str(r.url), "code": r.status})

                    status = "success" if resp.status < 400 else "broken"
                    if resp.history:
                        status = "redirect"

                    result = {
                        "program_id": program_id,
                        "url": url,
                        "url_type": url_type,
                        "status": status,
                        "http_code": resp.status,
                        "final_url": str(resp.url),
                        "redirect_chain": redirect_chain,
                        "response_time_ms": int(elapsed)
                    }

                    # Store in database
                    _execute(db_url, """
                        INSERT INTO affiliate_wiki.verification_runs
                        (program_id, url, url_type, status, http_code, redirect_chain, final_url, response_time_ms)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        program_id, url, url_type, status, resp.status,
                        json.dumps(redirect_chain) if redirect_chain else None,
                        str(resp.url), int(elapsed)
                    ))

                    return result

        except asyncio.TimeoutError:
            _execute(db_url, """
                INSERT INTO affiliate_wiki.verification_runs
                (program_id, url, url_type, status)
                VALUES (%s, %s, %s, 'timeout')
            """, (program_id, url, url_type))
            return {"program_id": program_id, "url": url, "status": "timeout"}

        except Exception as e:
            _execute(db_url, """
                INSERT INTO affiliate_wiki.verification_runs
                (program_id, url, url_type, status)
                VALUES (%s, %s, %s, 'broken')
            """, (program_id, url, url_type))
            return {"program_id": program_id, "url": url, "status": "broken", "error": str(e)}

    # Run all checks in parallel
    results = await asyncio.gather(*[check_url(item) for item in body.urls])

    return {
        "verified": len(results),
        "results": results,
        "summary": {
            "success": sum(1 for r in results if r.get("status") == "success"),
            "redirect": sum(1 for r in results if r.get("status") == "redirect"),
            "broken": sum(1 for r in results if r.get("status") == "broken"),
            "timeout": sum(1 for r in results if r.get("status") == "timeout"),
        }
    }


@router.get("/verify/broken")
@require_agent_key(["researcher", "reviewer", "admin"])
async def get_broken_urls(
    request: Request,
    limit: int = Query(default=100, ge=1, le=500),
    min_age_hours: int = Query(default=24, ge=0)
):
    """
    Get programs with broken/stale URLs.
    Staleness patrol uses this to auto-propose fixes.
    """
    db_url = _get_db_url()

    broken = _fetchall(db_url, """
        SELECT DISTINCT ON (v.program_id)
            v.program_id,
            v.url,
            v.url_type,
            v.status,
            v.http_code,
            v.verified_at,
            p.name as program_name,
            p.domain
        FROM affiliate_wiki.verification_runs v
        JOIN affiliate_wiki.programs p ON p.id = v.program_id
        WHERE v.status IN ('broken', 'timeout')
          AND v.verified_at < NOW() - INTERVAL '%s hours'
        ORDER BY v.program_id, v.verified_at DESC
        LIMIT %s
    """, (min_age_hours, limit))

    return {
        "items": [
            {
                "program_id": b["program_id"],
                "program_name": b["program_name"],
                "domain": b["domain"],
                "url": b["url"],
                "url_type": b["url_type"],
                "status": b["status"],
                "http_code": b["http_code"],
                "verified_at": b["verified_at"].isoformat() if b["verified_at"] else None
            }
            for b in broken
        ],
        "total": len(broken),
        "limit": limit,
        "min_age_hours": min_age_hours
    }


# ============================================
# Link Rules Endpoints
# ============================================

@router.get("/link-rules")
async def get_link_rules():
    """Get active link rewriting rules for SSR layer."""
    db_url = _get_db_url()

    rules = _fetchall(db_url, """
        SELECT id, match_domain, match_path_pattern, affiliate_template,
               network, default_tag, utm_source, utm_medium, utm_campaign,
               exception_paths, priority
        FROM affiliate_wiki.link_rules
        WHERE is_enabled = TRUE
        ORDER BY priority DESC
    """)

    return {
        "rules": rules,
        "total": len(rules)
    }


@router.post("/link-rules")
@require_agent_key(["admin"])
async def create_link_rule(request: Request, body: LinkRuleCreate):
    """Create deterministic link rewriting rule."""
    db_url = _get_db_url()

    result = _execute_returning(db_url, """
        INSERT INTO affiliate_wiki.link_rules (
            match_domain, match_path_pattern, affiliate_template,
            network, default_tag, exception_paths, priority
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id, created_at
    """, (
        body.match_domain,
        body.match_path_pattern,
        body.affiliate_template,
        body.network,
        body.default_tag,
        body.exception_paths,
        body.priority
    ))

    return {
        "id": result["id"],
        "match_domain": body.match_domain,
        "created_at": result["created_at"].isoformat() if result["created_at"] else None
    }


# ============================================
# Stats Endpoint
# ============================================

@router.get("/stats")
@require_agent_key(["researcher", "reviewer", "seo_editor", "admin"])
async def get_editorial_stats(request: Request):
    """Get editorial pipeline statistics."""
    db_url = _get_db_url()

    stats = _fetchone(db_url, """
        SELECT
            (SELECT COUNT(*) FROM affiliate_wiki.proposals WHERE status = 'pending_review') as pending_review,
            (SELECT COUNT(*) FROM affiliate_wiki.proposals WHERE status = 'approved') as approved,
            (SELECT COUNT(*) FROM affiliate_wiki.proposals WHERE status = 'pending_seo') as pending_seo,
            (SELECT COUNT(*) FROM affiliate_wiki.proposals WHERE status = 'published') as published,
            (SELECT COUNT(*) FROM affiliate_wiki.proposals WHERE status = 'rejected') as rejected,
            (SELECT COUNT(*) FROM affiliate_wiki.program_research_history) as total_changes,
            (SELECT COUNT(*) FROM affiliate_wiki.verification_runs WHERE status = 'broken') as broken_urls,
            (SELECT COUNT(*) FROM affiliate_wiki.link_rules WHERE is_enabled) as active_rules
    """)

    return {
        "proposals": {
            "pending_review": stats["pending_review"],
            "approved": stats["approved"],
            "pending_seo": stats["pending_seo"],
            "published": stats["published"],
            "rejected": stats["rejected"],
        },
        "history": {
            "total_changes": stats["total_changes"]
        },
        "verification": {
            "broken_urls": stats["broken_urls"]
        },
        "link_rules": {
            "active": stats["active_rules"]
        }
    }
