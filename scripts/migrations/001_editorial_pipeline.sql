-- ============================================
-- AI Editorial Pipeline Migration
-- Version: 001
-- Date: 2024-12-30
--
-- Creates tables for:
-- 1. Provenance tracking (history, verification, assets)
-- 2. Editorial pipeline (proposals, agent keys, audit log)
-- 3. Link rewriting rules
-- ============================================

-- ============================================
-- PROVENANCE TABLES
-- ============================================

-- Append-only history of all research changes
CREATE TABLE IF NOT EXISTS affiliate_wiki.program_research_history (
    id BIGSERIAL PRIMARY KEY,
    program_id BIGINT NOT NULL REFERENCES affiliate_wiki.programs(id) ON DELETE CASCADE,

    -- What changed
    previous_extracted JSONB,
    new_extracted JSONB NOT NULL,
    diff JSONB NOT NULL,  -- JSON Patch format (RFC 6902)

    -- Who/what made the change
    agent_type TEXT NOT NULL,  -- 'researcher', 'reviewer', 'seo_editor', 'manual', 'legacy'
    agent_id TEXT,  -- API key ID or user ID
    model_used TEXT,  -- 'kimi-k2', 'gpt-4', 'human'

    -- Evidence
    sources JSONB,  -- [{url, snapshot_hash, captured_at}]
    reasoning TEXT,  -- Why the change was made

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_history_program ON affiliate_wiki.program_research_history(program_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_history_agent ON affiliate_wiki.program_research_history(agent_type, created_at DESC);

COMMENT ON TABLE affiliate_wiki.program_research_history IS 'Append-only audit trail of all changes to program research data';


-- URL verification tracking
CREATE TABLE IF NOT EXISTS affiliate_wiki.verification_runs (
    id BIGSERIAL PRIMARY KEY,
    program_id BIGINT NOT NULL REFERENCES affiliate_wiki.programs(id) ON DELETE CASCADE,

    -- What was verified
    url TEXT NOT NULL,
    url_type TEXT NOT NULL,  -- 'signup', 'affiliate_page', 'deep_link', 'merchant_site'

    -- Results
    status TEXT NOT NULL,  -- 'success', 'redirect', 'broken', 'timeout', 'blocked'
    http_code INT,
    redirect_chain JSONB,  -- [{url, code}]
    final_url TEXT,

    -- Timing
    response_time_ms INT,
    verified_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    next_check_at TIMESTAMPTZ  -- For scheduling re-verification
);

CREATE INDEX IF NOT EXISTS idx_verification_program ON affiliate_wiki.verification_runs(program_id, verified_at DESC);
CREATE INDEX IF NOT EXISTS idx_verification_status ON affiliate_wiki.verification_runs(status, next_check_at);
CREATE INDEX IF NOT EXISTS idx_verification_broken ON affiliate_wiki.verification_runs(status) WHERE status IN ('broken', 'timeout');

COMMENT ON TABLE affiliate_wiki.verification_runs IS 'URL health check results for staleness detection';


-- Asset storage (screenshots, logos, creatives)
CREATE TABLE IF NOT EXISTS affiliate_wiki.assets (
    id BIGSERIAL PRIMARY KEY,

    -- What it belongs to
    program_id BIGINT REFERENCES affiliate_wiki.programs(id) ON DELETE CASCADE,
    category_id INT REFERENCES affiliate_wiki.categories(id) ON DELETE CASCADE,

    -- Asset metadata
    asset_type TEXT NOT NULL,  -- 'logo', 'screenshot', 'creative', 'payment_proof'
    storage_path TEXT NOT NULL,  -- Object storage path or URL
    file_hash TEXT NOT NULL,  -- SHA256 for deduplication
    mime_type TEXT NOT NULL,
    file_size_bytes INT NOT NULL,

    -- Dimensions (for images)
    width INT,
    height INT,

    -- AI-generated metadata
    title TEXT,
    alt_text TEXT,
    description TEXT,  -- "What this demonstrates"

    -- Provenance
    source_url TEXT,  -- Where it came from
    captured_at TIMESTAMPTZ,
    rights_confirmed BOOLEAN DEFAULT FALSE,  -- Legal clearance
    rights_notes TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT asset_has_parent CHECK (program_id IS NOT NULL OR category_id IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_assets_program ON affiliate_wiki.assets(program_id) WHERE program_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_assets_category ON affiliate_wiki.assets(category_id) WHERE category_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_assets_hash ON affiliate_wiki.assets(file_hash);

COMMENT ON TABLE affiliate_wiki.assets IS 'Screenshots, logos, and promotional creatives with provenance';


-- Deterministic link rewriting rules
CREATE TABLE IF NOT EXISTS affiliate_wiki.link_rules (
    id SERIAL PRIMARY KEY,

    -- Matching
    match_domain TEXT NOT NULL,  -- 'amazon.com', '*.shopify.com'
    match_path_pattern TEXT,  -- '/products/*' (optional)

    -- Rewriting
    affiliate_template TEXT NOT NULL,  -- 'https://tracker.example.com/click?url={url}&tag={tag}'
    network TEXT,  -- 'amazon', 'impact', 'shareasale'
    default_tag TEXT,  -- Our affiliate ID

    -- UTM defaults
    utm_source TEXT DEFAULT 'affiliateprograms.wiki',
    utm_medium TEXT DEFAULT 'referral',
    utm_campaign TEXT,

    -- Exceptions (paths that must NOT be rewritten)
    exception_paths TEXT[],  -- ['/login', '/terms', '/privacy', '/help']

    -- Control
    priority INT DEFAULT 100,  -- Higher = checked first
    is_enabled BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_link_rules_domain ON affiliate_wiki.link_rules(match_domain, match_path_pattern) WHERE is_enabled;
CREATE INDEX IF NOT EXISTS idx_link_rules_priority ON affiliate_wiki.link_rules(priority DESC) WHERE is_enabled;

COMMENT ON TABLE affiliate_wiki.link_rules IS 'Deterministic affiliate link rewriting rules (not LLM-based)';


-- ============================================
-- EDITORIAL PIPELINE TABLES
-- ============================================

-- Agent API keys with scoped permissions
CREATE TABLE IF NOT EXISTS affiliate_wiki.agent_keys (
    id TEXT PRIMARY KEY,  -- 'ak_researcher_001'
    name TEXT NOT NULL,  -- Human-readable name

    -- Permissions
    agent_type TEXT NOT NULL,  -- 'researcher', 'reviewer', 'seo_editor', 'admin'
    scopes TEXT[] NOT NULL,  -- ['propose:program', 'propose:category', 'read:all']

    -- Rate limiting
    rate_limit_per_minute INT DEFAULT 60,
    rate_limit_per_day INT DEFAULT 10000,

    -- Tracking
    last_used_at TIMESTAMPTZ,
    total_requests BIGINT DEFAULT 0,

    -- Control
    is_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,

    CONSTRAINT valid_agent_type CHECK (agent_type IN ('researcher', 'reviewer', 'seo_editor', 'admin'))
);

COMMENT ON TABLE affiliate_wiki.agent_keys IS 'API keys for LLM agents with scoped permissions';


-- Editorial proposals (the heart of the pipeline)
CREATE TABLE IF NOT EXISTS affiliate_wiki.proposals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- What's being changed
    entity_type TEXT NOT NULL,  -- 'program', 'category', 'network', 'asset'
    entity_id BIGINT NOT NULL,  -- program_id, category_id, etc.

    -- The proposed changes
    changes JSONB NOT NULL,  -- {field: new_value} format
    previous_values JSONB,  -- Snapshot of values before change

    -- Evidence/justification
    sources JSONB,  -- [{url, snapshot_hash, captured_at}]
    reasoning TEXT,
    raw_llm_response TEXT,  -- Full LLM output for debugging

    -- Workflow state
    status TEXT NOT NULL DEFAULT 'pending_review',
    -- States: pending_review, approved, rejected, pending_seo, published

    -- Who proposed it
    researcher_key_id TEXT REFERENCES affiliate_wiki.agent_keys(id),
    model_used TEXT,

    -- Review info
    reviewer_key_id TEXT REFERENCES affiliate_wiki.agent_keys(id),
    review_notes TEXT,
    validation_results JSONB,  -- {schema_valid, urls_verified, policy_passed, ...}
    reviewed_at TIMESTAMPTZ,

    -- SEO processing
    seo_editor_key_id TEXT REFERENCES affiliate_wiki.agent_keys(id),
    seo_metadata JSONB,  -- {title, description, og_*, json_ld}
    seo_processed_at TIMESTAMPTZ,

    -- Publication
    published_at TIMESTAMPTZ,
    history_id BIGINT,  -- Link to program_research_history entry after publish

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_entity_type CHECK (entity_type IN ('program', 'category', 'network', 'asset')),
    CONSTRAINT valid_status CHECK (status IN ('pending_review', 'approved', 'rejected', 'pending_seo', 'published'))
);

CREATE INDEX IF NOT EXISTS idx_proposals_status ON affiliate_wiki.proposals(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_proposals_entity ON affiliate_wiki.proposals(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_proposals_pending ON affiliate_wiki.proposals(status, created_at) WHERE status IN ('pending_review', 'approved');
CREATE INDEX IF NOT EXISTS idx_proposals_researcher ON affiliate_wiki.proposals(researcher_key_id, created_at DESC);

COMMENT ON TABLE affiliate_wiki.proposals IS 'Editorial change proposals from LLM agents - core of the pipeline';


-- Audit log for all approvals/rejections
CREATE TABLE IF NOT EXISTS affiliate_wiki.approval_log (
    id BIGSERIAL PRIMARY KEY,
    proposal_id UUID NOT NULL REFERENCES affiliate_wiki.proposals(id) ON DELETE CASCADE,

    action TEXT NOT NULL,  -- 'approve', 'reject', 'request_changes', 'publish'
    agent_key_id TEXT REFERENCES affiliate_wiki.agent_keys(id),

    -- Validation results at time of action
    validation_results JSONB,  -- {schema_valid, urls_verified, policy_passed}
    notes TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_action CHECK (action IN ('approve', 'reject', 'request_changes', 'publish', 'seo_complete'))
);

CREATE INDEX IF NOT EXISTS idx_approval_log_proposal ON affiliate_wiki.approval_log(proposal_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_approval_log_agent ON affiliate_wiki.approval_log(agent_key_id, created_at DESC);

COMMENT ON TABLE affiliate_wiki.approval_log IS 'Immutable audit trail of all proposal decisions';


-- ============================================
-- PERFORMANCE INDEXES (from DeepCode analysis)
-- ============================================

-- Expression index for deep_researched filtering (fixes slow queries)
CREATE INDEX IF NOT EXISTS idx_research_deep_at ON affiliate_wiki.program_research
USING BTREE ((extracted->>'deep_researched_at') DESC NULLS LAST);

-- GIN index for country array searches
CREATE INDEX IF NOT EXISTS idx_programs_countries ON affiliate_wiki.programs USING GIN (countries);

-- Partial index for success status
CREATE INDEX IF NOT EXISTS idx_research_success ON affiliate_wiki.program_research (last_success_at DESC)
WHERE status = 'success';


-- ============================================
-- TRIGGER: Update proposals.updated_at
-- ============================================

CREATE OR REPLACE FUNCTION affiliate_wiki.update_proposal_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_proposal_timestamp ON affiliate_wiki.proposals;
CREATE TRIGGER trigger_update_proposal_timestamp
    BEFORE UPDATE ON affiliate_wiki.proposals
    FOR EACH ROW
    EXECUTE FUNCTION affiliate_wiki.update_proposal_timestamp();


-- ============================================
-- INITIAL DATA: Create default agent keys
-- ============================================

INSERT INTO affiliate_wiki.agent_keys (id, name, agent_type, scopes)
VALUES
    ('ak_researcher_default', 'Default Researcher', 'researcher', ARRAY['propose:program', 'propose:category', 'read:all']),
    ('ak_reviewer_default', 'Default Reviewer', 'reviewer', ARRAY['review:all', 'publish:all', 'read:all']),
    ('ak_seo_default', 'Default SEO Editor', 'seo_editor', ARRAY['seo:all', 'read:all']),
    ('ak_admin_default', 'Default Admin', 'admin', ARRAY['*'])
ON CONFLICT (id) DO NOTHING;


-- ============================================
-- VIEWS for common queries
-- ============================================

-- Pending proposals with program info
CREATE OR REPLACE VIEW affiliate_wiki.pending_proposals AS
SELECT
    p.id,
    p.entity_type,
    p.entity_id,
    p.status,
    p.changes,
    p.reasoning,
    p.created_at,
    prog.name as program_name,
    prog.domain as program_domain
FROM affiliate_wiki.proposals p
LEFT JOIN affiliate_wiki.programs prog ON p.entity_type = 'program' AND p.entity_id = prog.id
WHERE p.status IN ('pending_review', 'approved', 'pending_seo')
ORDER BY p.created_at DESC;

-- Broken URLs needing attention
CREATE OR REPLACE VIEW affiliate_wiki.broken_urls AS
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
ORDER BY v.program_id, v.verified_at DESC;


-- ============================================
-- DONE
-- ============================================
