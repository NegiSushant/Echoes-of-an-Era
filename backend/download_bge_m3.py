"""
Utility script to pre-download BAAI/bge-m3 weights into the local Hugging Face cache.
Once downloaded, the model can run fully offline with EMBEDDING_LOCAL_ONLY=true.
"""
import os
import sys

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from sentence_transformers import SentenceTransformer

def download_bge_m3():
    print("=" * 70)
    print("DOWNLOADING BAAI/bge-m3 TO LOCAL HUGGING FACE CACHE")
    print("=" * 70)
    print("[Embeddings] Downloading BAAI/bge-m3 weights (~2.2 GB) via SentenceTransformers...")
    model = SentenceTransformer("BAAI/bge-m3", device="cpu", local_files_only=False)
    dim = model.get_sentence_embedding_dimension()
    assert dim == 1024, f"Dimension mismatch: expected 1024, got {dim}"
    print(f"[Embeddings] BAAI/bge-m3 successfully downloaded and verified in cache.")
    print(f"[Embeddings] Model dimension: {dim}")
    print("=" * 70)

if __name__ == "__main__":
    download_bge_m3()
