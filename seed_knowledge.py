import psycopg

DB_CONFIG = "postgresql://iaagent_user:iaagent_secret_password@localhost/iaagent_db"

documents = [
    {
        "title": "Formations IA disponibles",
        "content": "Nous proposons 3 formations : 1) IA Fondamentale (1 jour, 450€) pour découvrir les bases de l'intelligence artificielle. 2) IA pour PME (2 jours, 900€) pour intégrer l'IA dans votre business. 3) IA Avancée (3 jours, 1500€) pour les développeurs souhaitant créer leurs propres outils IA.",
        "category": "formations"
    },
    {
        "title": "Services de consulting IA",
        "content": "Consulting IA sur mesure : audit de vos processus (500€), recommandations d'outils IA adaptés (800€), accompagnement à l'implémentation (150€/heure). Nous travaillons avec les PME/TPE de Soissons et environs.",
        "category": "services"
    },
    {
        "title": "Tarifs et conditions",
        "content": "Paiement à 30% à la commande, 70% à la livraison. Devis gratuit pour tout projet. Déplacement inclus dans un rayon de 50km autour de Soissons. Au-delà, frais de déplacement de 0.50€/km.",
        "category": "tarifs"
    },
    {
        "title": "FAQ - Questions fréquentes",
        "content": "Q: Faut-il des connaissances techniques ? R: Non, nos formations s'adaptent à tous les niveaux. Q: Combien de temps pour voir des résultats ? R: En moyenne 2-3 semaines après implémentation. Q: Quels outils utilisez-vous ? R: Nous sommes indépendants et recommandons les meilleurs outils selon vos besoins (ChatGPT, Claude, outils open-source).",
        "category": "faq"
    }
]

conn = psycopg.connect(DB_CONFIG)
with conn.cursor() as cur:
    for doc in documents:
        cur.execute(
            "INSERT INTO knowledge_base (title, content, category) VALUES (%s, %s, %s)",
            (doc["title"], doc["content"], doc["category"])
        )
    conn.commit()
    print(f"[SEED] {len(documents)} documents ajoutés à la base de connaissances")
conn.close()