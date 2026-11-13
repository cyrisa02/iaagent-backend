import os
import json
import base64
import threading
import psycopg
from psycopg.rows import dict_row
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from groq import Groq
import instructor
from dotenv import load_dotenv
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse

load_dotenv()

app = FastAPI(title="IA Agent - Multi-Agents Consulting")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURATION ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GOOGLE_APPS_SCRIPT_URL = os.getenv("GOOGLE_APPS_SCRIPT_URL")
DB_USER = os.getenv("DB_USER", "iaagent_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "iaagent_secret_password")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "iaagent_db")

if not GROQ_API_KEY or not GOOGLE_APPS_SCRIPT_URL:
    raise ValueError("Variables GROQ_API_KEY ou GOOGLE_APPS_SCRIPT_URL manquantes")

groq_client = instructor.from_groq(
    Groq(api_key=GROQ_API_KEY),
    mode=instructor.Mode.JSON
)

def get_db_connection():
    return psycopg.connect(
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}",
        row_factory=dict_row
    )

# --- SCHÉMAS PYDANTIC ---
class LigneFacture(BaseModel):
    designation: str
    libelle: Optional[str] = None  # Description longue si présente
    quantite: int = 1
    prixFinal: float

class ExtractionFacture(BaseModel):
    date: str = Field(description="Format YYYY-MM-DD")
    fournisseur: str
    montant_ht: float
    montant_tva: float
    montant_ttc: float
    numero_facture: Optional[str] = None
    lignes: Optional[List[dict]] = None

class ImageRequest(BaseModel):
    image_base64: str

class MessageRequest(BaseModel):
    content: str
    type: str

class AgentResponse(BaseModel):
    suggestions: List[str]
    context: Optional[str] = None

class MarketingAnalysis(BaseModel):
    feedback: str
    improvements: List[str]
    html_suggestion: Optional[str] = None

class ProspectStrategy(BaseModel):
    cible: str
    point_de_douleur: str
    argumentaire_ia: str
    action: str

class KnowledgeDocument(BaseModel):
    title: str
    content: str
    category: str

class SEOAnalysis(BaseModel):
    url: str
    seo_score: int = Field(description="Score SEO de 0 à 100")
    title_found: Optional[str] = None
    meta_description: Optional[str] = None
    h1_count: int
    images_without_alt: int
    internal_links: int
    external_links: int
    word_count: int
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    html_snippet: Optional[str] = None

