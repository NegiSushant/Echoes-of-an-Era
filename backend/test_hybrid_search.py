import os
import json
import uuid
from fastapi.testclient import TestClient
from dotenv import load_dotenv

load_dotenv()

from app.main import app
from app.db.database import SessionLocal
from app.models.memory import (
    AudioRecord, MemoryTranscript, ExtractedMemory,
    MemoryTopic, MemoryPerson, MemoryPlace
)
from app.services.embeddings import embedding_service
from app.services.retrieval import retrieval_service

client = TestClient(app)

def seed_sample_memories(db):
    """Seeds authentic grandfather memories to demonstrate hybrid retrieval accuracy."""
    print(" [1/4] Seeding diverse grandfather memories for retrieval testing...")

    memories_data = [
        {
            "memory_id": "comm-1954-letters",
            "file_name": "grandfather_memories_communication_1954.mp3",
            "title": "Letters, Telegrams, and Waiting for the Postman",
            "time_period": "1950s",
            "location": "Old Town Postal District",
            "people_mentioned": ["Father", "Uncle Ram", "Babu the Postman"],
            "emotions": ["Nostalgic", "Patient", "Warmhearted"],
            "summary": (
                "Grandfather describes how communication worked in his youth during the 1950s. "
                "There were no mobile phones or instant messages. People wrote inland letters and postcards, "
                "waiting two weeks for a reply. For urgent news, they went to the telegraph office to send a telegram. "
                "The arrival of the neighborhood postman on his bicycle was a daily community event."
            ),
            "life_advice": "When words take time to travel, people weigh every syllable with care and love.",
            "tags": ["communication", "letters", "post office", "telegrams", "patience", "1950s"],
            "quotes": [
                {
                    "quote": "In my youth, we had no phones; we wrote blue aerograms and watched the lane for the postman's bicycle bell.",
                    "significance": "Illustrates the tactile, patient nature of mid-century communication."
                },
                {
                    "quote": "A telegram meant something urgent had happened, and our hearts would race until we opened the envelope.",
                    "significance": "Captures the emotional weight of urgent messages in the era."
                }
            ],
            "transcript": (
                "People often ask me, how did we talk to each other without mobile phones or internet? "
                "In the 1950s when I was a young boy, if we wanted to talk to someone in another town, "
                "we took out a fountain pen and a sheet of paper. We wrote letters, carefully folded them into envelopes, "
                "and dropped them in the red pillar postbox down the lane. We waited days, sometimes weeks, for a reply. "
                "And if it was very urgent, someone had to walk to the telegraph office to send a telegram. "
                "When Babu the postman rode down our street ringing his brass bell, the whole family would run to the verandah."
            ),
            "start_time": 12.0,
            "end_time": 195.0
        },
        {
            "memory_id": "happ-edmund-baker",
            "file_name": "grandfather_story_edmund_happiness.mp3",
            "title": "The Secret to True Happiness in Green Meadow",
            "time_period": "Past Era",
            "location": "Green Meadow, Eldoria",
            "people_mentioned": ["Edmund", "Villagers", "Grandfather"],
            "emotions": ["Peaceful", "Inspiring", "Content"],
            "summary": (
                "Grandfather shares the story of Edmund the baker who searched everywhere for the secret to happiness. "
                "He discovered that genuine contentment is not found in gold or grand city titles, but in baking warm "
                "bread and sharing with neighbors who have less."
            ),
            "life_advice": "Happiness is not something you chase; it is the warmth left behind when you share what you have.",
            "tags": ["happiness", "contentment", "sharing", "baking", "gratitude", "village life"],
            "quotes": [
                {
                    "quote": "A story that teaches us the true secret of happiness.",
                    "significance": "Moral foundation of family wisdom."
                }
            ],
            "transcript": (
                "My dear grandchildren, listen carefully to this story of Edmund the baker in Green Meadow. "
                "He spent years feeling unhappy because he thought he needed a grand bakery in the capital. "
                "Only when an old traveler stopped at his bakery did Edmund realize that sharing his bread freely "
                "with the hungry gave him the deep joy that money never could buy."
            ),
            "start_time": 0.0,
            "end_time": 240.0
        },
        {
            "memory_id": "fest-diwali-traditions",
            "file_name": "grandfather_diwali_sweets_tradition.mp3",
            "title": "Making Clay Lamps and Clay Ovens for the Autumn Festival",
            "time_period": "1960s",
            "location": "Ancestral Courtyard",
            "people_mentioned": ["Grandmother", "Elder Sister", "Neighbors"],
            "emotions": ["Festive", "Joyful", "Cohesive"],
            "summary": (
                "Memories of preparing for the festival of lights in the ancestral courtyard. "
                "Grandmother and the children molded small clay diyas by hand and roasted puffed rice and jaggery sweets. "
                "The entire neighborhood shared a single outdoor wood fire."
            ),
            "life_advice": "Traditions survive not through stone monuments, but through recipes passed from hand to hand.",
            "tags": ["festival", "diwali", "traditions", "family cooking", "sweets", "courtyard"],
            "quotes": [
                {
                    "quote": "We would sit around the courtyard until midnight rolling sweet ladoos by lantern light.",
                    "significance": "Evokes childhood sensory memories of celebration."
                }
            ],
            "transcript": (
                "Every autumn, weeks before the festival, our courtyard smelled of cardamom and ghee. "
                "My mother and sister would bring clay from the riverside to shape diyas. "
                "No one bought plastic decorations back then; everything was crafted by hand."
            ),
            "start_time": 5.5,
            "end_time": 180.0
        }
    ]

    for m in memories_data:
        # Check or create AudioRecord
        audio = db.query(AudioRecord).filter(AudioRecord.memory_id == m["memory_id"]).first()
        if not audio:
            audio = AudioRecord(
                memory_id=m["memory_id"],
                file_name=m["file_name"],
                audio_path=f"F:/practice/eco/backend/uploads/audio/{m['file_name']}",
                duration=m["end_time"],
                file_size_bytes=2048500,
                status="completed"
            )
            db.add(audio)
            db.commit()

        # Check or create MemoryTranscript
        tr = db.query(MemoryTranscript).filter(MemoryTranscript.memory_id == m["memory_id"]).first()
        if not tr:
            tr = MemoryTranscript(
                memory_id=m["memory_id"],
                full_transcript=m["transcript"],
                segments_json=[
                    {"segment_index": 0, "start_time": m["start_time"], "end_time": m["end_time"], "text": m["transcript"]}
                ],
                detected_language="en",
                language_probability=0.99,
                model_used="large-v3",
                duration_processed=12.5
            )
            db.add(tr)
            db.commit()

        # Embed composite text: TITLE + SUMMARY + TOPICS + TRANSCRIPT
        emb = embedding_service.embed_memory(
            title=m["title"],
            summary=m["summary"],
            topics=m["tags"],
            transcript=m["transcript"]
        )

        # Check or create ExtractedMemory
        mem = db.query(ExtractedMemory).filter(ExtractedMemory.memory_id == m["memory_id"]).first()
        if not mem:
            mem = ExtractedMemory(
                memory_id=m["memory_id"],
                title=m["title"],
                summary=m["summary"],
                time_period=m["time_period"],
                location=m["location"],
                people_mentioned=m["people_mentioned"],
                emotions=m["emotions"],
                verbatim_quotes=m["quotes"],
                life_advice=m["life_advice"],
                tags=m["tags"],
                embedding=emb,
                start_time=m["start_time"],
                end_time=m["end_time"]
            )
            db.add(mem)
            db.commit()
            db.refresh(mem)

            # Populate supporting tables
            for t in m["tags"]:
                db.add(MemoryTopic(memory_id=mem.id, topic=t))
            for p in m["people_mentioned"]:
                db.add(MemoryPerson(memory_id=mem.id, name=p))
            if m["location"]:
                db.add(MemoryPlace(memory_id=mem.id, place_name=m["location"]))
            db.commit()

    print(f"       Seeded {len(memories_data)} comprehensive memories successfully.")


