import os
import re
import json
import httpx
from pathlib import Path
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.memory import ExtractedMemory, ThenNowComparison, AudioRecord
from app.services.retrieval import retrieval_service

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

class ComparisonService:
    def __init__(self, ollama_url: str = None, model: str = None):
        self.ollama_url = (ollama_url or os.getenv("LLM_BASE_URL") or os.getenv("OLLAMA_BASE_URL", "http://localhost:12434")).rstrip("/")
        self.model = model or os.getenv("LLM_MODEL") or os.getenv("OLLAMA_MODEL", "gemma3:1B-Q4_K_M")

        prompt_file = PROMPTS_DIR / "comparison.txt"
        with open(prompt_file, "r", encoding="utf-8") as f:
            self.prompt_template = f.read()

    def _parse_json_safely(self, raw_str: str) -> dict:
        """Parses model json response safely, handling control characters and code fences."""
        if not raw_str:
            return {}
        cleaned = raw_str.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```", 1)[1].split("```", 1)[0].strip()

        # 1. Try standard load with strict=False (allows unescaped newlines/control chars)
        try:
            return json.loads(cleaned, strict=False)
        except Exception:
            pass

        # 2. Try regex extraction of outer JSON object
        m = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0), strict=False)
            except Exception:
                pass

        # 3. Fallback: individual key-value regex extraction
        extracted = {}
        for key in ["topic", "era_described", "then_experience", "now_reality", "reflection_question", "enduring_value"]:
            pattern = rf'"{key}"\s*:\s*"((?:[^"\\]|\\.)*)"'
            match = re.search(pattern, raw_str)
            if match:
                val = match.group(1).replace('\\"', '"').replace('\\n', '\n')
                extracted[key] = val

        return extracted

    def _resolve_memory(
        self,
        db: Session,
        memory_id: Optional[Any] = None,
        query: Optional[str] = None,
        topic: Optional[str] = None
    ) -> ExtractedMemory:
        """
        Flow Step 1: Retrieve relevant grandfather memories
        Resolves memory by memory_id, semantic query/topic, or defaults to the latest memory.
        """
        # 1. By explicit memory_id
        if memory_id is not None:
            # Check integer ID
            if isinstance(memory_id, int) or (isinstance(memory_id, str) and memory_id.isdigit()):
                mem = db.query(ExtractedMemory).filter(ExtractedMemory.id == int(memory_id)).first()
                if mem:
                    return mem
            # Check UUID / string memory_id
            mem = db.query(ExtractedMemory).filter(ExtractedMemory.memory_id == str(memory_id)).first()
            if mem:
                return mem

        # 2. By query or topic via Hybrid Retrieval
        search_term = (query or topic or "").strip()
        if search_term:
            results = retrieval_service.hybrid_search(db=db, query=search_term, limit=1)
            if results:
                return results[0].memory

        # 3. Default to the most recent extracted memory
        latest = db.query(ExtractedMemory).order_by(ExtractedMemory.id.desc()).first()
        if latest:
            return latest

        raise ValueError("No grandfather memories found in archive to compare.")

    def _format_comparison_response(self, comp: ThenNowComparison, memory: ExtractedMemory) -> Dict[str, Any]:
        """
        Enriches comparison with source audio metadata for immediate playback.
        """
        audio_rec = memory.audio if hasattr(memory, "audio") else None
        audio_id = str(memory.memory_id)
        audio_src = audio_rec.file_name if audio_rec else f"memory_{memory.memory_id}.wav"
        audio_url = f"/api/memories/audio/{memory.memory_id}/stream"
        start_t = float(memory.start_time or 0.0)
        end_t = float(memory.end_time or (audio_rec.duration if audio_rec else 0.0))

        quote_text = ""
        if memory.verbatim_quotes and isinstance(memory.verbatim_quotes, list) and len(memory.verbatim_quotes) > 0:
            first_q = memory.verbatim_quotes[0]
            quote_text = first_q.get("quote", "") if isinstance(first_q, dict) else str(first_q)

        source_audio_dict = {
            "memory_id": audio_id,
            "title": memory.title,
            "audio_id": audio_id,
            "audio_source": audio_src,
            "audio_url": audio_url,
            "start_time": start_t,
            "end_time": end_t,
            "verbatim_quote": quote_text
        }

        return {
            "id": comp.id,
            "memory_id": comp.memory_id,
            "topic": comp.topic,
            "era_described": comp.era_described,
            "then_experience": comp.then_experience,
            "now_reality": comp.now_reality,
            "reflection_question": comp.reflection_question,
            "enduring_value": comp.enduring_value,
            "created_at": comp.created_at,
            "source_audio": source_audio_dict,
            # Flat convenience fields for UI
            "audio_id": audio_id,
            "audio_source": audio_src,
            "audio_url": audio_url,
            "start_time": start_t,
            "end_time": end_t,
            "verbatim_quote": quote_text,
            "memory_title": memory.title
        }

    async def generate_comparison(
        self,
        db: Session,
        memory_id: Optional[Any] = None,
        query: Optional[str] = None,
        topic: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        THEN VS NOW Signature Flow:
        1. Retrieve relevant grandfather memories
        2. Extract 'THEN' (only from his words, zero hallucination)
        3. Provide clearly separated modern context ('NOW')
        4. Generate comparison & enduring generational bridge
        5. Always attach source audio details
        """
        # Step 1: Retrieve memory
        memory = self._resolve_memory(db, memory_id=memory_id, query=query, topic=topic)

        # Check if already generated in database
        existing = db.query(ThenNowComparison).filter(ThenNowComparison.memory_id == memory.id).first()
        if existing:
            return self._format_comparison_response(existing, memory)

        # Step 2: Build grounded context strictly from grandfather's words
        quotes = "\n".join([
            f'  - "{q.get("quote", "")}"'
            for q in (memory.verbatim_quotes or [])
            if isinstance(q, dict) and q.get("quote")
        ])

        memory_context = (
            f"Title: {memory.title}\n"
            f"Time Period: {memory.time_period or 'Unknown'}\n"
            f"Location: {memory.location or 'Unspecified'}\n"
            f"Audio Timestamps: {memory.start_time or 0.0}s to {memory.end_time or 0.0}s\n"
            f"Authentic Summary: {memory.summary}\n"
            f"Grandfather's Actual Words/Quotes:\n{quotes or '  (None explicitly listed)'}\n"
            f"Grandfather's Life Advice: {memory.life_advice or 'None'}"
        )

        prompt = self.prompt_template.format(memory_context=memory_context)

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.2, # Conservative temperature to prevent hallucinating historical facts
                "top_p": 0.85
            }
        }

        # Steps 3 & 4: Call Gemma 3 to generate structured comparison
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{self.ollama_url}/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            raw_response = data.get("response", "{}")

        # Parse JSON robustly with strict=False and regex fallbacks
        parsed = self._parse_json_safely(raw_response)

        # Save to database
        comp = ThenNowComparison(
            memory_id=memory.id,
            topic=parsed.get("topic", memory.title),
            era_described=parsed.get("era_described", memory.time_period or "Grandfather's Era"),
            then_experience=parsed.get("then_experience", memory.summary),
            now_reality=parsed.get("now_reality", "In the 2020s modern era, technology and speed have transformed this aspect of daily life."),
            reflection_question=parsed.get("reflection_question", "How has this change affected our relationships and family connections today?"),
            enduring_value=parsed.get("enduring_value", "The enduring value of human connection and patience.")
        )
        db.add(comp)
        db.commit()
        db.refresh(comp)

        # Step 5: Always attach source audio
        return self._format_comparison_response(comp, memory)

comparison_service = ComparisonService()
