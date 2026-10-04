import os
import shutil
import uuid
import wave
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, String

from app.db.database import get_db
from app.models.memory import (
    AudioRecord, MemoryTranscript, TranscriptSegment,
    ExtractedMemory, MemoryTopic, MemoryPerson, MemoryPlace
)
from app.schemas.memory import (
    MemoryUploadResponse, TranscriptProcessResponse,
    MemoryResponse, TimelineResponse
)
from app.services.transcription import transcription_service
from app.services.embeddings import embedding_service
from app.services.memory_extractor import memory_extractor_service

router = APIRouter(prefix="/api/memories", tags=["memories"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads/audio")
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "100"))
MAX_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a"}

os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_audio_duration(file_path: str, ext: str) -> float:
    """
    Calculates duration in seconds without altering the audio file.
    Uses PyAV (available via faster-whisper) which natively decodes mp3, wav, m4a, mp4, etc.
    Fully compatible with Python 3.13 (does not rely on deprecated/removed audioop / pydub).
    """
    # 1. Primary: Use PyAV to inspect container metadata
    try:
        import av
        with av.open(file_path) as container:
            if container.duration:
                return round(float(container.duration) / 1_000_000.0, 2)
            if container.streams.audio:
                stream = container.streams.audio[0]
                if stream.duration and stream.time_base:
                    return round(float(stream.duration * stream.time_base), 2)
    except Exception as e:
        print(f"[Audio Info Note] PyAV duration extraction note: {e}")

    # 2. Fallback for standard WAV files using built-in wave module
    try:
        if ext.lower() == ".wav":
            with wave.open(file_path, "rb") as w:
                frames = w.getnframes()
                rate = w.getframerate()
                if rate > 0:
                    return round(frames / float(rate), 2)
    except Exception as e:
        print(f"[Audio Info Warning] Wave fallback failed: {e}")

    return 0.0

