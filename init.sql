-- Table des conversations (agent administratif)
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT NOW(),
    message_type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    response_suggestions JSONB,
    context_used TEXT
);

-- Table des documents marketing (flyers, cartes de visite)
CREATE TABLE IF NOT EXISTS marketing_documents (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT NOW(),
    document_type VARCHAR(50) NOT NULL,
    file_path TEXT NOT NULL,
    analysis_feedback TEXT,
    html_suggestion TEXT,
    improvements JSONB
);

-- Table des prospects (agent commercial)
CREATE TABLE IF NOT EXISTS prospects (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT NOW(),
    nom_entreprise VARCHAR(255) NOT NULL,
    type_entreprise VARCHAR(100),
    secteur VARCHAR(100),
    localisation VARCHAR(255),
    point_douleur TEXT,
    argumentaire_ia TEXT,
    action_recommandee TEXT,
    statut VARCHAR(50) DEFAULT 'nouveau'
);

-- Table des factures (agent comptable)
CREATE TABLE IF NOT EXISTS factures (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT NOW(),
    date_facture DATE NOT NULL,
    fournisseur VARCHAR(255) NOT NULL,
    montant_ht FLOAT NOT NULL,
    montant_tva FLOAT NOT NULL,
    montant_ttc FLOAT NOT NULL,
    numero_facture VARCHAR(100),
    lignes JSONB
);

-- Table pour la mémoire des agents
CREATE TABLE IF NOT EXISTS agent_memory (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT NOW(),
    agent_type VARCHAR(50) NOT NULL,
    interaction_type VARCHAR(100),
    input_data JSONB,
    output_data JSONB,
    user_feedback TEXT
);

-- Index pour les recherches
CREATE INDEX IF NOT EXISTS idx_conversations_type ON conversations(message_type);
CREATE INDEX IF NOT EXISTS idx_prospects_secteur ON prospects(secteur);
CREATE INDEX IF NOT EXISTS idx_factures_date ON factures(date_facture);
CREATE INDEX IF NOT EXISTS idx_factures_fournisseur ON factures(fournisseur);