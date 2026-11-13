-- Mettre à jour le search_vector avec 'simple'
UPDATE knowledge_base 
SET search_vector = to_tsvector('simple', COALESCE(title, '') || ' ' || COALESCE(content, ''));

-- Vérifier le contenu
SELECT title, search_vector FROM knowledge_base;

-- Tester la recherche
SELECT title, ts_rank(search_vector, plainto_tsquery('simple', 'tarifs formation')) as rank 
FROM knowledge_base 
WHERE search_vector @@ plainto_tsquery('simple', 'tarifs formation') 
ORDER BY rank DESC;

-- Mettre à jour le trigger
CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := to_tsvector('simple', COALESCE(NEW.title, '') || ' ' || COALESCE(NEW.content, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;