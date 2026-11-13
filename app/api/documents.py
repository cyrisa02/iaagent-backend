from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel

router = APIRouter()

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload de document pour analyse"""
    return {"filename": file.filename, "status": "uploaded"}