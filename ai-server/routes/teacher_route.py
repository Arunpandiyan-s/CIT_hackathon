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
    """
    Upload a file (audio, image, or PDF) and receive structured classroom insights.
    """
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
    """
    Send raw text (teacher note) and receive structured classroom insights.
    """
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
