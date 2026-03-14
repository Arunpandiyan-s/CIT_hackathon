"""
EduAI Platform - Full Project Setup Script
Run: python create_dirs.py
This creates the entire ai-server project structure.
"""

import os

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai-server")

DIRS = [
    f"{BASE}/routes",
    f"{BASE}/services",
    f"{BASE}/pipelines",
    f"{BASE}/database",
    f"{BASE}/storage/uploads",
    f"{BASE}/utils",
    os.path.join(os.path.dirname(BASE), "frontend/teacher-dashboard"),
    os.path.join(os.path.dirname(BASE), "docs"),
]

for d in DIRS:
    os.makedirs(d, exist_ok=True)
print("✓ Directories created")

# ─────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────

def write(rel_path: str, content: str):
    path = os.path.join(BASE, rel_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.lstrip("\n"))
    print(f"  ✓ {rel_path}")

def write_abs(abs_path: str, content: str):
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(content.lstrip("\n"))
    print(f"  ✓ {os.path.relpath(abs_path, os.path.dirname(BASE))}")

# ─────────────────────────────────────────────────────────────
# config.py
# ─────────────────────────────────────────────────────────────
write("config.py", """
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
""")

# ─────────────────────────────────────────────────────────────
# main.py
# ─────────────────────────────────────────────────────────────
write("main.py", """
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.health_route import router as health_router
from routes.teacher_route import router as teacher_router
from database.sqlite_db import init_db

app = FastAPI(
    title="EduAI Platform",
    description="Multimodal AI platform for early childhood education programs",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    init_db()
    print("✓ EduAI Platform started — http://0.0.0.0:8000")

app.include_router(health_router)
app.include_router(teacher_router, prefix="/teacher", tags=["Teacher Assistant"])
""")

# ─────────────────────────────────────────────────────────────
# routes/__init__.py
# ─────────────────────────────────────────────────────────────
write("routes/__init__.py", "")

# ─────────────────────────────────────────────────────────────
# routes/health_route.py
# ─────────────────────────────────────────────────────────────
write("routes/health_route.py", """
from fastapi import APIRouter
from datetime import datetime

router = APIRouter(tags=["Health"])

@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "EduAI Platform",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "server": "http://192.168.188.202:8000",
    }
""")

# ─────────────────────────────────────────────────────────────
# routes/teacher_route.py
# ─────────────────────────────────────────────────────────────
write("routes/teacher_route.py", """
import os
import uuid
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional

from config import STORAGE_DIR
from pipelines.teacher_pipeline import run_teacher_pipeline
from database.sqlite_db import save_analysis

router = APIRouter()


class TextAnalysisRequest(BaseModel):
    text: str
    source_lang: Optional[str] = None   # NLLB language code, e.g. "tam_Taml"
    translate: Optional[bool] = False


@router.post("/upload", summary="Upload voice/image/document and analyze")
async def upload_and_analyze(
    file: UploadFile = File(...),
    input_type: str = Form(..., description="audio | image | pdf"),
    source_lang: str = Form(default="eng_Latn"),
    translate: bool = Form(default=False),
):
    \"\"\"
    Upload a file (audio, image, or PDF) and receive structured classroom insights.
    \"\"\"
    ext = os.path.splitext(file.filename or "file")[1] or ".bin"
    filename = f"{uuid.uuid4()}{ext}"
    file_path = str(STORAGE_DIR / filename)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    try:
        result = run_teacher_pipeline(
            input_type=input_type,
            file_path=file_path,
            source_lang=source_lang,
            translate=translate,
        )
        result["file_saved"] = filename
        save_analysis(input_type, result.get("extracted_text", ""), result, filename)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/analyze", summary="Analyze plain text input")
async def analyze_text(request: TextAnalysisRequest):
    \"\"\"
    Send raw text (teacher note) and receive structured classroom insights.
    \"\"\"
    try:
        result = run_teacher_pipeline(
            input_type="text",
            text=request.text,
            source_lang=request.source_lang,
            translate=request.translate,
        )
        save_analysis("text", request.text, result)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
""")

# ─────────────────────────────────────────────────────────────
# services/__init__.py
# ─────────────────────────────────────────────────────────────
write("services/__init__.py", "")

