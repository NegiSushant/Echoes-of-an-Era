"""
Database Cleanup Script for 'Echoes of an Era'

Cleans all records from PostgreSQL while preserving database tables,
the pgvector extension, and HNSW indexes.

Usage:
  python clean_db.py            # Truncates all database tables
  python clean_db.py --all      # Truncates tables AND clears uploaded audio files
"""

import os
import sys
import argparse
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Ensure backend directory is in sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://echoes:echoes_password@localhost:5432/echoes_of_an_era")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", os.path.join(backend_dir, "uploads", "audio"))

TABLES = [
    "then_now_comparisons",
    "memory_places",
    "memory_people",
    "memory_topics",
    "extracted_memories",
    "transcript_segments",
    "memory_transcripts",
    "audio_records"
]


def clean_database(clean_files: bool = False):
    print("=" * 65)
    print("ECHOES OF AN ERA - DATABASE CLEANUP")
    print("=" * 65)
    print(f"Connecting to: {DATABASE_URL}...\n")

    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        for tbl in TABLES:
            try:
                conn.execute(text(f"TRUNCATE TABLE {tbl} CASCADE;"))
                print(f"  [✓] Truncated table: {tbl}")
            except Exception as e:
                print(f"  [!] Skipped {tbl} ({e})")
        conn.commit()

    if clean_files:
        print(f"\nCleaning uploaded audio files in: {UPLOAD_DIR}...")
        if os.path.exists(UPLOAD_DIR):
            count = 0
            for fname in os.listdir(UPLOAD_DIR):
                fpath = os.path.join(UPLOAD_DIR, fname)
                if os.path.isfile(fpath):
                    try:
                        os.remove(fpath)
                        count += 1
                    except Exception as e:
                        print(f"  [!] Could not delete {fname}: {e}")
            print(f"  [✓] Deleted {count} uploaded audio file(s).")
        else:
            print("  [i] Uploads directory does not exist.")

    print("\n" + "=" * 65)
    print("DATABASE CLEANUP COMPLETED SUCCESSFULLY")
    print("All tables are clean and ready for fresh memory ingestion.")
    print("=" * 65)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean Echoes of an Era database.")
    parser.add_argument("--all", action="store_true", help="Also remove uploaded audio files from disk.")
    args = parser.parse_args()

    clean_database(clean_files=args.all)
