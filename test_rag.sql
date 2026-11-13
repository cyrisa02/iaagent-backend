-- 1. Reconstruire le search_vector avec 'french'
UPDATE knowledge_base 
SET search_vector = to_tsvector('french', COALESCE(title, '') || ' ' || COALESCE(content, ''));

-- 2. Test simple : chercher "tarif"
SELECT title, ts_rank(search_vector, to_tsquery('french', 'tarif')) as rank 
FROM knowledge_base 
WHERE search_vector @@ to_tsquery('french', 'tarif') 
ORDER BY rank DESC;

-- 3. Test avec OR : chercher "tarif" OU "format"
SELECT title, ts_rank(search_vector, to_tsquery('french', 'tarif | format')) as rank 
FROM knowledge_base 
WHERE search_vector @@ to_tsquery('french', 'tarif | format') 
ORDER BY rank DESC;