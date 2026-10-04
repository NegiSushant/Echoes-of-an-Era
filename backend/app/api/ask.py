from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.memory import AskQuery, AskResponse
from app.services.rag import rag_service

router = APIRouter(prefix="/api/ask", tags=["ask"])

@router.post("", response_model=AskResponse)
async def ask_grandfather(
    payload: AskQuery,
    db: Session = Depends(get_db)
):
    """
    Grounded RAG endpoint:
    Consults grandfather's living voice archive.
    Answers strictly using his recorded words and provides timestamped audio links.
    """
    result = await rag_service.answer_question(db=db, question=payload.question)
    return AskResponse(**result)
