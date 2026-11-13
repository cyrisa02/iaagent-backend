from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class MessageRequest(BaseModel):
    content: str
    type: str  # "email", "sms", "message"

class AgentResponse(BaseModel):
    suggestions: list[str]
    context: Optional[str] = None

@router.post("/administratif/response", response_model=AgentResponse)
async def generate_admin_response(request: MessageRequest):
    """
    Génère des suggestions de réponse pour un message entrant
    """
    # TODO: Intégration LangGraph + RAG
    return {
        "suggestions": [
            "Exemple de réponse 1...",
            "Exemple de réponse 2...",
            "Exemple de réponse 3..."
        ],
        "context": "Contexte extrait de la base de connaissances"
    }

@router.get("/commercial/prospects")
async def get_commercial_strategy():
    """
    Récupère la stratégie commerciale pour les prospects locaux
    """
    return {
        "cibles": ["PME/TPE", "Artisans", "Commerçants"],
        "zone": "Soissons et environs"
    }