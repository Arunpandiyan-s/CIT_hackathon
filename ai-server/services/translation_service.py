"""
Translation using NLLB-200 (facebook/nllb-200-distilled-600M).
Supports 200+ languages. Model is loaded once and cached.
"""
try:
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    NLLB_AVAILABLE = True
except ImportError:
    NLLB_AVAILABLE = False

from config import NLLB_MODEL, TARGET_LANGUAGE

_tokenizer = None
_model = None


def _load_model():
    if not NLLB_AVAILABLE:
        raise ImportError("Transformers not installed. Run: pip install transformers sentencepiece torch")
    global _tokenizer, _model
    if _tokenizer is None:
        print(f"Loading NLLB model '{NLLB_MODEL}'...")
        _tokenizer = AutoTokenizer.from_pretrained(NLLB_MODEL)
        _model = AutoModelForSeq2SeqLM.from_pretrained(NLLB_MODEL)
        print("✓ NLLB model loaded")
    return _tokenizer, _model


def translate_to_english(text: str, source_lang: str = "tam_Taml") -> str:
    """
    Translate text to English.
    source_lang: NLLB language code (e.g. 'tam_Taml' for Tamil, 'hin_Deva' for Hindi).
    Full list: https://github.com/facebookresearch/flores/tree/main/flores200
    """
    if not NLLB_AVAILABLE:
        raise ImportError("Transformers not installed. Run: pip install transformers sentencepiece torch")
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
