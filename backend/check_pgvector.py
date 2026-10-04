import os
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

load_dotenv()

engine = create_engine(os.getenv("DATABASE_URL"))

# 1. Ensure pgvector extension
with engine.connect() as conn:
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
    conn.commit()

# 2. Create any missing tables (memory_topics, memory_people, memory_places)
from app.db.database import Base
import app.models.memory

Base.metadata.create_all(bind=engine)

# 3. Create HNSW Vector Index on extracted_memories(embedding)
with engine.connect() as conn:
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_extracted_memories_embedding_hnsw 
        ON extracted_memories 
        USING hnsw (embedding vector_cosine_ops);
    """))
    conn.commit()

# 4. Inspect tables & indexes
inspector = inspect(engine)
tables = inspector.get_table_names()
print("All tables in database:", tables)

with engine.connect() as conn:
    indexes = conn.execute(text("""
        SELECT indexname, indexdef 
        FROM pg_indexes 
        WHERE tablename = 'extracted_memories';
    """)).fetchall()
    print("\nIndexes on extracted_memories:")
    for idx in indexes:
        print(f"  - {idx[0]}: {idx[1]}")
