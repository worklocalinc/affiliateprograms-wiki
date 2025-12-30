-- Category schema for affiliate programs
-- Supports hierarchical categories with programs in multiple categories

-- Categories table with parent reference for hierarchy
CREATE TABLE IF NOT EXISTS affiliate_wiki.categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL,
    parent_id INTEGER REFERENCES affiliate_wiki.categories(id),
    path TEXT NOT NULL,  -- Full path like "Sports & Outdoors > Racket Sports > Pickleball"
    depth INTEGER NOT NULL DEFAULT 0,
    description TEXT,
    icon VARCHAR(50),  -- emoji or icon name
    program_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(slug, parent_id)
);

-- Index for fast hierarchy queries
CREATE INDEX IF NOT EXISTS idx_categories_parent ON affiliate_wiki.categories(parent_id);
CREATE INDEX IF NOT EXISTS idx_categories_path ON affiliate_wiki.categories(path);
CREATE INDEX IF NOT EXISTS idx_categories_slug ON affiliate_wiki.categories(slug);

-- Junction table for program-category relationships
-- A program can be in multiple categories with a relevance score
CREATE TABLE IF NOT EXISTS affiliate_wiki.program_categories (
    id SERIAL PRIMARY KEY,
    program_id INTEGER NOT NULL REFERENCES affiliate_wiki.programs(id) ON DELETE CASCADE,
    category_id INTEGER NOT NULL REFERENCES affiliate_wiki.categories(id) ON DELETE CASCADE,
    relevance_score FLOAT DEFAULT 1.0,  -- Higher = more relevant to this category
    is_primary BOOLEAN DEFAULT FALSE,   -- Primary category for the program
    assigned_by VARCHAR(50) DEFAULT 'ai',  -- 'ai', 'manual', 'import'
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(program_id, category_id)
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_program_categories_program ON affiliate_wiki.program_categories(program_id);
CREATE INDEX IF NOT EXISTS idx_program_categories_category ON affiliate_wiki.program_categories(category_id);
CREATE INDEX IF NOT EXISTS idx_program_categories_relevance ON affiliate_wiki.program_categories(category_id, relevance_score DESC);

-- Function to update category program counts
CREATE OR REPLACE FUNCTION affiliate_wiki.update_category_counts()
RETURNS TRIGGER AS $$
BEGIN
    -- Update counts for affected categories
    UPDATE affiliate_wiki.categories c
    SET program_count = (
        SELECT COUNT(DISTINCT pc.program_id)
        FROM affiliate_wiki.program_categories pc
        WHERE pc.category_id = c.id
    ),
    updated_at = NOW();
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger to maintain counts
DROP TRIGGER IF EXISTS trigger_update_category_counts ON affiliate_wiki.program_categories;
CREATE TRIGGER trigger_update_category_counts
AFTER INSERT OR DELETE ON affiliate_wiki.program_categories
FOR EACH STATEMENT
EXECUTE FUNCTION affiliate_wiki.update_category_counts();
