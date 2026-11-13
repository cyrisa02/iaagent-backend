CREATE TABLE IF NOT EXISTS knowledge_base (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT NOW(),
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(50), -- 'tarifs', 'formations', 'cgv', 'services', 'faq'
    search_vector tsvector
);

-- Index pour la recherche full-text
CREATE INDEX IF NOT EXISTS idx_knowledge_search ON knowledge_base USING GIN(search_vector);

-- Trigger pour mettre à jour automatiquement le search_vector
CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := to_tsvector('french', COALESCE(NEW.title, '') || ' ' || COALESCE(NEW.content, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER knowledge_search_update
BEFORE INSERT OR UPDATE ON knowledge_base
FOR EACH ROW
EXECUTE FUNCTION update_search_vector();