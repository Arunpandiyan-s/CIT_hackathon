from fastapi import APIRouter
from datetime import datetime
import requests
from config import OLLAMA_BASE_URL

router = APIRouter(tags=["Health"])

def check_ollama():
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        return "available" if response.status_code == 200 else "offline"
    except:
        return "offline"

def check_whisper():
    try:
        import whisper
        return "available"
    except ImportError:
        return "not installed"

def check_transformers():
    try:
        import transformers
        return "available"
    except ImportError:
        return "not installed"

def check_tesseract():
    try:
        import pytesseract
        return "available"
    except ImportError:
        return "not installed"

@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "EduAI Platform",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "server": "http://192.168.188.202:8000",
        "models": {
            "Ollama (LLM)": check_ollama(),
            "Whisper (Speech)": check_whisper(),
            "NLLB (Translation)": check_transformers(),
            "Tesseract (OCR)": check_tesseract()
        }
    }
