import sys
import os
import asyncio
import json

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
from app.services.comparison import comparison_service
from app.models.memory import ExtractedMemory, ThenNowComparison
from fastapi.testclient import TestClient
from app.main import app

def run_tests():
    print("=" * 75)
    print("THEN VS NOW (Signature Feature) VERIFICATION TEST SUITE")
    print("=" * 75)

    db = SessionLocal()
    try:
        # TEST 1: Service Test with real grandfather memory
        print("\n[Test 1] Testing ComparisonService with Real Memory...")
        latest_mem = db.query(ExtractedMemory).order_by(ExtractedMemory.id.asc()).first()
        assert latest_mem is not None, "At least 1 extracted memory must exist in DB"
        print(f">> Selected Memory #{latest_mem.id}: '{latest_mem.title}' (UUID: {latest_mem.memory_id})")

        res_1 = asyncio.run(comparison_service.generate_comparison(db, memory_id=latest_mem.id))

        print("\n>> Generated 'Then vs Now' Data:")
        print(f"   Topic: {res_1.get('topic')}")
        print(f"   Era Described: {res_1.get('era_described')}")
        print(f"\n   --- GRANDPA'S EXPERIENCE (THEN) ---\n   {res_1.get('then_experience')}")
        print(f"\n   --- MODERN CONTEXT (NOW) ---\n   {res_1.get('now_reality')}")
        print(f"\n   --- COMPARISON & ENDURING BRIDGE ---\n   Enduring Value: {res_1.get('enduring_value')}")
        print(f"   Family Reflection: {res_1.get('reflection_question')}")
        print(f"\n   --- SOURCE RECORDING ---\n   Audio ID: {res_1.get('audio_id')}")
        print(f"   Audio Source File: {res_1.get('audio_source')}")
        print(f"   Audio Playback URL: {res_1.get('audio_url')}")
        print(f"   Timestamps: {res_1.get('start_time')}s -> {res_1.get('end_time')}s")
        print(f"   Verbatim Excerpt: '{res_1.get('verbatim_quote')}'")

        # Assertions
        assert len(res_1.get("then_experience", "")) > 10, "'then_experience' must be extracted from his words"
        assert len(res_1.get("now_reality", "")) > 10, "'now_reality' must provide modern context"
        assert res_1.get("source_audio") is not None or res_1.get("audio_url") is not None, "Source audio must be attached"
        assert res_1.get("audio_url", "").startswith("/api/memories/audio/"), "Must have valid audio stream URL"

        print("\n[Test 1 PASSED]: 'THEN' and 'NOW' correctly separated with source audio.")

        # TEST 2: Testing POST /api/compare Endpoint
        print("\n[Test 2] Testing Endpoint: POST /api/compare with memory_id...")
        client = TestClient(app)
        api_res = client.post("/api/compare", json={"memory_id": latest_mem.id})
        print(f">> HTTP Status Code: {api_res.status_code}")
        assert api_res.status_code == 200, f"Expected 200 OK, got {api_res.status_code}: {api_res.text}"

        json_data = api_res.json()
        assert "then_experience" in json_data, "Response missing 'then_experience'"
        assert "now_reality" in json_data, "Response missing 'now_reality'"
        assert "source_audio" in json_data or "audio_url" in json_data, "Response missing source audio info"
        assert json_data["audio_url"] == f"/api/memories/audio/{latest_mem.memory_id}/stream"

        print("[Test 2 PASSED]: POST /api/compare returned valid payload with source audio.")

        # TEST 3: Testing POST /api/compare with semantic query (hybrid retrieval)
        print("\n[Test 3] Testing Endpoint: POST /api/compare with semantic topic query...")
        query_res = client.post("/api/compare", json={"query": "communication and handwritten letters"})
        print(f">> HTTP Status Code: {query_res.status_code}")
        assert query_res.status_code == 200, f"Expected 200 OK, got {query_res.status_code}: {query_res.text}"

        query_data = query_res.json()
        print(f">> Retrieved Topic: '{query_data.get('topic')}'")
        print(f">> Source Audio URL: {query_data.get('audio_url')}")
        print(f">> Timestamps: {query_data.get('start_time')}s - {query_data.get('end_time')}s")
        assert len(query_data.get("then_experience", "")) > 0

        print("[Test 3 PASSED]: Semantic retrieval -> THEN extraction -> NOW contrast -> source audio completed.")

        # TEST 4: Testing GET /api/compare
        print("\n[Test 4] Testing GET /api/compare (List Comparisons)...")
        list_res = client.get("/api/compare")
        assert list_res.status_code == 200
        comp_list = list_res.json()
        print(f">> Total Comparisons in DB: {len(comp_list)}")
        assert len(comp_list) > 0, "Expected at least 1 saved comparison"
        print(f">> Latest Comparison Topic: '{comp_list[0].get('topic')}' with Audio: {comp_list[0].get('audio_url')}")

        print("[Test 4 PASSED]: GET /api/compare lists all saved comparisons with audio playback.")

        print("\n" + "=" * 75)
        print("ALL THEN VS NOW TESTS PASSED SUCCESSFULLY!")
        print("=" * 75)

    finally:
        db.close()

if __name__ == "__main__":
    run_tests()
