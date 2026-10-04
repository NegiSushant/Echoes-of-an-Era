import os
import json
import httpx
from pathlib import Path
from typing import Dict, Any, List

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

class MemoryExtractorService:
    def __init__(self, ollama_url: str = None, model: str = None):
        self.ollama_url = (ollama_url or os.getenv("LLM_BASE_URL") or os.getenv("OLLAMA_BASE_URL", "http://localhost:12434")).rstrip("/")
        self.model = model or os.getenv("LLM_MODEL") or os.getenv("OLLAMA_MODEL", "gemma3:1B-Q4_K_M")
        
        prompt_file = PROMPTS_DIR / "extraction.txt"
        with open(prompt_file, "r", encoding="utf-8") as f:
            self.prompt_template = f.read()

    async def extract_memories(self, transcript_text: str) -> Dict[str, Any]:
        """
        Sends transcript to Gemma 3 (gemma3:1B-Q4_K_M) via Docker Model Runner / Ollama API
        to extract structured memories strictly anchored in verbatim grandfather statements.
        """
        prompt = self.prompt_template.format(transcript_text=transcript_text)

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.1,  # Ultra-low temperature for strict factual extraction
                "top_p": 0.9
            }
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{self.ollama_url}/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            raw_response = data.get("response", "{}")

        try:
            parsed = json.loads(raw_response)
        except json.JSONDecodeError:
            # Fallback cleaning if markdown quotes were included
            cleaned = raw_response.strip().removeprefix("```json").removesuffix("```").strip()
            parsed = json.loads(cleaned)

        return parsed

# Singleton instance
memory_extractor_service = MemoryExtractorService()
