import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

STORAGE_DIR = BASE_DIR / "storage" / "uploads"
DB_PATH = BASE_DIR / "database" / "education.db"

# AI Models
WHISPER_MODEL = "small"
NLLB_MODEL = "facebook/nllb-200-distilled-600M"
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3"

# Translation
TARGET_LANGUAGE = "eng_Latn"   # NLLB language code for English

# Server
HOST = "0.0.0.0"
PORT = 8000

# Ensure storage directories exist on import
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
(BASE_DIR / "database").mkdir(parents=True, exist_ok=True)