# ─────────────────────────────────────────────────────────────
# services/speech_service.py
# ─────────────────────────────────────────────────────────────
write("services/speech_service.py", """
\"\"\"
Speech-to-text using OpenAI Whisper (local, runs on CPU/GPU).
Model is loaded once and cached for reuse.
\"\"\"
import whisper
from config import WHISPER_MODEL

_model = None


def get_whisper_model():
    global _model
    if _model is None:
        print(f"Loading Whisper model '{WHISPER_MODEL}'...")
        _model = whisper.load_model(WHISPER_MODEL)
        print("✓ Whisper model loaded")
    return _model


def transcribe_audio(file_path: str) -> str:
    \"\"\"Transcribe an audio file to text.\"\"\"
    model = get_whisper_model()
    result = model.transcribe(file_path, fp16=False)
    return result["text"].strip()
""")

# ─────────────────────────────────────────────────────────────
# services/translation_service.py
# ─────────────────────────────────────────────────────────────
write("services/translation_service.py", """
\"\"\"
Translation using NLLB-200 (facebook/nllb-200-distilled-600M).
Supports 200+ languages. Model is loaded once and cached.
\"\"\"
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from config import NLLB_MODEL, TARGET_LANGUAGE

_tokenizer = None
_model = None


def _load_model():
    global _tokenizer, _model
    if _tokenizer is None:
        print(f"Loading NLLB model '{NLLB_MODEL}'...")
        _tokenizer = AutoTokenizer.from_pretrained(NLLB_MODEL)
        _model = AutoModelForSeq2SeqLM.from_pretrained(NLLB_MODEL)
        print("✓ NLLB model loaded")
    return _tokenizer, _model


def translate_to_english(text: str, source_lang: str = "tam_Taml") -> str:
    \"\"\"
    Translate text to English.
    source_lang: NLLB language code (e.g. 'tam_Taml' for Tamil, 'hin_Deva' for Hindi).
    Full list: https://github.com/facebookresearch/flores/tree/main/flores200
    \"\"\"
    tokenizer, model = _load_model()
    tokenizer.src_lang = source_lang

    inputs = tokenizer(
        text,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=512,
    )
    translated_tokens = model.generate(
        **inputs,
        forced_bos_token_id=tokenizer.convert_tokens_to_ids(TARGET_LANGUAGE),
        max_length=512,
    )
    return tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)[0]
""")

# ─────────────────────────────────────────────────────────────
# services/llm_service.py
# ─────────────────────────────────────────────────────────────
write("services/llm_service.py", """
\"\"\"
LLM reasoning via Ollama (Llama 3).
Sends a structured prompt and parses JSON output.
\"\"\"
import json
import requests
from config import OLLAMA_BASE_URL, OLLAMA_MODEL

ANALYSIS_PROMPT = \"\"\"You are an expert in early childhood education.

Analyze the teacher observation below and return ONLY a valid JSON object — no extra text.

Required JSON structure:
{{
  "issue": "short description of the learning difficulty detected",
  "topic": "curriculum subject area (e.g. geometry, phonics, numeracy)",
  "age_group": "age range e.g. 3-4 or 4-5 or 5-6",
  "activity": {{
    "name": "name of the suggested classroom activity",
    "materials": ["material 1", "material 2"],
    "duration": "X minutes"
  }}
}}

Teacher observation:
{text}

Respond with the JSON object only.\"\"\"


def analyze_with_llm(text: str) -> dict:
    \"\"\"Send teacher text to Llama3 and return structured analysis.\"\"\"
    prompt = ANALYSIS_PROMPT.format(text=text)

    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2},
        },
        timeout=120,
    )
    response.raise_for_status()

    raw = response.json().get("response", "").strip()

    # Extract JSON block from response (LLM may add surrounding text)
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start == -1 or end <= start:
        raise ValueError(f"LLM did not return valid JSON. Raw response: {raw[:300]}")

    json_str = raw[start:end]
    return json.loads(json_str)
""")

# ─────────────────────────────────────────────────────────────
# services/activity_service.py
# ─────────────────────────────────────────────────────────────
write("services/activity_service.py", """
\"\"\"
Formats and validates the structured output from the LLM into
a standard response shape consumed by the API routes.
\"\"\"


def format_activity_response(llm_output: dict) -> dict:
    \"\"\"
    Validate and normalise LLM output into the canonical API response format.
    Missing fields receive safe defaults.
    \"\"\"
    activity = llm_output.get("activity") or {}

    return {
        "issue": llm_output.get("issue") or "Learning difficulty detected",
        "topic": llm_output.get("topic") or "General",
        "age_group": llm_output.get("age_group") or "3-6",
        "activity": {
            "name": activity.get("name") or "Exploratory Play Activity",
            "materials": activity.get("materials") or [],
            "duration": activity.get("duration") or "15 minutes",
        },
    }
""")

