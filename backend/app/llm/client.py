"""LLM-клиент: Ollama (локально) или mock (без модели)."""
import json
import os

import httpx

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
USE_MOCK = os.getenv("EXITKIT_MOCK", "1") == "1"


def generate_json(prompt: str) -> dict:
    if USE_MOCK:
        return {}
    r = httpx.post(
        f"{OLLAMA_URL}/api/generate",
        json={"model": OLLAMA_MODEL, "prompt": prompt, "format": "json", "stream": False},
        timeout=120,
    )
    r.raise_for_status()
    return json.loads(r.json()["response"])
