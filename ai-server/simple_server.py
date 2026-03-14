from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from datetime import datetime
import requests

app = FastAPI(title="EduAI Platform", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.get("/health")
def health_check():
    def check_ollama():
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            return "available" if response.status_code == 200 else "offline"
        except:
            return "offline"
    
    return {
        "status": "healthy",
        "service": "EduAI Platform",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "models": {
            "Ollama (LLM)": check_ollama(),
            "Whisper (Speech)": "not loaded",
            "NLLB (Translation)": "not loaded",
            "Tesseract (OCR)": "not loaded"
        }
    }

@app.post("/teacher/analyze")
async def analyze_text(request: dict):
    return {"error": "Install dependencies: pip install -r requirements.txt"}

@app.post("/teacher/upload")
async def upload_file():
    return {"error": "Install dependencies: pip install -r requirements.txt"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
