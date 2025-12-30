-- Affiliate Wiki schema (Neon/Postgres)
-- Safe to re-run.

CREATE SCHEMA IF NOT EXISTS affiliate_wiki;

CREATE TABLE IF NOT EXISTS affiliate_wiki.programs (
  id BIGSERIAL PRIMARY KEY,

  source TEXT NOT NULL,
  source_advertiser_id BIGINT NOT NULL,

  name TEXT NOT NULL,
  domain TEXT NULL,
  domains TEXT[] NULL,
  countries TEXT[] NULL,

  partner_type TEXT NULL,
  merchant_ids TEXT[] NULL,

  verticals JSONB NULL,
  metadata JSONB NULL,

  raw JSONB NOT NULL,

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT programs_source_advertiser_uniq UNIQUE (source, source_advertiser_id)
);

CREATE INDEX IF NOT EXISTS programs_name_idx ON affiliate_wiki.programs (name);
CREATE INDEX IF NOT EXISTS programs_domain_idx ON affiliate_wiki.programs (domain);
CREATE INDEX IF NOT EXISTS programs_raw_gin ON affiliate_wiki.programs USING GIN (raw);

-- Research/enrichment state per program (filled later).
CREATE TABLE IF NOT EXISTS affiliate_wiki.program_research (
  program_id BIGINT PRIMARY KEY REFERENCES affiliate_wiki.programs(id) ON DELETE CASCADE,
  status TEXT NOT NULL DEFAULT 'pending',
  last_attempt_at TIMESTAMPTZ NULL,
  last_success_at TIMESTAMPTZ NULL,
  error TEXT NULL,
  extracted JSONB NULL,
  evidence JSONB NULL
);

CREATE INDEX IF NOT EXISTS program_research_status_idx ON affiliate_wiki.program_research (status);

-- CPA networks (seeded + researched similarly to programs)
CREATE TABLE IF NOT EXISTS affiliate_wiki.cpa_networks (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  website TEXT NULL,
  countries TEXT[] NULL,
  raw JSONB NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT cpa_networks_name_uniq UNIQUE (name)
);

CREATE INDEX IF NOT EXISTS cpa_networks_name_idx ON affiliate_wiki.cpa_networks (name);

CREATE TABLE IF NOT EXISTS affiliate_wiki.cpa_network_research (
  cpa_network_id BIGINT PRIMARY KEY REFERENCES affiliate_wiki.cpa_networks(id) ON DELETE CASCADE,
  status TEXT NOT NULL DEFAULT 'pending',
  last_attempt_at TIMESTAMPTZ NULL,
  last_success_at TIMESTAMPTZ NULL,
  error TEXT NULL,
  extracted JSONB NULL,
  evidence JSONB NULL
);

CREATE INDEX IF NOT EXISTS cpa_network_research_status_idx ON affiliate_wiki.cpa_network_research (status);
