import os
import hashlib
import json
from fastapi.testclient import TestClient
from dotenv import load_dotenv

load_dotenv()

from app.main import app
from app.db.database import SessionLocal
from app.models.memory import AudioRecord, MemoryTranscript, TranscriptSegment

client = TestClient(app)

def run_stt_verification():
    print("=" * 70)
    print("SPEECH-TO-TEXT PIPELINE VERIFICATION SUITE")
    print("=" * 70)

    memory_id = "b736fd2c-6e1e-4d2b-a0b4-b6263ca55418"

    # 1. Verify Audio Record exists and get initial MD5
    db = SessionLocal()
    record = db.query(AudioRecord).filter(AudioRecord.memory_id == memory_id).first()
    assert record is not None, f"AudioRecord '{memory_id}' not found in database!"
    print(f" [1/6] Audio Record Found: {record.file_name} (Initial Status: {record.status})")

    with open(record.audio_path, "rb") as f:
        orig_bytes = f.read()
        orig_md5 = hashlib.md5(orig_bytes).hexdigest()
        orig_len = len(orig_bytes)
    print(f"       Original Audio File: {record.audio_path}")
    print(f"       Size: {orig_len} bytes | MD5: {orig_md5}")

    # 2. Call POST /api/memories/{memory_id}/process
    print(f"\n [2/6] Executing POST /api/memories/{memory_id}/process?model_size=tiny...")
    resp = client.post(f"/api/memories/{memory_id}/process?model_size=tiny")
    assert resp.status_code == 200, f"Process endpoint failed: {resp.status_code} - {resp.text}"
    
    data = resp.json()
    print("       Transcription succeeded! (HTTP 200)")
    print(f"       Detected Language   : {data['detected_language']} (Confidence: {data['language_probability']})")
    print(f"       Model Used          : {data['model_used']}")
    print(f"       Duration Processed  : {data['duration_processed']}s")
    print(f"       Segment Count       : {data['segment_count']}")
    print(f"       Status              : {data['status']}")

    # 3. Verify Verbatim Timestamps
    print("\n [3/6] Verifying Timestamps Preservation (First 5 Segments):")
    for s in data["segments"][:5]:
        print(f"       [{s['start_time']:6.2f}s -> {s['end_time']:6.2f}s]: {s['text']}")
    
    assert len(data["segments"]) > 0, "No segments returned!"
    assert all("start_time" in s and "end_time" in s and "text" in s for s in data["segments"])

    # 4. Verify Original Audio Preservation (Bit-for-Bit Integrity)
    print("\n [4/6] Verifying Original Audio Integrity (Read-Only Guarantee):")
    with open(record.audio_path, "rb") as f:
        after_bytes = f.read()
        after_md5 = hashlib.md5(after_bytes).hexdigest()
    assert orig_md5 == after_md5, f"CRITICAL: Audio file was modified! {orig_md5} != {after_md5}"
    assert orig_len == len(after_bytes), "Audio file length changed!"
    print("       Audio Preservation: PASSED (Original audio completely untouched)")

    # 5. Verify Database Persistence in memory_transcripts and transcript_segments
    print("\n [5/6] Verifying Database Persistence in PostgreSQL:")
    db.refresh(record)
    assert record.status == "completed", f"Expected status 'completed', got '{record.status}'"
    print(f"       AudioRecord status: {record.status} (Updated duration: {record.duration}s)")

    # Verify memory_transcripts row
    mt = db.query(MemoryTranscript).filter(MemoryTranscript.memory_id == memory_id).first()
    assert mt is not None, "memory_transcripts row missing!"
    assert mt.full_transcript == data["full_transcript"]
    assert len(mt.segments_json) == data["segment_count"]
    print(f"       memory_transcripts table: PERSISTED (ID: {mt.id}, Segments: {len(mt.segments_json)})")

    # Verify transcript_segments rows
    seg_rows = db.query(TranscriptSegment).filter(TranscriptSegment.memory_id == memory_id).all()
    assert len(seg_rows) == data["segment_count"]
    print(f"       transcript_segments table: PERSISTED ({len(seg_rows)} individual rows)")

    # 6. Verify Retrieval Endpoint GET /api/memories/{memory_id}/transcript
    print("\n [6/6] Verifying GET /api/memories/{memory_id}/transcript:")
    get_resp = client.get(f"/api/memories/{memory_id}/transcript")
    assert get_resp.status_code == 200, f"Transcript GET failed: {get_resp.status_code}"
    get_data = get_resp.json()
    assert get_data["full_transcript"] == data["full_transcript"]
    assert len(get_data["segments"]) == data["segment_count"]
    print("       GET /api/memories/{id}/transcript: VERIFIED (Exact match with stored transcript)")

    db.close()

    print("\n" + "=" * 70)
    print("ALL SPEECH-TO-TEXT CHECKS & TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)

    # Print sample JSON structure for documentation
    sample_json = {
        "memory_id": data["memory_id"],
        "status": data["status"],
        "detected_language": data["detected_language"],
        "language_probability": data["language_probability"],
        "model_used": data["model_used"],
        "duration_processed": data["duration_processed"],
        "segment_count": data["segment_count"],
        "full_transcript": data["full_transcript"][:200] + "...",
        "segments": data["segments"][:3]
    }
    print("\n--- SAMPLE OUTPUT JSON ---")
    print(json.dumps(sample_json, indent=2))

if __name__ == "__main__":
    run_stt_verification()
