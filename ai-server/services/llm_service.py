"""
LLM reasoning via Ollama (Llama 3).
Sends a structured prompt and parses JSON output.
"""
import json
import requests
from config import OLLAMA_BASE_URL, OLLAMA_MODEL

ANALYSIS_PROMPT = """You are an expert in early childhood education.

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

Respond with the JSON object only."""


def analyze_with_llm(text: str) -> dict:
    """Send teacher text to Llama3 and return structured analysis."""
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
