import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, Field

class QuoteSchema(BaseModel):
    quote: str
    significance: Optional[str] = None

class TranscriptSegmentResponse(BaseModel):
    id: int
    memory_id: str
    segment_index: int
    start_time: float
    end_time: float
    text: str

    class Config:
        from_attributes = True

class TranscriptSegmentItem(BaseModel):
    segment_index: int
    start_time: float
    end_time: float
    text: str
    avg_logprob: Optional[float] = None
    no_speech_prob: Optional[float] = None

class TranscriptProcessResponse(BaseModel):
    memory_id: str
    status: str
    detected_language: Optional[str] = None
    language_probability: Optional[float] = None
    model_used: Optional[str] = None
    duration_processed: Optional[float] = None
    full_transcript: str
    segment_count: int
    segments: List[TranscriptSegmentItem] = Field(default_factory=list)

    class Config:
        from_attributes = True

# --- AUDIO INGESTION SCHEMAS ---
class MemoryUploadResponse(BaseModel):
    memory_id: str
    file_name: str
    audio_path: str
    duration: float
    file_size_bytes: int
    status: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class MemoryBase(BaseModel):
    title: str
    summary: str
    time_period: Optional[str] = "Unknown"
    location: Optional[str] = "Unspecified"
    people_mentioned: List[str] = Field(default_factory=list)
    emotions: List[str] = Field(default_factory=list)
    verbatim_quotes: List[QuoteSchema] = Field(default_factory=list)
    life_advice: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    start_time: Optional[float] = 0.0
    end_time: Optional[float] = 0.0

class MemoryCreate(MemoryBase):
    memory_id: str

class MemoryResponse(MemoryBase):
    id: int
    memory_id: str
    audio_id: Optional[str] = None
    audio_source: Optional[str] = None
    audio_url: Optional[str] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class TimelineEraGroup(BaseModel):
    era: str
    time_period: str
    count: int
    memories: List[MemoryResponse] = Field(default_factory=list)

class TimelineResponse(BaseModel):
    total_memories: int
    eras: List[TimelineEraGroup] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)

class AudioRecordResponse(BaseModel):
    memory_id: str
    file_name: str
    audio_path: str
    duration: float
    file_size_bytes: int
    status: str
    created_at: datetime.datetime
    segments: List[TranscriptSegmentResponse] = Field(default_factory=list)
    memories: List[MemoryResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True

class SearchQuery(BaseModel):
    query: str
    limit: int = 5
    threshold: Optional[float] = 0.0
    topic: Optional[str] = None
    person: Optional[str] = None
    place: Optional[str] = None

class RelevantTimestamps(BaseModel):
    start_time: float
    end_time: float

class SearchResultItem(BaseModel):
    memory_id: str
    title: str
    summary: str
    similarity_score: float
    audio_source: Optional[str] = None
    relevant_timestamps: Optional[RelevantTimestamps] = None
    audio_timestamp_start: float
    audio_timestamp_end: Optional[float] = 0.0
    relevant_quote: Optional[str] = None
    search_match_type: Optional[str] = "hybrid"
    memory: Optional[MemoryResponse] = None

    class Config:
        from_attributes = True

class SearchResponse(BaseModel):
    query: str
    total_matches: int = 0
    results: List[SearchResultItem]

class AskQuery(BaseModel):
    question: str

class CitationSource(BaseModel):
    memory_id: str
    title: str
    summary: Optional[str] = None
    audio_id: str
    audio_source: Optional[str] = None
    audio_url: str
    timestamp_start: float = 0.0
    timestamp_end: float = 0.0
    start_time: float = 0.0
    end_time: float = 0.0
    relevant_timestamps: Optional[RelevantTimestamps] = None
    verbatim_quote: Optional[str] = ""
    similarity_score: Optional[float] = None
    memory_title: Optional[str] = None

class AskResponse(BaseModel):
    question: str
    answer: str
    sources: List[CitationSource] = Field(default_factory=list)
    citations: List[CitationSource] = Field(default_factory=list)
    grounded: bool = True

class CompareSourceAudio(BaseModel):
    memory_id: str
    title: str
    audio_id: str
    audio_source: Optional[str] = None
    audio_url: str
    start_time: float = 0.0
    end_time: float = 0.0
    verbatim_quote: Optional[str] = ""

class ComparisonResponse(BaseModel):
    id: Optional[int] = None
    memory_id: int
    topic: str
    era_described: str
    then_experience: str
    now_reality: str
    reflection_question: Optional[str] = None
    enduring_value: Optional[str] = None
    created_at: Optional[datetime.datetime] = None
    source_audio: Optional[CompareSourceAudio] = None
    # Convenience flat audio fields for direct UI access
    audio_id: Optional[str] = None
    audio_source: Optional[str] = None
    audio_url: Optional[str] = None
    start_time: Optional[float] = 0.0
    end_time: Optional[float] = 0.0
    verbatim_quote: Optional[str] = None
    memory_title: Optional[str] = None

    class Config:
        from_attributes = True

class CompareRequest(BaseModel):
    memory_id: Optional[Any] = None
    query: Optional[str] = None
    topic: Optional[str] = None
