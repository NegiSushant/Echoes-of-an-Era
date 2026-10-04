import os
from typing import List, Any, Dict
import numpy as np

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

class EmbeddingService:
    """
    Embedding service using BAAI/bge-m3 to generate 1024-dimensional normalized dense vectors.
    Encodes composite representation: TITLE + SUMMARY + TOPICS + TRANSCRIPT.
    Uses SentenceTransformers with local Hugging Face cache or fails loudly.
    No padding, truncation, or silent fallback to lower-dimensional models.
    """

    def __init__(self, model_name: str = None, device: str = None, local_only: bool = None):
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-m3")
        self.device = device or os.getenv("DEVICE", "cpu")
        self.target_dim = 1024
        self._model = None
        self._source = None
        self._local_only_override = local_only

    @property
    def local_only(self) -> bool:
        if self._local_only_override is not None:
            return self._local_only_override
        val = os.getenv("EMBEDDING_LOCAL_ONLY", "true").strip().lower()
        return val in ("true", "1", "yes")

    def _get_model(self):
        """
        Loads the embedding model locally from the Hugging Face cache.
        Enforces local-only execution: no network downloading during API requests.
        Asserts that sentence embedding dimension is exactly target_dim (1024).
        Logs model, device, dimension, and source.
        """
        if self._model is not None:
            return self._model

        from sentence_transformers import SentenceTransformer

        model = None
        source = None

        # Attempt loading from local cache (strict local execution, no downloading during requests)
        try:
            print(f"[Embeddings] Loading '{self.model_name}' locally from Hugging Face cache...")
            model = SentenceTransformer(self.model_name, device=self.device, local_files_only=True)
            source = "local Hugging Face cache"
        except Exception as local_err:
            error_msg = (
                f"\n{'=' * 70}\n"
                f"[Embeddings Error] Failed to load model '{self.model_name}' from local cache.\n"
                f"Underlying Error: {local_err}\n"
                f"Explanation: BAAI/bge-m3 must run locally, but required weights or config files\n"
                f"are not present in your local Hugging Face cache.\n"
                f"Downloading during API requests is disabled to prevent request stalls.\n"
                f"To fix this, pre-download the model offline using:\n"
                f"  python backend/download_bge_m3.py\n"
                f"{'=' * 70}\n"
            )
            print(error_msg)
            raise RuntimeError(error_msg) from local_err

        # Step 3: Verify dimension at runtime
        dim_fn = getattr(model, "get_embedding_dimension", getattr(model, "get_sentence_embedding_dimension", None))
        dim = dim_fn() if dim_fn else 1024
        if dim != self.target_dim:
            raise ValueError(
                f"[Embeddings Error] Model dimension mismatch for '{self.model_name}': "
                f"expected {self.target_dim}, but got {dim}. "
                f"Padding or truncating vectors is strictly disallowed."
            )

        # Step 4: Clear startup/runtime logging
        print(f"[Embeddings] Model: {self.model_name}")
        print(f"[Embeddings] Device: {self.device}")
        print(f"[Embeddings] Dimension: {dim}")
        print(f"[Embeddings] Source: {source}")

        self._model = model
        self._source = source
        return self._model

    def get_model_info(self) -> Dict[str, Any]:
        """
        Returns runtime model metadata.
        Guarantees exact schema and values expected by health checks.
        """
        model = self._get_model()
        dim_fn = getattr(model, "get_embedding_dimension", getattr(model, "get_sentence_embedding_dimension", None))
        dim = dim_fn() if dim_fn else 1024
        return {
            "model_name": self.model_name,
            "device": str(self.device),
            "dimension": dim,
            "normalized": True,
            "local": True
        }

    def test_embedding(
        self,
        sample_text: str = "Grandfather remembers using letters to communicate with family."
    ) -> Dict[str, Any]:
        """
        Runs an embedding verification test on reference memory phrase:
          - vector length == 1024
          - vector contains finite values
          - vector is normalized (L2 norm ≈ 1.0)
          - no NaN values
          - no infinite values
        """
        vec = self.embed_text(sample_text)
        vec_arr = np.array(vec, dtype=np.float32)

        # 1. Dimension check
        if len(vec) != self.target_dim:
            raise AssertionError(f"Expected vector length {self.target_dim}, got {len(vec)}")

        # 2. Finite / NaN / Inf checks
        if np.isnan(vec_arr).any():
            raise AssertionError("Embedding vector contains NaN values")

        if np.isinf(vec_arr).any():
            raise AssertionError("Embedding vector contains infinite values")

        if not np.isfinite(vec_arr).all():
            raise AssertionError("Embedding vector contains non-finite values")

        # 3. L2 Normalization check
        l2_norm = float(np.linalg.norm(vec_arr))
        if abs(l2_norm - 1.0) > 1e-3:
            raise AssertionError(f"Vector is not normalized! L2 norm: {l2_norm}")

        return {
            "status": "passed",
            "sample_text": sample_text,
            "dimension": len(vec),
            "l2_norm": round(l2_norm, 6),
            "finite": True,
            "has_nan": False,
            "has_inf": False,
            "normalized": True
        }

    @staticmethod
    def compose_embedding_text(title: str, summary: str, topics: Any, transcript: str) -> str:
        """
        Creates composite representation from:
        TITLE + SUMMARY + TOPICS + TRANSCRIPT
        """
        if isinstance(topics, list):
            topics_str = ", ".join(str(t) for t in topics if t)
        else:
            topics_str = str(topics or "").strip()

        parts = []
        if title:
            parts.append(f"Title: {title.strip()}")
        if summary:
            parts.append(f"Summary: {summary.strip()}")
        if topics_str:
            parts.append(f"Topics: {topics_str.strip()}")
        if transcript:
            parts.append(f"Transcript: {transcript.strip()}")

        return "\n".join(parts)

    def embed_text(self, text: str) -> List[float]:
        """Generates a normalized 1024-dim dense embedding for a single text."""
        if not text:
            text = ""
        model = self._get_model()
        vec = model.encode(text, normalize_embeddings=True)
        vec_arr = np.array(vec, dtype=np.float32)

        if len(vec_arr) != self.target_dim:
            raise ValueError(
                f"[Embeddings Error] Expected {self.target_dim} dimensions from {self.model_name}, got {len(vec_arr)}"
            )

        return vec_arr.tolist()

    def embed_batch(self, texts: List[str], batch_size: int = 16) -> List[List[float]]:
        """Generates normalized 1024-dim embeddings for a batch of texts."""
        if not texts:
            return []
        model = self._get_model()
        vectors = model.encode(texts, normalize_embeddings=True, batch_size=batch_size)
        results = []
        for idx, v in enumerate(vectors):
            vec_arr = np.array(v, dtype=np.float32)
            if len(vec_arr) != self.target_dim:
                raise ValueError(
                    f"[Embeddings Error] Expected {self.target_dim} dimensions at index {idx}, got {len(vec_arr)}"
                )
            results.append(vec_arr.tolist())
        return results

    def embed_memory(self, title: str, summary: str, topics: Any, transcript: str) -> List[float]:
        """
        Creates 1024-dim dense embedding from:
        TITLE + SUMMARY + TOPICS + TRANSCRIPT
        """
        composite_text = self.compose_embedding_text(title, summary, topics, transcript)
        return self.embed_text(composite_text)


# Singleton instance
embedding_service = EmbeddingService()

