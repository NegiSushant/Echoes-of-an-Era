from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.memory import ThenNowComparison, ExtractedMemory
from app.schemas.memory import ComparisonResponse, CompareRequest
from app.services.comparison import comparison_service

router = APIRouter(prefix="/api/compare", tags=["compare"])

@router.post("", response_model=ComparisonResponse)
async def generate_comparison_endpoint(
    payload: Optional[CompareRequest] = Body(default=None),
    db: Session = Depends(get_db)
):
    """
    THEN VS NOW Signature Endpoint:
    POST /api/compare
    Flow:
    1. Retrieve relevant grandfather memories (via memory_id, query, or topic)
    2. Extract 'THEN' (only from his words, zero hallucination)
    3. Provide clearly separated modern context ('NOW')
    4. Generate comparison & reflection question
    5. Always show source audio with streaming link & timestamps
    """
    try:
        mem_id = payload.memory_id if payload else None
        query = payload.query if payload else None
        topic = payload.topic if payload else None

        comparison_data = await comparison_service.generate_comparison(
            db=db,
            memory_id=mem_id,
            query=query,
            topic=topic
        )
        return ComparisonResponse(**comparison_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison generation failed: {e}")

@router.post("/{memory_id}", response_model=ComparisonResponse)
async def generate_or_get_comparison_by_id(
    memory_id: str,
    db: Session = Depends(get_db)
):
    """
    Generates or retrieves a 'Then vs Now' comparison by memory_id (integer or string/UUID).
    """
    try:
        comparison_data = await comparison_service.generate_comparison(db, memory_id=memory_id)
        return ComparisonResponse(**comparison_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison generation failed: {e}")

@router.get("", response_model=List[ComparisonResponse])
def list_comparisons(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Lists all generated 'Then vs Now' historical reflections with source audio."""
    comparisons = (
        db.query(ThenNowComparison)
        .order_by(ThenNowComparison.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    results = []
    for comp in comparisons:
        mem = comp.memory or db.query(ExtractedMemory).filter(ExtractedMemory.id == comp.memory_id).first()
        if mem:
            results.append(ComparisonResponse(**comparison_service._format_comparison_response(comp, mem)))
        else:
            results.append(ComparisonResponse(
                id=comp.id,
                memory_id=comp.memory_id,
                topic=comp.topic,
                era_described=comp.era_described,
                then_experience=comp.then_experience,
                now_reality=comp.now_reality,
                reflection_question=comp.reflection_question,
                enduring_value=comp.enduring_value,
                created_at=comp.created_at
            ))

    return results
