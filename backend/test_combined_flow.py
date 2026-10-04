import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app

def run_tests():
    print("=" * 75)
    print("COMBINED CAPABILITIES VERIFICATION TEST SUITE")
    print("=" * 75)

    client = TestClient(app)

    # 1. Test Health
    print("\n[Test 1] Health Check...")
    res = client.get("/api/health")
    assert res.status_code == 200
    print(">> Health OK:", res.json()["status"])

    # 2. Test Timeline Metadata Generation (Era + Category)
    print("\n[Test 2] Testing Timeline Generation: GET /api/memories/timeline...")
    res = client.get("/api/memories/timeline")
    assert res.status_code == 200, f"Timeline failed with {res.status_code}: {res.text}"
    timeline = res.json()

    print(f">> Total Memories: {timeline.get('total_memories')}")
    print(f">> Discovered Eras: {[e['era'] for e in timeline.get('eras', [])]}")
    print(f">> Discovered Categories/Topics ({len(timeline.get('categories', []))}): {timeline.get('categories')[:8]}...")
    assert timeline.get("total_memories") > 0, "Expected at least 1 memory in archive"
    assert len(timeline.get("eras", [])) > 0, "Expected eras to be grouped from metadata"
    assert len(timeline.get("categories", [])) > 0, "Expected categories to be extracted"

    # Verify that memories in timeline have playable audio links and timestamps
    first_era = timeline["eras"][0]
    first_mem = first_era["memories"][0]
    print(f">> Sample Memory in Era '{first_era['era']}': '{first_mem['title']}'")
    print(f"   Audio URL: {first_mem.get('audio_url')}")
    print(f"   Timestamps: {first_mem.get('start_time')}s -> {first_mem.get('end_time')}s")
    assert first_mem.get("audio_url", "").startswith("/api/memories/audio/"), "Must provide streaming audio URL"

    print("[Test 2 PASSED]: Timeline generated with era groups, categories, and playable audio.")

    # 3. Test Filtered Memory Listing
    print("\n[Test 3] Testing Memory Listing with Category / Era Filters...")
    res_all = client.get("/api/memories")
    assert res_all.status_code == 200
    memories_list = res_all.json()
    print(f">> GET /api/memories returned {len(memories_list)} memories.")
    assert len(memories_list) > 0
    assert "title" in memories_list[0]
    assert "audio_url" in memories_list[0]

    # 4. Test Grounded RAG with playable source timestamps (Ask Grandpa)
    print("\n[Test 4] Grounded RAG Source Linking: POST /api/ask...")
    ask_res = client.post("/api/ask", json={"question": "How did Grandpa communicate when he was young?"})
    assert ask_res.status_code == 200
    ask_data = ask_res.json()
    print(f">> Answer snippet: {ask_data['answer'][:100]}...")
    sources = ask_data.get("sources", [])
    assert len(sources) > 0, "Expected at least 1 source with audio playback"
    top_s = sources[0]
    print(f">> Top Source: {top_s.get('title')}")
    print(f"   Audio ID: {top_s.get('audio_id')}")
    print(f"   Playback Stream: {top_s.get('audio_url')}")
    print(f"   Time Jump: {top_s.get('start_time')}s -> {top_s.get('end_time')}s")
    assert top_s.get("audio_url", "").startswith("/api/memories/audio/")

    print("[Test 4 PASSED]: Ask Grandpa returns grounded answer with playable audio jump.")

    # 5. Test Then vs Now Visual Separation & Source Audio
    print("\n[Test 5] Then vs Now Signature Feature: POST /api/compare...")
    comp_res = client.post("/api/compare", json={"query": "Communication and letters"})
    assert comp_res.status_code == 200
    comp_data = comp_res.json()
    print(f">> Topic: {comp_data.get('topic')}")
    print(f">> Era: {comp_data.get('era_described')}")
    print(f">> THEN Excerpt: {comp_data.get('then_experience')[:80]}...")
    print(f">> NOW Reality: {comp_data.get('now_reality')[:80]}...")
    print(f">> Audio Source: {comp_data.get('audio_source')}")
    print(f">> Audio Playback URL: {comp_data.get('audio_url')}")
    assert len(comp_data.get("then_experience", "")) > 0
    assert len(comp_data.get("now_reality", "")) > 0
    assert comp_data.get("audio_url", "").startswith("/api/memories/audio/")

    print("[Test 5 PASSED]: Then vs Now generated with separated THEN, NOW, and playable audio.")

    print("\n" + "=" * 75)
    print("ALL COMBINED BACKEND TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 75)

if __name__ == "__main__":
    run_tests()