# ─────────────────────────────────────────────────────────────
# pipelines/__init__.py
# ─────────────────────────────────────────────────────────────
write("pipelines/__init__.py", "")

# ─────────────────────────────────────────────────────────────
# pipelines/teacher_pipeline.py
# ─────────────────────────────────────────────────────────────
write("pipelines/teacher_pipeline.py", """
\"\"\"
Teacher Processing Pipeline — Phase 1

Accepts any of four input types and returns structured classroom insights.

Flow:
  audio  → Whisper STT → text ──┐
  pdf    → pdfplumber   → text  ├─→ [optional NLLB translate] → Llama3 → activity
  image  → OCR/filename → text  │
  text   → (pass-through) ──────┘

Phase 2+: context aggregation, pattern detection, regional insights.
\"\"\"
import os
from services.speech_service import transcribe_audio
from services.translation_service import translate_to_english
from services.llm_service import analyze_with_llm
from services.activity_service import format_activity_response


def _extract_pdf_text(file_path: str) -> str:
    import pdfplumber
    pages = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                pages.append(t)
    return "\\n".join(pages).strip()


def _extract_image_text(file_path: str) -> str:
    \"\"\"
    Attempt OCR via pytesseract. Falls back to filename as context.
    Install Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
    \"\"\"
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(file_path)
        text = pytesseract.image_to_string(img).strip()
        if text:
            return text
    except Exception:
        pass
    return f"Classroom image uploaded: {os.path.basename(file_path)}"


def run_teacher_pipeline(
    input_type: str,
    file_path: str = None,
    text: str = None,
    source_lang: str = None,
    translate: bool = False,
) -> dict:
    \"\"\"
    Main pipeline entry point.

    Args:
        input_type : one of 'audio' | 'pdf' | 'image' | 'text'
        file_path  : path to uploaded file (audio / pdf / image)
        text       : raw text (when input_type == 'text')
        source_lang: NLLB language code for translation source
        translate  : whether to translate to English before LLM analysis

    Returns:
        dict with keys: issue, topic, age_group, activity, extracted_text
    \"\"\"
    # ── Step 1: Extract text ──────────────────────────────────
    if input_type == "audio":
        if not file_path:
            raise ValueError("file_path required for audio input")
        text = transcribe_audio(file_path)

    elif input_type == "pdf":
        if not file_path:
            raise ValueError("file_path required for pdf input")
        text = _extract_pdf_text(file_path)

    elif input_type == "image":
        if not file_path:
            raise ValueError("file_path required for image input")
        text = _extract_image_text(file_path)

    elif input_type == "text":
        text = (text or "").strip()

    else:
        raise ValueError(f"Unsupported input_type: '{input_type}'. Use audio|pdf|image|text")

    if not text:
        raise ValueError("No text could be extracted from the provided input.")

    # ── Step 2: Translate (optional) ─────────────────────────
    if translate and source_lang and source_lang != "eng_Latn":
        text = translate_to_english(text, source_lang=source_lang)

    # ── Step 3: LLM analysis ─────────────────────────────────
    llm_output = analyze_with_llm(text)

    # ── Step 4: Format response ───────────────────────────────
    result = format_activity_response(llm_output)
    result["extracted_text"] = text   # echoed back for transparency

    return result

    # ── Future Phase 2 hook ───────────────────────────────────
    # from intelligence.context_engine import store_insight
    # store_insight(result, region=teacher.region)
""")

# ─────────────────────────────────────────────────────────────
# database/__init__.py
# ─────────────────────────────────────────────────────────────
write("database/__init__.py", "")

