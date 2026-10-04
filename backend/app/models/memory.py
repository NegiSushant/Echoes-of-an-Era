import datetime
import uuid
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

try:
    from pgvector.sqlalchemy import Vector
    HAS_VECTOR = True
except ImportError:
    HAS_VECTOR = False

from app.db.database import Base

class AudioRecord(Base):
    """
    Primary record of grandfather's authentic audio recording.
    The original audio is preserved permanently as the single source of truth.
    Status transitions: uploaded -> processing -> completed / failed
    """
    __tablename__ = "audio_records"

    memory_id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    file_name = Column(String(255), nullable=False)
    audio_path = Column(String(512), nullable=False, unique=True)
    duration = Column(Float, default=0.0)
    file_size_bytes = Column(Integer, default=0)
    status = Column(String(50), default="uploaded", nullable=False)  # uploaded -> processing -> completed / failed
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships for subsequent pipeline phases
    transcript = relationship("MemoryTranscript", back_populates="audio", uselist=False, cascade="all, delete-orphan")
    segments = relationship("TranscriptSegment", back_populates="audio", cascade="all, delete-orphan")
    memories = relationship("ExtractedMemory", back_populates="audio", cascade="all, delete-orphan")


class MemoryTranscript(Base):
    """
    Complete transcript record of grandfather's recording, including full text
    and JSON serialized segment timestamps.
    """
    __tablename__ = "memory_transcripts"

    id = Column(Integer, primary_key=True, index=True)
    memory_id = Column(String(36), ForeignKey("audio_records.memory_id"), nullable=False, unique=True, index=True)
    full_transcript = Column(Text, nullable=False)
    segments_json = Column(JSON, nullable=False)
    detected_language = Column(String(50), nullable=True)
    language_probability = Column(Float, nullable=True)
    model_used = Column(String(100), nullable=True)
    duration_processed = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    audio = relationship("AudioRecord", back_populates="transcript")


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"

    id = Column(Integer, primary_key=True, index=True)
    memory_id = Column(String(36), ForeignKey("audio_records.memory_id"), nullable=False, index=True)
    segment_index = Column(Integer, nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    text = Column(Text, nullable=False)

    audio = relationship("AudioRecord", back_populates="segments")


class ExtractedMemory(Base):
    __tablename__ = "extracted_memories"

    id = Column(Integer, primary_key=True, index=True)
    memory_id = Column(String(36), ForeignKey("audio_records.memory_id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    time_period = Column(String(100), default="Unknown")
    location = Column(String(255), default="Unspecified")
    people_mentioned = Column(JSON, default=list)
    emotions = Column(JSON, default=list)
    verbatim_quotes = Column(JSON, default=list)
    life_advice = Column(Text, nullable=True)
    tags = Column(JSON, default=list)
    start_time = Column(Float, default=0.0)
    end_time = Column(Float, default=0.0)

    if HAS_VECTOR:
        embedding = Column(Vector(1024), nullable=True)
    else:
        embedding = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    audio = relationship("AudioRecord", back_populates="memories")
    comparisons = relationship("ThenNowComparison", back_populates="memory", cascade="all, delete-orphan")
    topics = relationship("MemoryTopic", back_populates="memory", cascade="all, delete-orphan")
    people = relationship("MemoryPerson", back_populates="memory", cascade="all, delete-orphan")
    places = relationship("MemoryPlace", back_populates="memory", cascade="all, delete-orphan")


class MemoryTopic(Base):
    """Normalized topics/tags associated with an extracted memory."""
    __tablename__ = "memory_topics"

    id = Column(Integer, primary_key=True, index=True)
    memory_id = Column(Integer, ForeignKey("extracted_memories.id"), nullable=False, index=True)
    topic = Column(String(100), nullable=False, index=True)

    memory = relationship("ExtractedMemory", back_populates="topics")


class MemoryPerson(Base):
    """People mentioned in an extracted grandfather memory."""
    __tablename__ = "memory_people"

    id = Column(Integer, primary_key=True, index=True)
    memory_id = Column(Integer, ForeignKey("extracted_memories.id"), nullable=False, index=True)
    name = Column(String(150), nullable=False, index=True)
    relationship_to_narrator = Column(String(100), nullable=True)

    memory = relationship("ExtractedMemory", back_populates="people")


class MemoryPlace(Base):
    """Geographic locations/places mentioned in an extracted memory."""
    __tablename__ = "memory_places"

    id = Column(Integer, primary_key=True, index=True)
    memory_id = Column(Integer, ForeignKey("extracted_memories.id"), nullable=False, index=True)
    place_name = Column(String(200), nullable=False, index=True)

    memory = relationship("ExtractedMemory", back_populates="places")


class ThenNowComparison(Base):
    __tablename__ = "then_now_comparisons"

    id = Column(Integer, primary_key=True, index=True)
    memory_id = Column(Integer, ForeignKey("extracted_memories.id"), nullable=False, index=True)
    topic = Column(String(255), nullable=False)
    era_described = Column(String(100), nullable=False)
    then_experience = Column(Text, nullable=False)
    now_reality = Column(Text, nullable=False)
    reflection_question = Column(Text, nullable=True)
    enduring_value = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    memory = relationship("ExtractedMemory", back_populates="comparisons")
