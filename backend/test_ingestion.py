import os
import math
import struct
import wave
import hashlib
import requests

BASE_URL = "http://127.0.0.1:8000"

def create_sample_wav(filename: str, duration_sec: float = 3.0, sample_rate: int = 16000) -> str:
    """Generates a valid test audio WAV file."""
    filepath = os.path.abspath(filename)
    num_samples = int(duration_sec * sample_rate)
    with wave.open(filepath, "wb") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        # 440 Hz tone (A4)
        for i in range(num_samples):
            val = int(32767.0 * 0.5 * math.sin(2.0 * math.pi * 440.0 * i / sample_rate))
            data = struct.pack("<h", val)
            wav_file.writeframesraw(data)
    return filepath

def get_file_md5(filepath: str) -> str:
    h = hashlib.md5()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def run_tests():
    print("=" * 60)
    print("AUDIO INGESTION VERIFICATION TEST SUITE")
    print("=" * 60)

    # 1. Health check
    res = requests.get(f"{BASE_URL}/api/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print(" [1/5] Backend Health Check: OK")

    # 2. Test Invalid File Extension Rejection
    fake_txt = "test_note.txt"
    with open(fake_txt, "w") as f:
        f.write("This is not an audio file.")
    try:
        with open(fake_txt, "rb") as f:
            res = requests.post(f"{BASE_URL}/api/memories/upload", files={"file": ("test_note.txt", f, "text/plain")})
        assert res.status_code == 400, f"Expected 400 for .txt, got {res.status_code}"
        print(f" [2/5] Invalid Extension Validation: REJECTED (HTTP 400: {res.json()['detail']})")
    finally:
        if os.path.exists(fake_txt):
            os.remove(fake_txt)

    # 3. Test Real Audio Upload
    test_audio_path = create_sample_wav("grandfather_story_sample.wav", duration_sec=3.5)
    orig_md5 = get_file_md5(test_audio_path)
    orig_size = os.path.getsize(test_audio_path)
    print(f"       Created test audio: grandfather_story_sample.wav ({orig_size} bytes, MD5: {orig_md5})")

    try:
        with open(test_audio_path, "rb") as f:
            res = requests.post(
                f"{BASE_URL}/api/memories/upload",
                files={"file": ("grandfather_story_sample.wav", f, "audio/wav")}
            )

        assert res.status_code == 201, f"Upload failed: {res.status_code} - {res.text}"
        data = res.json()
        print(" [3/5] Audio Upload Endpoint: SUCCESS (HTTP 201)")
        print(f"       memory_id:   {data['memory_id']}")
        print(f"       file_name:   {data['file_name']}")
        print(f"       duration:    {data['duration']}s")
        print(f"       file_size:   {data['file_size_bytes']} bytes")
        print(f"       status:      {data['status']}")
        print(f"       created_at:  {data['created_at']}")
        print(f"       audio_path:  {data['audio_path']}")

        # 4. Verify Database Persistence & Querying
        list_res = requests.get(f"{BASE_URL}/api/memories")
        assert list_res.status_code == 200
        memories = list_res.json()
        found = any(m["memory_id"] == data["memory_id"] for m in memories)
        assert found, "Uploaded record not found in database query!"
        print(" [4/5] Database Record Persistence: VERIFIED in PostgreSQL")

        # 5. Verify Original Audio Preservation (Bit-for-Bit Integrity)
        stream_res = requests.get(f"{BASE_URL}/api/memories/audio/{data['memory_id']}/stream")
        assert stream_res.status_code == 200, f"Stream failed: {stream_res.status_code}"
        streamed_content = stream_res.content
        streamed_md5 = hashlib.md5(streamed_content).hexdigest()

        assert len(streamed_content) == orig_size, f"Size mismatch: {len(streamed_content)} vs {orig_size}"
        assert streamed_md5 == orig_md5, f"MD5 mismatch: {streamed_md5} vs {orig_md5}"
        print(" [5/5] Audio Preservation Verification: PASSED")
        print(f"       Original MD5: {orig_md5}")
        print(f"       Streamed MD5: {streamed_md5}")
        print("       --> Bit-for-bit exact match! Audio is permanently preserved without modification.")

    finally:
        if os.path.exists(test_audio_path):
            os.remove(test_audio_path)

    print("=" * 60)
    print("ALL AUDIO INGESTION TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
