from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

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

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.on_event("startup")
async def startup_event():
    init_db()
    print("✓ EduAI Platform started — http://0.0.0.0:8000")

app.include_router(health_router)
app.include_router(teacher_router, prefix="/teacher", tags=["Teacher Assistant"])
