import re
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, text
from app.models.memory import (
    ExtractedMemory, MemoryTopic, MemoryPerson, MemoryPlace,
    AudioRecord, MemoryTranscript, TranscriptSegment, HAS_VECTOR
)
from app.services.embeddings import embedding_service

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "has", "he", "in", "is", "it", "its", "of", "on", "that", "the",
    "to", "was", "were", "will", "with", "did", "does", "what", "when",
    "where", "who", "how", "grandpa", "grandfather", "tell", "about",
    "his", "her", "they", "them", "my", "your", "can", "could", "would"
}

class HybridSearchResult:
    def __init__(
        self,
        memory: ExtractedMemory,
        similarity_score: float,
        vector_score: float,
        keyword_score: float,
        search_match_type: str,
        relevant_quote: Optional[str] = None,
        audio_source: Optional[str] = None,
        start_time: float = 0.0,
        end_time: float = 0.0,
    ):
        self.memory = memory
        self.similarity_score = similarity_score
        self.vector_score = vector_score
        self.keyword_score = keyword_score
        self.search_match_type = search_match_type
        self.relevant_quote = relevant_quote
        self.audio_source = audio_source
        self.start_time = start_time
        self.end_time = end_time


class RetrievalService:
    """
    Hybrid Retrieval Service:
    1. Vector similarity search (BGE-M3 1024-dim dense vectors with HNSW index)
    2. Keyword & Lexical search across title, summary, tags, quotes, and transcripts
    3. Merge + Re-rank (Reciprocal Rank Fusion & Weighted Score Fusion)
    """

    def _extract_query_keywords(self, query: str) -> List[str]:
        tokens = re.findall(r"\b[A-Za-z0-9_]{3,}\b", query.lower())
        meaningful = [t for t in tokens if t not in STOPWORDS]
        return meaningful if meaningful else tokens

    def _score_keywords(self, mem: ExtractedMemory, transcript_text: str, keywords: List[str]) -> float:
        """Scores keyword relevance across multiple metadata fields."""
        if not keywords:
            return 0.0

        title_lower = (mem.title or "").lower()
        summary_lower = (mem.summary or "").lower()
        tags_lower = " ".join(str(t).lower() for t in (mem.tags or []))
        advice_lower = (mem.life_advice or "").lower()
        quotes_lower = " ".join(
            (q.get("quote", "") if isinstance(q, dict) else str(q)).lower()
            for q in (mem.verbatim_quotes or [])
        )
        transcript_lower = (transcript_text or "").lower()

        score = 0.0
        max_possible = len(keywords) * 6.0

        for kw in keywords:
            # Title match (high weight)
            if kw in title_lower:
                score += 3.0
            # Tags match (high weight)
            if kw in tags_lower:
                score += 2.5
            # Summary match (medium weight)
            if kw in summary_lower:
                score += 2.0
            # Quotes match (medium weight)
            if kw in quotes_lower:
                score += 2.0
            # Advice match
            if kw in advice_lower:
                score += 1.5
            # Transcript match
            if kw in transcript_lower:
                score += 1.0

        return min(round(score / max_possible, 4), 1.0) if max_possible > 0 else 0.0

    def hybrid_search(
        self,
        db: Session,
        query: str,
        limit: int = 5,
        threshold: float = 0.0,
        topic: Optional[str] = None,
        person: Optional[str] = None,
        place: Optional[str] = None,
    ) -> List[HybridSearchResult]:
        """
        Executes hybrid retrieval (Vector + Keyword + Fusion) and returns top ranked memories.
        """
        candidate_pool: Dict[int, ExtractedMemory] = {}
        vector_scores: Dict[int, float] = {}
        vector_ranks: Dict[int, int] = {}
        keyword_scores: Dict[int, float] = {}
        keyword_ranks: Dict[int, int] = {}

        # -------------------------------------------------------------
        # STEP 1: Vector Similarity Search (BGE-M3 1024-dim via HNSW)
        # -------------------------------------------------------------
        query_vector = embedding_service.embed_text(query)

        if HAS_VECTOR:
            vec_q = db.query(
                ExtractedMemory,
                (1.0 - ExtractedMemory.embedding.cosine_distance(query_vector)).label("vec_sim")
            ).filter(ExtractedMemory.embedding.isnot(None))

            # Optional relational filters
            if topic:
                vec_q = vec_q.join(ExtractedMemory.topics).filter(MemoryTopic.topic.ilike(f"%{topic}%"))
            if person:
                vec_q = vec_q.join(ExtractedMemory.people).filter(MemoryPerson.name.ilike(f"%{person}%"))
            if place:
                vec_q = vec_q.join(ExtractedMemory.places).filter(MemoryPlace.place_name.ilike(f"%{place}%"))

            vec_matches = (
                vec_q.order_by(ExtractedMemory.embedding.cosine_distance(query_vector))
                .limit(max(limit * 3, 15))
                .all()
            )

            for rank, (mem, sim) in enumerate(vec_matches, start=1):
                candidate_pool[mem.id] = mem
                vector_scores[mem.id] = max(float(sim), 0.0)
                vector_ranks[mem.id] = rank

        # -------------------------------------------------------------
        # STEP 2: Keyword / Lexical Search
        # -------------------------------------------------------------
        keywords = self._extract_query_keywords(query)

        # Query all candidate memories (or filtered candidates)
        kw_q = db.query(ExtractedMemory)
        if topic:
            kw_q = kw_q.join(ExtractedMemory.topics).filter(MemoryTopic.topic.ilike(f"%{topic}%"))
        if person:
            kw_q = kw_q.join(ExtractedMemory.people).filter(MemoryPerson.name.ilike(f"%{person}%"))
        if place:
            kw_q = kw_q.join(ExtractedMemory.places).filter(MemoryPlace.place_name.ilike(f"%{place}%"))

        all_candidates = kw_q.limit(50).all()

        # Fetch transcripts for candidate memories in a batch
        memory_ids = [m.memory_id for m in all_candidates if m.memory_id]
        transcripts_by_mid = {}
        if memory_ids:
            t_rows = db.query(MemoryTranscript).filter(MemoryTranscript.memory_id.in_(memory_ids)).all()
            transcripts_by_mid = {t.memory_id: t.full_transcript for t in t_rows}

        kw_ranked_list = []
        for mem in all_candidates:
            t_text = transcripts_by_mid.get(mem.memory_id, "")
            kw_s = self._score_keywords(mem, t_text, keywords)
            if kw_s > 0 or mem.id in candidate_pool:
                candidate_pool[mem.id] = mem
                kw_ranked_list.append((mem.id, kw_s))

        # Sort keyword candidates by score descending
        kw_ranked_list.sort(key=lambda x: x[1], reverse=True)
        for rank, (mid, score) in enumerate(kw_ranked_list, start=1):
            keyword_scores[mid] = score
            keyword_ranks[mid] = rank

        # -------------------------------------------------------------
        # STEP 3: Merge + Re-rank (Reciprocal Rank Fusion & Score Blend)
        # -------------------------------------------------------------
        fused_scores: List[Tuple[int, float, float, float, str]] = []

        k_rrf = 60.0
        w_vec = 0.65
        w_kw = 0.35

        for mid, mem in candidate_pool.items():
            vec_s = vector_scores.get(mid, 0.0)
            kw_s = keyword_scores.get(mid, 0.0)

            vec_rank = vector_ranks.get(mid, 999)
            kw_rank = keyword_ranks.get(mid, 999)

            # Reciprocal Rank Fusion component
            rrf_val = (w_vec / (k_rrf + vec_rank)) + (w_kw / (k_rrf + kw_rank))

            # Linear Score Blend
            score_blend = (w_vec * vec_s) + (w_kw * kw_s)

            # Both match bonus
            agreement_boost = 0.05 if (mid in vector_scores and kw_s > 0.05) else 0.0

            # Combined hybrid score (scaled to ~0-1)
            hybrid_score = round(score_blend + (rrf_val * 10.0) + agreement_boost, 4)

            # Match type classification
            if mid in vector_scores and kw_s > 0.1:
                match_type = "hybrid"
            elif mid in vector_scores:
                match_type = "semantic_vector"
            else:
                match_type = "keyword"

            fused_scores.append((mid, hybrid_score, vec_s, kw_s, match_type))

        # Sort descending by hybrid score
        fused_scores.sort(key=lambda x: x[1], reverse=True)

        # -------------------------------------------------------------
        # STEP 4: Format Final Results
        # -------------------------------------------------------------
        results: List[HybridSearchResult] = []

        # Pre-fetch AudioRecord to get audio source filename / duration
        audio_by_mid = {}
        if candidate_pool:
            cand_mids = [m.memory_id for m in candidate_pool.values() if m.memory_id]
            if cand_mids:
                a_rows = db.query(AudioRecord).filter(AudioRecord.memory_id.in_(cand_mids)).all()
                audio_by_mid = {a.memory_id: a for a in a_rows}

        for mid, h_score, v_score, k_score, m_type in fused_scores:
            if h_score < threshold:
                continue

            mem = candidate_pool[mid]
            audio_rec = audio_by_mid.get(mem.memory_id)

            # Best matching quote
            best_quote = None
            if mem.verbatim_quotes and isinstance(mem.verbatim_quotes, list):
                # Search for quote containing keywords if possible
                for q in mem.verbatim_quotes:
                    q_text = q.get("quote", "") if isinstance(q, dict) else str(q)
                    if any(kw in q_text.lower() for kw in keywords):
                        best_quote = q_text
                        break
                if not best_quote and len(mem.verbatim_quotes) > 0:
                    first = mem.verbatim_quotes[0]
                    best_quote = first.get("quote") if isinstance(first, dict) else str(first)

            audio_src = audio_rec.file_name if audio_rec else f"memory_{mem.memory_id}.wav"
            start_t = mem.start_time or 0.0
            end_t = mem.end_time or (audio_rec.duration if audio_rec else 0.0)

            results.append(
                HybridSearchResult(
                    memory=mem,
                    similarity_score=h_score,
                    vector_score=round(v_score, 4),
                    keyword_score=round(k_score, 4),
                    search_match_type=m_type,
                    relevant_quote=best_quote,
                    audio_source=audio_src,
                    start_time=start_t,
                    end_time=end_t
                )
            )

            if len(results) >= limit:
                break

        return results

    # Backward compatibility helper
    def search_memories(
        self,
        db: Session,
        query: str,
        limit: int = 5,
        threshold: float = 0.0,
        topic: Optional[str] = None,
        person: Optional[str] = None,
        place: Optional[str] = None,
    ) -> List[Tuple[ExtractedMemory, float]]:
        hybrid_results = self.hybrid_search(
            db=db,
            query=query,
            limit=limit,
            threshold=threshold,
            topic=topic,
            person=person,
            place=place
        )
        return [(r.memory, r.similarity_score) for r in hybrid_results]


retrieval_service = RetrievalService()