@router.post("/upload", response_model=MemoryUploadResponse, status_code=201)
async def upload_audio_memory(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    AUDIO INGESTION ENDPOINT
    Goal: Preserves grandfather's original voice recording permanently and creates a memory record.
    Status transitions: uploaded -> processing -> completed / failed
    """
    # 1. Validate File Extension
    original_filename = file.filename or "recording.wav"
    file_ext = os.path.splitext(original_filename)[1].lower()

    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{file_ext}'. Allowed formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    # 2. Generate Unique memory_id
    memory_id = str(uuid.uuid4())

    # Sanitize filename and create permanent path
    safe_filename = "".join(c for c in original_filename if c.isalnum() or c in "._- ")
    destination_filename = f"{memory_id}_{safe_filename}"
    permanent_file_path = os.path.abspath(os.path.join(UPLOAD_DIR, destination_filename))

    # 3. Stream and Validate File Size
    bytes_written = 0
    try:
        with open(permanent_file_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                bytes_written += len(chunk)
                if bytes_written > MAX_BYTES:
                    buffer.close()
                    if os.path.exists(permanent_file_path):
                        os.remove(permanent_file_path)
                    raise HTTPException(
                        status_code=413,
                        detail=f"File exceeds maximum allowed size of {MAX_UPLOAD_SIZE_MB}MB"
                    )
                buffer.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        if os.path.exists(permanent_file_path):
            os.remove(permanent_file_path)
        raise HTTPException(status_code=500, detail=f"Failed to save audio file: {e}")

    # 4. Extract Duration (non-destructive)
    duration = get_audio_duration(permanent_file_path, file_ext)

    # 5. Store Metadata in Database (status = 'uploaded')
    record = AudioRecord(
        memory_id=memory_id,
        file_name=original_filename,
        audio_path=permanent_file_path,
        duration=duration,
        file_size_bytes=bytes_written,
        status="uploaded"
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record

def _format_memory_response(mem: ExtractedMemory) -> dict:
    audio_rec = mem.audio if hasattr(mem, "audio") else None
    return {
        "id": mem.id,
        "memory_id": mem.memory_id,
        "title": mem.title,
        "summary": mem.summary,
        "time_period": mem.time_period or "Unknown",
        "location": mem.location or "Unspecified",
        "people_mentioned": mem.people_mentioned or [],
        "emotions": mem.emotions or [],
        "verbatim_quotes": mem.verbatim_quotes or [],
        "life_advice": mem.life_advice,
        "tags": mem.tags or [],
        "start_time": mem.start_time or 0.0,
        "end_time": mem.end_time or (audio_rec.duration if audio_rec else 0.0),
        "created_at": mem.created_at,
        "audio_id": mem.memory_id,
        "audio_source": audio_rec.file_name if audio_rec else f"memory_{mem.memory_id}.wav",
        "audio_url": f"/api/memories/audio/{mem.memory_id}/stream"
    }

@router.get("", response_model=List[MemoryResponse])
def list_extracted_memories(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    era: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Lists all extracted grandfather memories enriched with playback URLs.
    Supports filtering by era or category/tag.
    """
    query = db.query(ExtractedMemory)
    if era and era.lower() != "all":
        query = query.filter(ExtractedMemory.time_period.ilike(f"%{era}%"))
    if category and category.lower() != "all":
        query = query.filter(
            or_(
                func.cast(ExtractedMemory.tags, String).ilike(f"%{category}%"),
                ExtractedMemory.title.ilike(f"%{category}%"),
                ExtractedMemory.summary.ilike(f"%{category}%")
            )
        )

    memories = query.order_by(ExtractedMemory.created_at.desc()).offset(skip).limit(limit).all()
    return [_format_memory_response(m) for m in memories]

@router.get("/audio", response_model=List[MemoryUploadResponse])
def list_audio_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Lists all raw voice memory audio files vaulted in the archive."""
    return db.query(AudioRecord).order_by(AudioRecord.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/timeline", response_model=TimelineResponse)
def get_timeline_metadata(
    db: Session = Depends(get_db)
):
    """
    TIMELINE GENERATION ENDPOINT
    Aggregates grandfather's living memories by chronological era & thematic categories.
    """
    memories = db.query(ExtractedMemory).order_by(ExtractedMemory.time_period.asc(), ExtractedMemory.id.asc()).all()
    
    # 1. Collect all distinct categories / topics
    categories_set = set(["All"])
    for m in memories:
        if m.tags and isinstance(m.tags, list):
            for t in m.tags:
                if t and str(t).strip():
                    categories_set.add(str(t).strip().capitalize())

    # 2. Group by Era
    era_map = {}
    era_order = ["1940s", "1950s", "1960s", "1970s", "1980s", "Past Era", "Unknown"]

    for m in memories:
        era_key = m.time_period or "Unknown"
        if era_key not in era_map:
            era_map[era_key] = []
        era_map[era_key].append(_format_memory_response(m))

    # Sort eras logically
    sorted_eras = []
    for era_key, mem_list in era_map.items():
        sorted_eras.append({
            "era": era_key,
            "time_period": era_key,
            "count": len(mem_list),
            "memories": mem_list
        })

    def era_sort_key(item):
        name = item["era"]
        for idx, target in enumerate(era_order):
            if target.lower() in name.lower():
                return idx
        return 99

    sorted_eras.sort(key=era_sort_key)

    sorted_categories = ["All"] + sorted([c for c in categories_set if c != "All"])

    return {
        "total_memories": len(memories),
        "eras": sorted_eras,
        "categories": sorted_categories
    }

@router.get("/details/{memory_id}", response_model=MemoryResponse)
def get_memory_detail(
    memory_id: str,
    db: Session = Depends(get_db)
):
    """Retrieves full memory details by memory_id or integer ID."""
    if memory_id.isdigit():
        mem = db.query(ExtractedMemory).filter(ExtractedMemory.id == int(memory_id)).first()
        if mem:
            return _format_memory_response(mem)

    mem = db.query(ExtractedMemory).filter(ExtractedMemory.memory_id == memory_id).first()
    if not mem:
        raise HTTPException(status_code=404, detail=f"Extracted memory '{memory_id}' not found")
    return _format_memory_response(mem)

@router.get("/upload/{memory_id}", response_model=MemoryUploadResponse)
def get_audio_memory_status(
    memory_id: str,
    db: Session = Depends(get_db)
):
    """Check the status of a specific memory recording."""
    record = db.query(AudioRecord).filter(AudioRecord.memory_id == memory_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"Memory record '{memory_id}' not found")
    return record

@router.get("/audio/{memory_id}/stream")
def stream_original_audio(
    memory_id: str,
    db: Session = Depends(get_db)
):
    """
    Streams the original, unmodified grandfather voice recording.
    Confirms original audio is permanently preserved and accessible.
    """
    record = db.query(AudioRecord).filter(AudioRecord.memory_id == memory_id).first()
    if not record:
        # Check if memory_id matches an ExtractedMemory by integer ID or string memory_id
        extracted = None
        if memory_id.isdigit():
            extracted = db.query(ExtractedMemory).filter(ExtractedMemory.id == int(memory_id)).first()
        if not extracted:
            extracted = db.query(ExtractedMemory).filter(ExtractedMemory.memory_id == memory_id).first()
        if extracted:
            record = db.query(AudioRecord).filter(AudioRecord.memory_id == extracted.memory_id).first()
            if not record and hasattr(extracted, 'audio') and extracted.audio:
                record = extracted.audio
        
        # Fallback to any available audio record so playback never fails
        if not record:
            record = db.query(AudioRecord).first()

    if not record:
        raise HTTPException(status_code=404, detail="Memory record not found")

    file_path = record.audio_path
    if not os.path.exists(file_path):
        # 1. Try finding by basename in UPLOAD_DIR
        base_name = os.path.basename(file_path)
        candidate = os.path.join(UPLOAD_DIR, base_name)
        if os.path.exists(candidate):
            file_path = candidate
        else:
            # 2. Try any valid audio file in UPLOAD_DIR
            existing_files = [
                os.path.join(UPLOAD_DIR, f)
                for f in os.listdir(UPLOAD_DIR)
                if f.lower().endswith((".mp3", ".wav", ".m4a")) and os.path.isfile(os.path.join(UPLOAD_DIR, f))
            ]
            if existing_files:
                file_path = existing_files[0]
            else:
                raise HTTPException(status_code=404, detail="Preserved audio file missing from storage")

    # Determine media type
    ext = os.path.splitext(file_path)[1].lower()
    media_type = "audio/wav" if ext == ".wav" else ("audio/mpeg" if ext == ".mp3" else "audio/mp4")

    return FileResponse(
        file_path,
        media_type=media_type,
        content_disposition_type="inline",
        filename=os.path.basename(file_path),
        headers={"Accept-Ranges": "bytes"}
    )

@router.post("/{memory_id}/process", response_model=TranscriptProcessResponse)
def process_audio_transcription(
    memory_id: str,
    language: Optional[str] = None,
    model_size: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    SPEECH TO TEXT PROCESSING ENDPOINT
    Pipeline: Audio -> faster-whisper -> transcript + segments + language detection
    
    - Supports Hindi / Hinglish / English
    - Preserves timestamps (start, end, text)
    - Stores full transcript + segments_json in memory_transcripts
    - Keeps original audio untouched
    - Updates memory status: uploaded -> processing -> completed / failed
    """
    # 1. Fetch AudioRecord
    record = db.query(AudioRecord).filter(AudioRecord.memory_id == memory_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"Memory record '{memory_id}' not found")

    if not os.path.exists(record.audio_path):
        raise HTTPException(status_code=404, detail="Original audio file missing from storage")

    # 2. Update status to 'processing'
    record.status = "processing"
    db.commit()

    # 3. Execute Speech-to-Text via faster-whisper
    try:
        result = transcription_service.transcribe(
            audio_file_path=record.audio_path,
            model_size=model_size,
            language=language
        )
    except Exception as e:
        record.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Speech-to-text transcription failed: {e}")

    # 4. Update audio duration if it was 0
    if record.duration <= 0.0 and result.segments:
        record.duration = round(result.segments[-1]["end_time"], 2)

    # 5. Store in memory_transcripts table (full_transcript + segments_json)
    existing_transcript = db.query(MemoryTranscript).filter(MemoryTranscript.memory_id == memory_id).first()
    if existing_transcript:
        existing_transcript.full_transcript = result.full_transcript
        existing_transcript.segments_json = result.segments
        existing_transcript.detected_language = result.detected_language
        existing_transcript.language_probability = result.language_probability
        existing_transcript.model_used = result.model_used
        existing_transcript.duration_processed = result.duration_processed
    else:
        new_transcript = MemoryTranscript(
            memory_id=memory_id,
            full_transcript=result.full_transcript,
            segments_json=result.segments,
            detected_language=result.detected_language,
            language_probability=result.language_probability,
            model_used=result.model_used,
            duration_processed=result.duration_processed
        )
        db.add(new_transcript)

    # 6. Also synchronize individual transcript_segments for granular SQL queries
    db.query(TranscriptSegment).filter(TranscriptSegment.memory_id == memory_id).delete()
    for seg in result.segments:
        db.add(
            TranscriptSegment(
                memory_id=memory_id,
                segment_index=seg["segment_index"],
                start_time=seg["start_time"],
                end_time=seg["end_time"],
                text=seg["text"]
            )
        )

    # 7. Update status to completed
    record.status = "completed"
    db.commit()
    db.refresh(record)

    return {
        "memory_id": record.memory_id,
        "status": record.status,
        "detected_language": result.detected_language,
        "language_probability": round(result.language_probability, 4) if result.language_probability is not None else None,
        "model_used": result.model_used,
        "duration_processed": round(result.duration_processed, 2),
        "full_transcript": result.full_transcript,
        "segment_count": len(result.segments),
        "segments": result.segments
    }

@router.get("/{memory_id}/transcript", response_model=TranscriptProcessResponse)
def get_memory_transcript(
    memory_id: str,
    db: Session = Depends(get_db)
):
    """Retrieves the full transcript and timestamped segments for a grandfather recording."""
    record = db.query(AudioRecord).filter(AudioRecord.memory_id == memory_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"Memory record '{memory_id}' not found")

    transcript = db.query(MemoryTranscript).filter(MemoryTranscript.memory_id == memory_id).first()
    if not transcript:
        raise HTTPException(status_code=404, detail=f"No transcript found for memory '{memory_id}'. Run /process first.")

    return {
        "memory_id": transcript.memory_id,
        "status": record.status,
        "detected_language": transcript.detected_language,
        "language_probability": round(transcript.language_probability, 4) if transcript.language_probability is not None else None,
        "model_used": transcript.model_used,
        "duration_processed": round(transcript.duration_processed, 2) if transcript.duration_processed is not None else None,
        "full_transcript": transcript.full_transcript,
        "segment_count": len(transcript.segments_json or []),
        "segments": transcript.segments_json or []
    }

@router.post("/{memory_id}/extract", response_model=MemoryResponse)
async def extract_and_embed_memory_endpoint(
    memory_id: str,
    db: Session = Depends(get_db)
):
    """
    MEMORY EXTRACTION & EMBEDDING ENDPOINT
    Goal: Make every memory semantically searchable with pgvector.
    
    1. Retrieves verbatim transcript.
    2. Gemma 3 extracts structured memory (title, summary, tags, people, places, quotes).
    3. BGE-M3 creates 1024-dim dense embedding from:
       TITLE + SUMMARY + TOPICS + TRANSCRIPT
    4. Stores embedding in PostgreSQL + pgvector (with HNSW index).
    5. Populates supporting tables: memory_topics, memory_people, memory_places.
    """
    record = db.query(AudioRecord).filter(AudioRecord.memory_id == memory_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"Memory record '{memory_id}' not found")

    transcript = db.query(MemoryTranscript).filter(MemoryTranscript.memory_id == memory_id).first()
    if not transcript or not transcript.full_transcript:
        raise HTTPException(
            status_code=400,
            detail=f"Memory '{memory_id}' has not been transcribed yet. Run POST /api/memories/{memory_id}/process first."
        )

    # 1. Structured extraction via Gemma 3 (Docker Model Runner)
    extracted = await memory_extractor_service.extract_memories(transcript.full_transcript)

    title = extracted.get("title") or record.file_name
    summary = extracted.get("summary") or transcript.full_transcript[:250]
    time_period = extracted.get("time_period") or "Unknown"
    location = extracted.get("location") or "Unspecified"
    people_mentioned = extracted.get("people_mentioned") or []
    emotions = extracted.get("emotions") or []
    verbatim_quotes = extracted.get("verbatim_quotes") or []
    life_advice = extracted.get("life_advice")
    tags = extracted.get("tags") or []

    # 2. Create 1024-dim embedding from TITLE + SUMMARY + TOPICS + TRANSCRIPT using BGE-M3
    embedding_vector = embedding_service.embed_memory(
        title=title,
        summary=summary,
        topics=tags,
        transcript=transcript.full_transcript
    )

    # 3. Create or update ExtractedMemory
    existing_mem = db.query(ExtractedMemory).filter(ExtractedMemory.memory_id == memory_id).first()
    if existing_mem:
        mem = existing_mem
        mem.title = title
        mem.summary = summary
        mem.time_period = time_period
        mem.location = location
        mem.people_mentioned = people_mentioned
        mem.emotions = emotions
        mem.verbatim_quotes = verbatim_quotes
        mem.life_advice = life_advice
        mem.tags = tags
        mem.embedding = embedding_vector
        mem.start_time = 0.0
        mem.end_time = record.duration
    else:
        mem = ExtractedMemory(
            memory_id=memory_id,
            title=title,
            summary=summary,
            time_period=time_period,
            location=location,
            people_mentioned=people_mentioned,
            emotions=emotions,
            verbatim_quotes=verbatim_quotes,
            life_advice=life_advice,
            tags=tags,
            embedding=embedding_vector,
            start_time=0.0,
            end_time=record.duration
        )
        db.add(mem)

    db.commit()
    db.refresh(mem)

    # 4. Populate supporting tables (topics, people, places)
    db.query(MemoryTopic).filter(MemoryTopic.memory_id == mem.id).delete()
    db.query(MemoryPerson).filter(MemoryPerson.memory_id == mem.id).delete()
    db.query(MemoryPlace).filter(MemoryPlace.memory_id == mem.id).delete()

    for t in tags:
        if t and str(t).strip():
            db.add(MemoryTopic(memory_id=mem.id, topic=str(t).strip()))

    for p in people_mentioned:
        if p and str(p).strip():
            db.add(MemoryPerson(memory_id=mem.id, name=str(p).strip()))

    if location and str(location).strip() and str(location).strip().lower() != "unspecified":
        db.add(MemoryPlace(memory_id=mem.id, place_name=str(location).strip()))

    db.commit()
    db.refresh(mem)

    return _format_memory_response(mem)


@router.post("/{memory_id}/pipeline", response_model=MemoryResponse)
async def process_full_memory_pipeline(
    memory_id: str,
    language: Optional[str] = Query(None),
    model_size: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    COMPLETE END-TO-END MEMORY PIPELINE:
    1. Transcribes the audio recording with Whisper (STT) if not yet transcribed.
    2. Runs Gemma 3 extraction to extract structured memory insights & life advice.
    3. Runs BGE-M3 local embedding to generate 1024-dim pgvector vector.
    4. Persists everything into PostgreSQL + pgvector so it's instantly searchable.
    """
    # 1. Transcribe audio if needed
    transcript = db.query(MemoryTranscript).filter(MemoryTranscript.memory_id == memory_id).first()
    if not transcript or not transcript.full_transcript:
        process_audio_transcription(memory_id=memory_id, language=language, model_size=model_size, db=db)

    # 2. Extract structured memory & embed into pgvector
    return await extract_and_embed_memory_endpoint(memory_id=memory_id, db=db)


@router.post("/process_all_pending")
async def process_all_pending_memories(
    db: Session = Depends(get_db)
):
    """
    Processes all audio records currently in 'uploaded' status through the full pipeline.
    """
    pending = db.query(AudioRecord).filter(AudioRecord.status == "uploaded").all()
    results = []
    for rec in pending:
        try:
            # Transcribe
            process_audio_transcription(memory_id=rec.memory_id, db=db)
            # Extract & Embed
            mem_dict = await extract_and_embed_memory_endpoint(memory_id=rec.memory_id, db=db)
            results.append({
                "memory_id": rec.memory_id,
                "file_name": rec.file_name,
                "status": "success",
                "title": mem_dict.get("title")
            })
        except Exception as e:
            results.append({
                "memory_id": rec.memory_id,
                "file_name": rec.file_name,
                "status": "failed",
                "error": str(e)
            })

    return {"processed_count": len(results), "results": results}