# ─────────────────────────────────────────────────────────────
# database/sqlite_db.py
# ─────────────────────────────────────────────────────────────
write("database/sqlite_db.py", """
\"\"\"
SQLite database layer.

Phase 1 tables  : analyses
Phase 2 (future): classroom_patterns
Phase 3 (future): users (role-based access)
Phase 4 (future): knowledge_base
Phase 5 (future): early_warnings
\"\"\"
import sqlite3
import json
from datetime import datetime
from config import DB_PATH


def _connect():
    return sqlite3.connect(str(DB_PATH))


def init_db():
    \"\"\"Create all tables. Safe to call multiple times (CREATE IF NOT EXISTS).\"\"\"
    conn = _connect()
    cur = conn.cursor()

    # ── Phase 1: Teacher analysis records ────────────────────
    cur.execute(\"\"\"
        CREATE TABLE IF NOT EXISTS analyses (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            input_type       TEXT    NOT NULL,
            extracted_text   TEXT,
            issue            TEXT,
            topic            TEXT,
            age_group        TEXT,
            activity_name    TEXT,
            activity_materials TEXT,
            activity_duration  TEXT,
            file_name        TEXT,
            created_at       TEXT    DEFAULT CURRENT_TIMESTAMP
        )
    \"\"\")

    # ── Phase 2: Regional pattern aggregation ─────────────────
    cur.execute(\"\"\"
        CREATE TABLE IF NOT EXISTS classroom_patterns (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            region       TEXT,
            issue_type   TEXT,
            frequency    INTEGER DEFAULT 1,
            detected_at  TEXT    DEFAULT CURRENT_TIMESTAMP
        )
    \"\"\")

    # ── Phase 3: Role-based users ─────────────────────────────
    cur.execute(\"\"\"
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT,
            role       TEXT,   -- teacher | manager | officer
            region     TEXT,
            created_at TEXT    DEFAULT CURRENT_TIMESTAMP
        )
    \"\"\")

    # ── Phase 4: Knowledge base ───────────────────────────────
    cur.execute(\"\"\"
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            issue        TEXT,
            topic        TEXT,
            activity_json TEXT,
            usage_count  INTEGER DEFAULT 0,
            created_at   TEXT    DEFAULT CURRENT_TIMESTAMP
        )
    \"\"\")

    # ── Phase 5: Early warning signals ───────────────────────
    cur.execute(\"\"\"
        CREATE TABLE IF NOT EXISTS early_warnings (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            region      TEXT,
            issue_type  TEXT,
            severity    TEXT,   -- low | medium | high
            detected_at TEXT    DEFAULT CURRENT_TIMESTAMP
        )
    \"\"\")

    conn.commit()
    conn.close()
    print("✓ Database initialised")


def save_analysis(
    input_type: str,
    extracted_text: str,
    result: dict,
    file_name: str = None,
):
    \"\"\"Persist one teacher analysis to the database.\"\"\"
    conn = _connect()
    activity = result.get("activity") or {}
    conn.execute(
        \"\"\"
        INSERT INTO analyses
            (input_type, extracted_text, issue, topic, age_group,
             activity_name, activity_materials, activity_duration, file_name, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        \"\"\",
        (
            input_type,
            extracted_text,
            result.get("issue"),
            result.get("topic"),
            result.get("age_group"),
            activity.get("name"),
            json.dumps(activity.get("materials", [])),
            activity.get("duration"),
            file_name,
            datetime.utcnow().isoformat(),
        ),
    )
    conn.commit()
    conn.close()


def get_all_analyses() -> list:
    \"\"\"Retrieve all analysis records (used by future dashboard/reporting).\"\"\"
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM analyses ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return rows
""")

# ─────────────────────────────────────────────────────────────
# utils/__init__.py
# ─────────────────────────────────────────────────────────────
write("utils/__init__.py", "# Utility helpers — extend for Phase 2+ (logging, auth, formatting)")

# ─────────────────────────────────────────────────────────────
# requirements.txt
# ─────────────────────────────────────────────────────────────
write("requirements.txt", """
# API framework
fastapi==0.111.0
uvicorn[standard]==0.30.1
python-multipart==0.0.9

# AI — Speech Recognition
openai-whisper==20231117

# AI — Translation (NLLB-200)
transformers==4.41.2
sentencepiece==0.2.0
torch==2.3.1

# AI — Embeddings (Phase 2+)
sentence-transformers==3.0.1

# Vector DB (Phase 2+)
chromadb==0.5.3

# PDF extraction
pdfplumber==0.11.0

# Image OCR
Pillow==10.3.0
pytesseract==0.3.10

# HTTP (Ollama calls)
requests==2.32.3

# Data validation
pydantic==2.7.3
""")

