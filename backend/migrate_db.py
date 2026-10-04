import os
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://echoes:echoes_password@localhost:5432/echoes_of_an_era")

def migrate():
    print(f"[Migration] Connecting to database: {DATABASE_URL}...")
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        print("[Migration] Dropping old tables to align with Audio Ingestion schema...")
        conn.execute(text("DROP TABLE IF EXISTS then_now_comparisons CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS extracted_memories CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS memory_transcripts CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS transcript_segments CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS audio_records CASCADE;"))
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.commit()
    
    # Import models and recreate
    from app.db.database import Base
    import app.models.memory
    
    Base.metadata.create_all(bind=engine)
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"[Migration] Successfully created tables: {tables}")
    
    # Verify columns in audio_records
    columns = [col['name'] for col in inspector.get_columns('audio_records')]
    print(f"[Migration] Columns in audio_records: {columns}")

if __name__ == "__main__":
    migrate()