# --- FONCTIONS UTILITAIRES ---
async def send_to_google_sheets(payload: dict):
    try:
        async with httpx.AsyncClient(timeout=10.0) as http_client:
            response = await http_client.post(
                GOOGLE_APPS_SCRIPT_URL,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            print(f"[SHEETS] Status: {response.status_code}")
    except Exception as e:
        print(f"[SHEETS] Erreur: {e}")

def save_to_db(table: str, data: dict):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            columns = ", ".join(data.keys())
            placeholders = ", ".join(["%s"] * len(data))
            values = list(data.values())
            query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            cur.execute(query, values)
            conn.commit()
            print(f"[DB] Sauvegardé dans {table}")
        conn.close()
    except Exception as e:
        print(f"[DB] Erreur: {e}")

def db_task(table: str, data: dict):
    threading.Thread(target=save_to_db, args=(table, data), daemon=True).start()

def search_knowledge_base(query: str, limit: int = 3) -> list:
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            words = query.split()
            tsquery_str = " | ".join(words)
            cur.execute("""
                SELECT title, content, category,
                       ts_rank(search_vector, to_tsquery('french', %s)) as rank
                FROM knowledge_base
                WHERE search_vector @@ to_tsquery('french', %s)
                ORDER BY rank DESC
                LIMIT %s
            """, (tsquery_str, tsquery_str, limit))
            results = cur.fetchall()
            return [dict(row) for row in results]
        conn.close()
    except Exception as e:
        print(f"[RAG] Erreur: {e}")
        return []

async def fetch_and_parse_url(url: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            title = soup.title.string if soup.title else None
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            meta_description = meta_desc['content'] if meta_desc else None
            
            h1_tags = soup.find_all('h1')
            images = soup.find_all('img')
            images_without_alt = sum(1 for img in images if not img.get('alt'))
            
            links = soup.find_all('a', href=True)
            internal_links = 0
            external_links = 0
            
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            
            for link in links:
                href = link['href']
                if href.startswith('http'):
                    link_domain = urlparse(href).netloc
                    if domain in link_domain:
                        internal_links += 1
                    else:
                        external_links += 1
                elif href.startswith('/'):
                    internal_links += 1
            
            text = soup.get_text()
            word_count = len(text.split())
            
            return {
                "title": title,
                "meta_description": meta_description,
                "h1_count": len(h1_tags),
                "images_without_alt": images_without_alt,
                "internal_links": internal_links,
                "external_links": external_links,
                "word_count": word_count,
                "html_content": str(soup)[:5000]
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lors de la récupération de l'URL: {str(e)}")

# --- ROUTES ---

@app.post("/api/comptable/extract", response_model=ExtractionFacture)
async def extract_invoice(request: ImageRequest, background_tasks: BackgroundTasks):
    try:
        image_base64 = request.image_base64
        if "," in image_base64:
            image_base64 = image_base64.split(",")[1]
        image_data_uri = f"data:image/jpeg;base64,{image_base64}"

        extraction = groq_client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            response_model=ExtractionFacture,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extrais les données de cette facture. Pour chaque ligne, fournis un objet avec : designation (nom court du produit/service), libelle (description détaillée si présente sur la facture, sinon mets la designation), quantite (nombre), prixFinal (prix total de la ligne)."},
                    {"type": "image_url", "image_url": {"url": image_data_uri}}
                ]
            }],
            max_tokens=1000
        )

        # Données formatées pour Evolbee
        sheets_data = {
            "fournisseur": extraction.fournisseur,
            "date_facture": extraction.date,
            "montant_ht": extraction.montant_ht,
            "montant_tva": extraction.montant_tva,
            "numero_facture": extraction.numero_facture,
            "lignes": extraction.lignes
        }
        background_tasks.add_task(send_to_google_sheets, sheets_data)

        db_data = {
            "date_facture": extraction.date,
            "fournisseur": extraction.fournisseur,
            "montant_ht": extraction.montant_ht,
            "montant_tva": extraction.montant_tva,
            "montant_ttc": extraction.montant_ttc,
            "numero_facture": extraction.numero_facture,
            "lignes": json.dumps(extraction.lignes) if extraction.lignes else None
        }
        db_task("factures", db_data)

        return extraction
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/administratif/response", response_model=AgentResponse)
async def generate_admin_response(request: MessageRequest):
    try:
        context_docs = search_knowledge_base(request.content)
        
        if context_docs:
            context_text = "\n\n".join([
                f"[{doc['category'].upper()}] {doc['title']}:\n{doc['content']}"
                for doc in context_docs
            ])
            system_prompt = f"""Tu es un assistant administratif professionnel pour un consultant IA à Soissons.
Propose 3 variantes de réponse (formelle, directe, commerciale).

BASE DE CONNAISSANCES À UTILISER :
{context_text}

Utilise ces informations pour personnaliser ta réponse."""
        else:
            system_prompt = "Tu es un assistant administratif professionnel. Propose 3 variantes de réponse."
        
        response = groq_client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            response_model=AgentResponse,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Type: {request.type}\nMessage: {request.content}"}
            ],
            max_tokens=500
        )
        
        db_data = {
            "message_type": request.type,
            "content": request.content,
            "response_suggestions": json.dumps(response.suggestions),
            "context_used": context_text if context_docs else None
        }
        db_task("conversations", db_data)
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/marketing/analyze-flyer", response_model=MarketingAnalysis)
async def analyze_flyer(file: UploadFile = File(...), document_type: str = Form(...)):
    try:
        image_bytes = await file.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        image_data_uri = f"data:image/jpeg;base64,{image_base64}"
        
        analysis = groq_client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            response_model=MarketingAnalysis,
            messages=[{"role": "user", "content": [
                {"type": "text", "text": "Analyse ce document marketing. Propose des améliorations et un snippet HTML/Tailwind."},
                {"type": "image_url", "image_url": {"url": image_data_uri}}
            ]}],
            max_tokens=1000
        )
        
        db_data = {
            "document_type": document_type,
            "file_path": file.filename,
            "analysis_feedback": analysis.feedback,
            "html_suggestion": analysis.html_suggestion,
            "improvements": json.dumps(analysis.improvements)
        }
        db_task("marketing_documents", db_data)
        
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/commercial/prospect-strategy", response_model=ProspectStrategy)
async def get_prospect_strategy(secteur: str, localisation: str):
    try:
        strategy = groq_client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            response_model=ProspectStrategy,
            messages=[
                {"role": "system", "content": "Tu es un expert commercial spécialisé PME/TPE locales à Soissons."},
                {"role": "user", "content": f"Secteur: {secteur}\nLocalisation: {localisation}"}
            ],
            max_tokens=500
        )
        
        db_data = {
            "nom_entreprise": f"Prospect {secteur}",
            "type_entreprise": secteur,
            "secteur": secteur,
            "localisation": localisation,
            "point_douleur": strategy.point_de_douleur,
            "argumentaire_ia": strategy.argumentaire_ia,
            "action_recommandee": strategy.action
        }
        db_task("prospects", db_data)
        
        return strategy
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/knowledge/add")
async def add_knowledge(doc: KnowledgeDocument):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO knowledge_base (title, content, category) VALUES (%s, %s, %s) RETURNING id",
                (doc.title, doc.content, doc.category)
            )
            doc_id = cur.fetchone()[0]
            conn.commit()
        conn.close()
        return {"id": doc_id, "message": "Document ajouté"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/knowledge/search")
async def search_knowledge(q: str):
    results = search_knowledge_base(q)
    return {"results": results, "count": len(results)}

@app.post("/api/seo/analyze", response_model=SEOAnalysis)
async def analyze_seo(url: str = Query(...), focus_keyword: Optional[str] = Query(None)):
    try:
        page_data = await fetch_and_parse_url(url)
        
        analysis_prompt = f"""Analyse SEO de cette page web :
URL: {url}
Mot-clé cible: {focus_keyword or 'Non spécifié'}

Données techniques :
- Title: {page_data['title'] or 'Manquant'}
- Meta description: {page_data['meta_description'] or 'Manquante'}
- Nombre de H1: {page_data['h1_count']}
- Images sans attribut alt: {page_data['images_without_alt']}
- Liens internes: {page_data['internal_links']}
- Liens externes: {page_data['external_links']}
- Nombre de mots: {page_data['word_count']}

Extrait HTML (structure) :
{page_data['html_content'][:3000]}

Analyse cette page et propose :
1. Un score SEO de 0 à 100
2. 3-5 points forts
3. 3-5 points faibles
4. 5-7 recommandations concrètes et actionnables
5. Si applicable, un snippet HTML optimisé pour améliorer le SEO

Réponds en JSON avec cette structure :
{{
  "seo_score": <int 0-100>,
  "strengths": [<liste de strings>],
  "weaknesses": [<liste de strings>],
  "recommendations": [<liste de strings>],
  "html_snippet": "<snippet HTML optimisé ou null>"
}}"""
        
        analysis = groq_client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            response_model=SEOAnalysis,
            messages=[
                {"role": "system", "content": "Tu es un expert SEO. Analyse les pages web et propose des recommandations concrètes."},
                {"role": "user", "content": analysis_prompt}
            ],
            max_tokens=1500
        )
        
        analysis.url = url
        analysis.title_found = page_data['title']
        analysis.meta_description = page_data['meta_description']
        analysis.h1_count = page_data['h1_count']
        analysis.images_without_alt = page_data['images_without_alt']
        analysis.internal_links = page_data['internal_links']
        analysis.external_links = page_data['external_links']
        analysis.word_count = page_data['word_count']
        
        db_data = {
            "url": url,
            "focus_keyword": focus_keyword,
            "title_found": analysis.title_found,
            "meta_description": analysis.meta_description,
            "h1_count": analysis.h1_count,
            "images_without_alt": analysis.images_without_alt,
            "internal_links": analysis.internal_links,
            "external_links": analysis.external_links,
            "word_count": analysis.word_count,
            "seo_score": analysis.seo_score,
            "strengths": json.dumps(analysis.strengths),
            "weaknesses": json.dumps(analysis.weaknesses),
            "recommendations": json.dumps(analysis.recommendations),
            "html_snippet": analysis.html_snippet
        }
        db_task("seo_analyses", db_data)
        
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {"message": "IA Agent API - Système Multi-Agents Opérationnel"}