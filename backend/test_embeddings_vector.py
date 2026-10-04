import os
import json
import numpy as np
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from fastapi.testclient import TestClient

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

def run_embeddings_verification():
    print("=" * 70)
    print("EMBEDDINGS & VECTOR STORAGE VERIFICATION SUITE")
    print("=" * 70)

    db = SessionLocal()

    # 1. Verify pgvector extension
    print("\n [1/6] Verifying pgvector Extension in PostgreSQL:")
    ext = db.execute(text("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';")).fetchall()
    assert len(ext) > 0, "pgvector extension is NOT installed!"
    print(f"       Extension Name   : {ext[0][0]}")
    print(f"       Extension Version: {ext[0][1]}")

    # 2. Verify HNSW Vector Index on extracted_memories
    print("\n [2/6] Verifying HNSW Vector Index:")
    indexes = db.execute(text("""
        SELECT indexname, indexdef 
        FROM pg_indexes 
        WHERE tablename = 'extracted_memories' 
          AND indexname = 'idx_extracted_memories_embedding_hnsw';
    """)).fetchall()
    assert len(indexes) > 0, "idx_extracted_memories_embedding_hnsw index NOT found!"
    print(f"       Index Name: {indexes[0][0]}")
    print(f"       Index Def : {indexes[0][1]}")

    # 3. Verify Supporting Tables (topics, people, places)
    print("\n [3/6] Verifying Supporting Tables in PostgreSQL:")
    tables_to_check = ["memory_topics", "memory_people", "memory_places"]
    for tbl in tables_to_check:
        cols = db.execute(text(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{tbl}';
        """)).fetchall()
        assert len(cols) > 0, f"Table '{tbl}' does not exist!"
        col_summary = ", ".join(f"{c[0]} ({c[1]})" for c in cols)
        print(f"       Table '{tbl}': OK -> Columns: {col_summary}")

    # 4. Generate 1024-dim Embedding from TITLE + SUMMARY + TOPICS + TRANSCRIPT
    print("\n [4/6] Generating 1024-dim Embedding with BGE-M3:")
    title = "The Secret to True Happiness in Green Meadow"
    summary = (
        "Grandfather recounts the tale of Edmund the baker in the village of Green Meadow. "
        "Despite his baking success, Edmund learned that true happiness comes from sharing "
        "and simple gratitude rather than chasing grand titles in the capital."
    )
    topics = ["happiness", "contentment", "baking", "gratitude", "village life"]
    transcript = (
        "My dear grandchildren, I have a wonderful story to share with you. "
        "A story that teaches us the true secret of happiness. "
        "Once upon a time in the kingdom of Eldoria, in the village of Green Meadow, "
        "lived young baker Edmund. He learned that sharing fresh bread with his neighbors "
        "filled his heart with more joy than gold ever could."
    )

    composite_text = embedding_service.compose_embedding_text(
        title=title,
        summary=summary,
        topics=topics,
        transcript=transcript
    )
    print("       Composite Text Formatted:")
    for line in composite_text.split("\n"):
        print(f"         | {line[:80]}{'...' if len(line) > 80 else ''}")

    embedding = embedding_service.embed_memory(
        title=title,
        summary=summary,
        topics=topics,
        transcript=transcript
    )

    print(f"       Embedding Vector Dimension: {len(embedding)}")
    assert len(embedding) == 1024, f"Expected 1024 dimensions, got {len(embedding)}"

    # Check normalization: L2 norm should be ~1.0
    l2_norm = float(np.linalg.norm(np.array(embedding)))
    print(f"       Vector L2 Norm            : {l2_norm:.6f} (Normalized for Cosine Similarity)")
    assert abs(l2_norm - 1.0) < 1e-3, f"Vector is not normalized! Norm: {l2_norm}"

    # 5. Store in PostgreSQL + pgvector
    print("\n [5/6] Storing Memory with 1024-dim Embedding in Database:")
    memory_id = "b736fd2c-6e1e-4d2b-a0b4-b6263ca55418"

    # Clean existing
    existing = db.query(ExtractedMemory).filter(ExtractedMemory.memory_id == memory_id).all()
    for em in existing:
        db.query(MemoryTopic).filter(MemoryTopic.memory_id == em.id).delete()
        db.query(MemoryPerson).filter(MemoryPerson.memory_id == em.id).delete()
        db.query(MemoryPlace).filter(MemoryPlace.memory_id == em.id).delete()
        db.delete(em)
    db.commit()

    memory_record = ExtractedMemory(
        memory_id=memory_id,
        title=title,
        summary=summary,
        time_period="Past Era",
        location="Green Meadow, Eldoria",
        people_mentioned=["Edmund", "Grandfather", "Villagers"],
        emotions=["Nostalgic", "Inspiring", "Peaceful"],
        verbatim_quotes=[
            {
                "quote": "A story that teaches us the true secret of happiness.",
                "significance": "Core moral lesson of the recording"
            }
        ],
        life_advice="Happiness is not found in grand ambitions, but in gratitude and sharing.",
        tags=topics,
        embedding=embedding,
        start_time=0.0,
        end_time=306.19
    )
    db.add(memory_record)
    db.commit()
    db.refresh(memory_record)

    # Populate supporting tables
    for top in topics:
        db.add(MemoryTopic(memory_id=memory_record.id, topic=top))
    for p in ["Edmund", "Villagers"]:
        db.add(MemoryPerson(memory_id=memory_record.id, name=p, relationship_to_narrator="Story Characters"))
    db.add(MemoryPlace(memory_id=memory_record.id, place_name="Green Meadow"))
    db.commit()

    print(f"       ExtractedMemory ID: {memory_record.id} stored successfully.")
    print(f"       Topics stored     : {db.query(MemoryTopic).filter_by(memory_id=memory_record.id).count()}")
    print(f"       People stored     : {db.query(MemoryPerson).filter_by(memory_id=memory_record.id).count()}")
    print(f"       Places stored     : {db.query(MemoryPlace).filter_by(memory_id=memory_record.id).count()}")

    # 6. Query by Similarity
    print("\n [6/6] Demonstrating Similarity Search Queries:")

    # Method A: Direct SQL Query using pgvector cosine distance operator <=>
    print("\n       --- METHOD A: Direct SQL query via pgvector operator (<=>) ---")
    query_text = "What is the secret to true happiness and contentment in life?"
    query_vec = embedding_service.embed_text(query_text)

    # Format vector as string for PostgreSQL literal
    vec_str = "[" + ",".join(str(x) for x in query_vec) + "]"

    sql = text("""
        SELECT 
            id,
            title,
            1 - (embedding <=> CAST(:vec AS vector)) AS cosine_similarity,
            (embedding <=> CAST(:vec AS vector)) AS cosine_distance
        FROM extracted_memories
        ORDER BY embedding <=> CAST(:vec AS vector)
        LIMIT 3;
    """)

    sql_results = db.execute(sql, {"vec": vec_str}).fetchall()
    for row in sql_results:
        print(f"       SQL Match: ID {row[0]} | Title: '{row[1]}'")
        print(f"                  Cosine Similarity = {row[2]:.4f} | Cosine Distance = {row[3]:.4f}")

    # Method B: Via RetrievalService Python / FastAPI Search Endpoint
    print("\n       --- METHOD B: REST API Query (POST /api/search) ---")
    search_payload = {
        "query": "baker sharing bread with neighbors for contentment",
        "limit": 3,
        "threshold": 0.1
    }
    resp = client.post("/api/search", json=search_payload)
    assert resp.status_code == 200, f"Search failed: {resp.text}"
    search_data = resp.json()

    print(f"       Search Query     : '{search_data['query']}'")
    print(f"       Total Results    : {len(search_data['results'])}")
    for item in search_data["results"]:
        print(f"       -> Match Title   : {item['memory']['title']}")
        print(f"          Similarity    : {item['similarity_score']}")
        print(f"          Quote Citation: \"{item['relevant_quote']}\"")
        print(f"          Summary       : {item['memory']['summary'][:100]}...")

    # Method C: Hybrid Query with Supporting Table (Topic Filter)
    print("\n       --- METHOD C: Hybrid Vector + Topic Filter Search ---")
    hybrid_results = retrieval_service.search_memories(
        db=db,
        query="peace and joy",
        topic="happiness",
        limit=2
    )
    print(f"       Hybrid Results count: {len(hybrid_results)}")
    for mem, sim in hybrid_results:
        print(f"       -> Matched Memory: '{mem.title}' (Similarity: {sim:.4f})")

    db.close()

    print("\n" + "=" * 70)
    print("ALL EMBEDDING & VECTOR STORAGE CHECKS PASSED SUCCESSFULLY!")
    print("=" * 70)

    # Show sample output JSON
    sample_json = {
        "query": search_payload["query"],
        "results": search_data["results"]
    }
    print("\n--- SAMPLE SEARCH RESPONSE JSON ---")
    print(json.dumps(sample_json, indent=2))

if __name__ == "__main__":
    run_embeddings_verification()
