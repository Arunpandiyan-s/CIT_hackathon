"""
Speech-to-text using OpenAI Whisper (local, runs on CPU/GPU).
Model is loaded once and cached for reuse.
"""
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

from config import WHISPER_MODEL

_model = None


def get_whisper_model():
    if not WHISPER_AVAILABLE:
        raise ImportError("Whisper not installed. Run: pip install openai-whisper")
    global _model
    if _model is None:
        print(f"Loading Whisper model '{WHISPER_MODEL}'...")
        _model = whisper.load_model(WHISPER_MODEL)
        print("✓ Whisper model loaded")
    return _model


def transcribe_audio(file_path: str) -> str:
    """Transcribe an audio file to text."""
    if not WHISPER_AVAILABLE:
        raise ImportError("Whisper not installed. Run: pip install openai-whisper")
    model = get_whisper_model()
    result = model.transcribe(file_path, fp16=False)
    return result["text"].strip()
