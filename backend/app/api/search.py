from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.memory import (
    SearchQuery, SearchResponse, SearchResultItem,
    MemoryResponse, RelevantTimestamps
)
from app.services.retrieval import retrieval_service

router = APIRouter(prefix="/api/search", tags=["search"])

@router.post("", response_model=SearchResponse)
def search_memories(
    payload: SearchQuery,
    db: Session = Depends(get_db)
):
    """
    SEMANTIC + HYBRID RETRIEVAL ENDPOINT
    Goal: Natural language questions retrieve the most relevant memories.

    Pipeline:
    1. Vector similarity (BGE-M3 1024-dim dense embedding via HNSW)
    2. Keyword / full-text search across title, summary, tags, quotes, transcript
    3. Merge + re-rank (RRF + Weighted Score Fusion) -> top 3-5 memories

    Returns:
    memory_id, title, summary, similarity score, audio source, relevant timestamps
    """
    matches = retrieval_service.hybrid_search(
        db=db,
        query=payload.query,
        limit=payload.limit or 5,
        threshold=payload.threshold or 0.0,
        topic=payload.topic,
        person=payload.person,
        place=payload.place
    )

    items = []
    for res in matches:
        items.append(
            SearchResultItem(
                memory_id=res.memory.memory_id,
                title=res.memory.title,
                summary=res.memory.summary,
                similarity_score=res.similarity_score,
                audio_source=res.audio_source,
                relevant_timestamps=RelevantTimestamps(
                    start_time=res.start_time,
                    end_time=res.end_time
                ),
                audio_timestamp_start=res.start_time,
                audio_timestamp_end=res.end_time,
                relevant_quote=res.relevant_quote,
                search_match_type=res.search_match_type,
                memory=MemoryResponse.model_validate(res.memory)
            )
        )

    return SearchResponse(
        query=payload.query,
        total_matches=len(items),
        results=items
    )