# ─────────────────────────────────────────────────────────────
# docs/architecture.md
# ─────────────────────────────────────────────────────────────
docs_root = os.path.join(os.path.dirname(BASE), "docs")
docs_path = os.path.join(docs_root, "architecture.md")
write_abs(docs_path, """
# EduAI Platform — System Architecture

## 1. Full System Architecture Explanation

The EduAI Platform is a **locally-hosted, multimodal AI server** designed for early
childhood education programs. Teachers submit observations in any format (voice, image,
document, or text). The platform processes the input through a chain of AI models and
returns structured, actionable classroom insights.

All AI inference runs **on-premise** (Windows server, 24 GB RAM) at `192.168.188.202`.
Other laptops on the college LAN call the API at `http://192.168.188.202:8000`.

---

## 2. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        TEACHER DEVICES (LAN)                        │
│   Browser / App / curl  →  http://192.168.188.202:8000              │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ HTTP / REST
┌───────────────────────────────▼─────────────────────────────────────┐
│  LAYER 2 — API LAYER                                                 │
│  FastAPI  (uvicorn, port 8000)                                       │
│  ┌──────────────────┐  ┌────────────────────────────────────────┐   │
│  │  GET  /health    │  │  POST /teacher/upload                  │   │
│  └──────────────────┘  │  POST /teacher/analyze                 │   │
│                         └────────────────────────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────┐
│  LAYER 3 — AI PROCESSING LAYER                                       │
│                                                                      │
│  ┌─────────────┐  ┌────────────────┐  ┌──────────────────────────┐  │
│  │ Whisper     │  │ NLLB-200       │  │ Llama 3 (Ollama)         │  │
│  │ (STT)       │  │ (Translation)  │  │ (Reasoning + Activity)   │  │
│  └──────┬──────┘  └───────┬────────┘  └──────────────────────────┘  │
│         │                 │                        ▲                  │
│  audio──┘  text (non-EN)──┘               text ───┘                  │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────┐
│  LAYER 4 — DATA LAYER                                                │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐   │
│  │  SQLite          │  │  Local Storage   │  │  ChromaDB        │   │
│  │  (metadata)      │  │  /storage/uploads│  │  (embeddings)    │   │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  LAYER 5 — INTELLIGENCE LAYER  (Phase 2-5, future)                  │
│  Context Engine  •  Trend Detection  •  Role-Based Insights          │
│  Knowledge Base  •  Early Warning System                             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. System Components

| Component | Technology | Role |
|-----------|-----------|------|
| API Server | FastAPI + Uvicorn | Receives teacher requests |
| Speech-to-Text | Whisper Small | Converts voice notes to text |
| Translation | NLLB-200-distilled-600M | Multi-language → English |
| LLM Reasoning | Llama 3 via Ollama | Issue detection + activity suggestion |
| Embeddings | SentenceTransformers | Semantic similarity (Phase 2+) |
| Vector DB | ChromaDB | Pattern storage (Phase 2+) |
| Relational DB | SQLite | Metadata persistence |
| File Storage | Local filesystem | Raw uploads |

---

## 4. Data Flow

### Voice input
```
teacher audio file
  → POST /teacher/upload (input_type=audio)
  → Whisper Small transcription
  → [optional NLLB translation to English]
  → Llama 3 structured JSON analysis
  → SQLite save
  → JSON response to teacher
```

### Text input
```
teacher text observation
  → POST /teacher/analyze
  → [optional NLLB translation]
  → Llama 3 structured JSON analysis
  → SQLite save
  → JSON response
```

---

## 5. Phase Roadmap

| Phase | Feature | Status |
|-------|---------|--------|
| 1 | Teacher Assistant Module (voice/image/doc/text → insights) | ✅ Implemented |
| 2 | Context Intelligence Engine (pattern detection across classrooms) | 🏗 Architecture ready |
| 3 | Role-Based Intelligence (teacher / manager / officer views) | 🏗 Architecture ready |
| 4 | Knowledge Base (AI teaching repository) | 🏗 Architecture ready |
| 5 | Early Warning System (regional issue detection) | 🏗 Architecture ready |

---

## 6. Server Info

- **Server IP**: 192.168.188.202
- **Port**: 8000
- **Start command**: `uvicorn main:app --host 0.0.0.0 --port 8000`
- **Swagger UI**: http://192.168.188.202:8000/docs
""")

print()
print("=" * 60)
print("✓ EduAI Platform project created successfully!")
print("=" * 60)
print()
print("Next steps:")
print("  1. cd ai-server")
print("  2. pip install -r requirements.txt")
print("  3. Install Ollama: https://ollama.com")
print("  4. ollama pull llama3")
print("  5. uvicorn main:app --host 0.0.0.0 --port 8000")
print()
print("API will be available at: http://192.168.188.202:8000")
print("Swagger docs:             http://192.168.188.202:8000/docs")

