import os
import httpx
from pathlib import Path
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.services.retrieval import retrieval_service

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

class RAGService:
    def __init__(self, ollama_url: str = None, model: str = None):
        self.ollama_url = (ollama_url or os.getenv("LLM_BASE_URL") or os.getenv("OLLAMA_BASE_URL", "http://localhost:12434")).rstrip("/")
        self.model = model or os.getenv("LLM_MODEL") or os.getenv("OLLAMA_MODEL", "gemma3:1B-Q4_K_M")

        prompt_file = PROMPTS_DIR / "rag.txt"
        with open(prompt_file, "r", encoding="utf-8") as f:
            self.prompt_template = f.read()

    async def answer_question(self, db: Session, question: str) -> Dict[str, Any]:
        """
        Grounded RAG (Ask Grandpa):
        1. Hybrid retrieval (BGE-M3 dense vector + keyword search + fusion)
        2. Strict zero-hallucination prompting to Gemma 3
        3. Returns grounded answer + sources with full audio playback capability
        """
        clean_question = (question or "").strip()
        if not clean_question:
            return {
                "question": question,
                "answer": "Please ask a question about Grandfather's memories.",
                "sources": [],
                "citations": [],
                "grounded": True
            }

        # 1. Retrieve top matching memories via Hybrid Search
        hybrid_results = retrieval_service.hybrid_search(
            db=db,
            query=clean_question,
            limit=4,
            threshold=0.15
        )

        # Insufficient evidence guardrail: No memories matched the threshold
        if not hybrid_results or hybrid_results[0].similarity_score < 0.20:
            return {
                "question": clean_question,
                "answer": "Grandfather has not spoken about this in his recorded memories.",
                "sources": [],
                "citations": [],
                "grounded": True
            }

        # 2. Build context block with memory facts, timestamps, and verbatim quotes
        context_parts = []
        sources = []

        for res in hybrid_results:
            mem = res.memory
            quotes = "\n".join([
                f'  - "{q.get("quote", "")}"'
                for q in (mem.verbatim_quotes or [])
                if isinstance(q, dict) and q.get("quote")
            ])

            context_parts.append(
                f"[Memory ID: {mem.memory_id}]\n"
                f"Title: {mem.title}\n"
                f"Time Period: {mem.time_period or 'Unknown'} | Location: {mem.location or 'Unspecified'}\n"
                f"Recorded Audio Timestamps: {res.start_time:.1f}s to {res.end_time:.1f}s\n"
                f"Summary: {mem.summary}\n"
                f"Grandfather's Actual Quotes:\n{quotes or '  (No explicit quote tagged)'}\n"
                f"Life Advice / Reflections: {mem.life_advice or 'None recorded'}\n"
            )

            # Determine best quote for citation badge
            quote_text = res.relevant_quote or ""
            if not quote_text and mem.verbatim_quotes and isinstance(mem.verbatim_quotes, list):
                first_q = mem.verbatim_quotes[0]
                quote_text = first_q.get("quote", "") if isinstance(first_q, dict) else str(first_q)

            source_item = {
                "memory_id": str(mem.memory_id),
                "title": mem.title,
                "memory_title": mem.title,
                "summary": mem.summary,
                "audio_id": str(mem.memory_id),
                "audio_source": res.audio_source or f"memory_{mem.memory_id}.wav",
                "audio_url": f"/api/memories/audio/{mem.memory_id}/stream",
                "timestamp_start": float(res.start_time),
                "timestamp_end": float(res.end_time),
                "start_time": float(res.start_time),
                "end_time": float(res.end_time),
                "relevant_timestamps": {
                    "start_time": float(res.start_time),
                    "end_time": float(res.end_time)
                },
                "verbatim_quote": quote_text,
                "similarity_score": round(float(res.similarity_score), 4)
            }
            sources.append(source_item)

        context_str = "\n---\n".join(context_parts)
        prompt = self.prompt_template.format(context=context_str, question=clean_question)

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2, # Conservative temperature for strict grounding
                "top_p": 0.85
            }
        }

        # 3. Call local Docker Model Runner (Gemma 3)
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{self.ollama_url}/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            answer_text = data.get("response", "").strip()

        # Check if the model explicitly stated it cannot answer
        insufficient_phrases = [
            "grandfather has not spoken about this",
            "not spoken about this in his recorded memories",
            "no mention of this in the provided",
            "not mentioned in his recorded memories"
        ]
        is_insufficient = any(phrase in answer_text.lower() for phrase in insufficient_phrases)

        final_sources = [] if is_insufficient else sources

        return {
            "question": clean_question,
            "answer": answer_text,
            "sources": final_sources,
            "citations": final_sources, # Dual support for sources and citations
            "grounded": True
        }

rag_service = RAGService()
