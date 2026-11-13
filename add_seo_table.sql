CREATE TABLE IF NOT EXISTS seo_analyses (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT NOW(),
    url TEXT NOT NULL,
    focus_keyword VARCHAR(255),
    title_found VARCHAR(255),
    meta_description TEXT,
    h1_count INT,
    images_without_alt INT,
    internal_links INT,
    external_links INT,
    word_count INT,
    seo_score INT,
    strengths JSONB,
    weaknesses JSONB,
    recommendations JSONB,
    html_snippet TEXT
);

CREATE INDEX IF NOT EXISTS idx_seo_url ON seo_analyses(url);
CREATE INDEX IF NOT EXISTS idx_seo_score ON seo_analyses(seo_score);