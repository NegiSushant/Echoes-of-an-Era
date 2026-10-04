"""
Utility script to pre-download BAAI/bge-m3 weights into the local Hugging Face cache.
Once downloaded, the model can run fully offline with EMBEDDING_LOCAL_ONLY=true.
"""
import os
import sys

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from huggingface_hub import hf_hub_download
from sentence_transformers import SentenceTransformer

def download_bge_m3():
    print("=" * 70)
    print("DOWNLOADING BAAI/bge-m3 TO LOCAL HUGGING FACE CACHE")
    print("=" * 70)
    print("[Embeddings] Ensuring pooling configuration is cached...")
    try:
        hf_hub_download(repo_id="BAAI/bge-m3", filename="1_Pooling/config.json")
    except Exception as e:
        print(f"[Embeddings] Note on pooling config: {e}")

    print("[Embeddings] Downloading BAAI/bge-m3 weights (~2.2 GB) via SentenceTransformers...")
    model = SentenceTransformer("BAAI/bge-m3", device="cpu", local_files_only=False)
    dim_fn = getattr(model, "get_embedding_dimension", getattr(model, "get_sentence_embedding_dimension", None))
    dim = dim_fn() if dim_fn else 1024
    assert dim == 1024, f"Dimension mismatch: expected 1024, got {dim}"
    print(f"[Embeddings] BAAI/bge-m3 successfully downloaded and verified in cache.")
    print(f"[Embeddings] Model dimension: {dim}")
    print("=" * 70)

if __name__ == "__main__":
    download_bge_m3()
