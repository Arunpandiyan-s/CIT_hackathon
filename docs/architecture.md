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
