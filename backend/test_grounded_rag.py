import sys
import os
import asyncio
import json

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
from app.services.rag import rag_service
from app.api.ask import router
from fastapi.testclient import TestClient
from app.main import app

def run_tests():
    print("=" * 70)
    print("GROUNDED RAG (Ask Grandpa) VERIFICATION TEST SUITE")
    print("=" * 70)

    db = SessionLocal()
    try:
        # TEST 1: Grounded Deliverable Query
        query_1 = "How did Grandpa communicate when he was young?"
        print(f"\n[Test 1] Positive Query: '{query_1}'")
        res_1 = asyncio.run(rag_service.answer_question(db, query_1))

        print(f"\n>> Grounded Status: {res_1.get('grounded')}")
        print(f">> Gemma 3 Generated Answer:\n{res_1.get('answer')}\n")

        sources = res_1.get("sources", [])
        print(f">> Sources Count: {len(sources)}")
        assert len(sources) > 0, "Expected at least 1 source memory for grounded query"

        top_source = sources[0]
        print(">> Top Source Details:")
        print(f"   - Memory ID: {top_source.get('memory_id')}")
        print(f"   - Title: {top_source.get('title')}")
        print(f"   - Audio Source: {top_source.get('audio_source')}")
        print(f"   - Audio Playback URL: {top_source.get('audio_url')}")
        print(f"   - Start Time: {top_source.get('start_time')}s")
        print(f"   - End Time: {top_source.get('end_time')}s")
        print(f"   - Verbatim Quote: '{top_source.get('verbatim_quote')}'")
        print(f"   - Similarity Score: {top_source.get('similarity_score')}")

        assert "letter" in top_source.get("title", "").lower() or "postman" in top_source.get("title", "").lower() or "letters" in res_1.get("answer", "").lower(), \
            "Top source should be related to letters / communication"
        assert top_source.get("audio_url", "").startswith("/api/memories/audio/"), "Should provide stream URL"

        print("\n[Test 1 PASSED]: Real grandfather memory retrieved and grounded answer generated.")

        # TEST 2: Zero-Hallucination Negative Query
        query_2 = "What did Grandpa think about cryptocurrency, Bitcoin, and artificial intelligence in 2024?"
        print(f"\n[Test 2] Ungrounded / Out-of-Archive Query: '{query_2}'")
        res_2 = asyncio.run(rag_service.answer_question(db, query_2))

        print(f">> Answer:\n{res_2.get('answer')}")
        print(f">> Sources Count: {len(res_2.get('sources', []))}")

        answer_lower = res_2.get("answer", "").lower()
        has_guardrail = (
            "not spoken" in answer_lower or
            "not mentioned" in answer_lower or
            "no mention" in answer_lower or
            len(res_2.get("sources", [])) == 0
        )
        assert has_guardrail, "Zero-hallucination rule violated: AI should state Grandpa has not spoken about this"
        print("\n[Test 2 PASSED]: Zero-hallucination guardrail preserved. System refused to invent memories.")

        # TEST 3: API Endpoint Test via TestClient (POST /api/ask)
        print("\n[Test 3] Testing HTTP API Endpoint: POST /api/ask")
        client = TestClient(app)
        api_res = client.post("/api/ask", json={"question": "How did Grandpa communicate when he was young?"})
        print(f">> HTTP Status Code: {api_res.status_code}")
        assert api_res.status_code == 200, f"Expected 200 OK, got {api_res.status_code}: {api_res.text}"

        json_data = api_res.json()
        assert "answer" in json_data, "Response missing 'answer' field"
        assert "sources" in json_data, "Response missing 'sources' field"
        assert "citations" in json_data, "Response missing 'citations' field"
        assert len(json_data["sources"]) > 0, "Response should have populated sources"

        first_s = json_data["sources"][0]
        print(f">> API Returned Answer Snippet: {json_data['answer'][:120]}...")
        print(f">> API Source Audio URL: {first_s['audio_url']}")
        print(f">> API Timestamps: {first_s['start_time']}s -> {first_s['end_time']}s")
        print("\n[Test 3 PASSED]: POST /api/ask returned expected schema with audio playback capability.")

        print("\n" + "=" * 70)
        print("ALL TESTS PASSED SUCCESSFULLY!")
        print("=" * 70)

    finally:
        db.close()

if __name__ == "__main__":
    run_tests()