def run_hybrid_search_tests():
    print("=" * 70)
    print("SEMANTIC + HYBRID RETRIEVAL TEST SUITE")
    print("=" * 70)

    db = SessionLocal()
    seed_sample_memories(db)

    # -------------------------------------------------------------
    # TEST 1: DELIVERABLE TEST QUESTION
    # "How did Grandpa communicate when he was young?"
    # -------------------------------------------------------------
    print("\n [2/4] Testing Primary Deliverable Question:")
    q1 = "How did Grandpa communicate when he was young?"
    print(f"       Natural Language Query: \"{q1}\"")

    resp1 = client.post("/api/search", json={"query": q1, "limit": 3})
    assert resp1.status_code == 200, f"Search failed: {resp1.text}"
    data1 = resp1.json()

    print(f"       Total Results Returned: {len(data1['results'])}")
    assert len(data1["results"]) > 0, "No results returned for deliverable question!"

    top_result = data1["results"][0]
    print(f"\n       [TOP MATCH #1]:")
    print(f"          - memory_id       : {top_result['memory_id']}")
    print(f"          - title           : {top_result['title']}")
    print(f"          - similarity_score: {top_result['similarity_score']}")
    print(f"          - match_type      : {top_result['search_match_type']}")
    print(f"          - audio_source    : {top_result['audio_source']}")
    print(f"          - timestamps      : {top_result['relevant_timestamps']}")
    print(f"          - relevant_quote  : \"{top_result['relevant_quote']}\"")
    print(f"          - summary snippet : {top_result['summary'][:110]}...")

    # Verification of deliverable requirement:
    # Must retrieve the communication memory as top match
    assert "comm-1954-letters" in top_result["memory_id"], (
        f"Deliverable Failed! Expected communication memory, got '{top_result['title']}'"
    )
    print("       --> DELIVERABLE VERIFIED: Query about communication retrieved letters/post office memory!")

    # -------------------------------------------------------------
    # TEST 2: SECONDARY TEST QUESTION (Life Advice & Contentment)
    # "What was the secret to true happiness and joy?"
    # -------------------------------------------------------------
    print("\n [3/4] Testing Conceptual / Semantic Query:")
    q2 = "What was the secret to true happiness and contentment?"
    print(f"       Natural Language Query: \"{q2}\"")

    resp2 = client.post("/api/search", json={"query": q2, "limit": 3})
    assert resp2.status_code == 200
    data2 = resp2.json()

    top2 = data2["results"][0]
    print(f"       [TOP MATCH #1]: '{top2['title']}' (Score: {top2['similarity_score']})")
    assert "happ-edmund" in top2["memory_id"] or "happiness" in top2["title"].lower(), (
        f"Expected happiness memory, got '{top2['title']}'"
    )
    print("       --> SEMANTIC MATCH VERIFIED: Happiness query retrieved Edmund the baker story!")

    # -------------------------------------------------------------
    # TEST 3: KEYWORD / LEXICAL MATCH QUERY
    # "Edmund baker Eldoria"
    # -------------------------------------------------------------
    print("\n [4/4] Testing Exact Keyword & Lexical Match:")
    q3 = "Edmund baker Eldoria"
    resp3 = client.post("/api/search", json={"query": q3, "limit": 2})
    assert resp3.status_code == 200
    data3 = resp3.json()
    top3 = data3["results"][0]
    print(f"       [TOP MATCH #1]: '{top3['title']}' (Match Type: {top3['search_match_type']}, Score: {top3['similarity_score']})")
    assert "Edmund" in top3["summary"] or "baker" in top3["summary"].lower()

    db.close()

    print("\n" + "=" * 70)
    print("ALL HYBRID RETRIEVAL TESTS COMPLETED WITH 100% SUCCESS!")
    print("=" * 70)

    # Output Sample JSON for the primary deliverable
    print("\n--- SAMPLE OUTPUT JSON (POST /api/search) ---")
    print(json.dumps(data1, indent=2))

if __name__ == "__main__":
    run_hybrid_search_tests()
