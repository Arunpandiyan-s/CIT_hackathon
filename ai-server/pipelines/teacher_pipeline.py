"""
Teacher Processing Pipeline — Phase 1

Accepts any of four input types and returns structured classroom insights.

Flow:
  audio  → Whisper STT → text ──┐
  pdf    → pdfplumber   → text  ├─→ [optional NLLB translate] → Llama3 → activity
  image  → OCR/filename → text  │
  text   → (pass-through) ──────┘

Phase 2+: context aggregation, pattern detection, regional insights.
"""
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
    return "\n".join(pages).strip()


def _extract_image_text(file_path: str) -> str:
    """
    Attempt OCR via pytesseract. Falls back to filename as context.
    Install Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
    """
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
    """
    Main pipeline entry point.

    Args:
        input_type : one of 'audio' | 'pdf' | 'image' | 'text'
        file_path  : path to uploaded file (audio / pdf / image)
        text       : raw text (when input_type == 'text')
        source_lang: NLLB language code for translation source
        translate  : whether to translate to English before LLM analysis

    Returns:
        dict with keys: issue, topic, age_group, activity, extracted_text
    """
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
