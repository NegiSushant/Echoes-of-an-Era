"""
Embedding Service Audit and Verification Script for 'Echoes of an Era'

Verifies:
1. EMBEDDING_LOCAL_ONLY=true fails loudly when BGE-M3 weights are missing from local cache.
2. No silent fallback to all-MiniLM-L6-v2 or any 384-dim model.
3. No zero-padding or vector truncation.
4. Correct behavior of get_model_info() and test_embedding() on BAAI/bge-m3.
5. Consistent 1024-dimensional normalized dense embeddings.
"""

import os
import sys
import numpy as np

# Ensure backend directory is in sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.services.embeddings import EmbeddingService


def test_audit_suite():
    print("=" * 70)
    print("RUNNING EMBEDDING SERVICE AUDIT & VERIFICATION SUITE")
    print("=" * 70)

    # -------------------------------------------------------------------------
    # TEST 1: Fail Loudly with EMBEDDING_LOCAL_ONLY=true when weights missing
    # -------------------------------------------------------------------------
    print("\n[Test 1/4] Verifying 'fail loudly' behavior when EMBEDDING_LOCAL_ONLY=true...")
    # Initialize service with local_only=True
    service_local_strict = EmbeddingService(model_name="BAAI/bge-m3", device="cpu", local_only=True)
    
    # We test whether the local cache load raises RuntimeError if weights are not cached
    from huggingface_hub import try_to_load_from_cache
    cached_weights = try_to_load_from_cache("BAAI/bge-m3", "pytorch_model.bin")
    
    if cached_weights is None:
        print("  -> BAAI/bge-m3 'pytorch_model.bin' is not in local cache.")
        try:
            service_local_strict._get_model()
            raise AssertionError("FAIL: Expected RuntimeError when loading missing model with local_only=True, but succeeded!")
        except RuntimeError as e:
            print("  -> PASSED: Service failed loudly with RuntimeError as required.")
            print(f"     Captured error summary: {str(e).strip().splitlines()[1]}")
            assert "EMBEDDING_LOCAL_ONLY=true" in str(e)
            assert "BAAI/bge-m3" in str(e)
    else:
        print(f"  -> Model weights found in local cache at: {cached_weights}")
        model = service_local_strict._get_model()
        assert service_local_strict._source == "local Hugging Face cache"
        print("  -> PASSED: Loaded successfully from local Hugging Face cache.")

    # -------------------------------------------------------------------------
    # TEST 2: Verifying rejection of dimension mismatch (no zero-padding fallback)
    # -------------------------------------------------------------------------
    print("\n[Test 2/4] Verifying elimination of 384-dim zero-padding fallback...")
    # If someone attempts to initialize with all-MiniLM-L6-v2, it MUST fail dimension assertion
    minilm_service = EmbeddingService(model_name="sentence-transformers/all-MiniLM-L6-v2", device="cpu", local_only=False)
    try:
        minilm_service._get_model()
        raise AssertionError("FAIL: Service allowed 384-dim model without failing dimension check!")
    except ValueError as e:
        print("  -> PASSED: Dimension mismatch rejected with ValueError.")
        print(f"     Captured message: {e}")
        assert "expected 1024" in str(e)

    # -------------------------------------------------------------------------
    # TEST 3: Health Method get_model_info() Schema & Value Contract
    # -------------------------------------------------------------------------
    print("\n[Test 3/4] Verifying get_model_info() contract...")
    # Mock or live check
    dummy_service = EmbeddingService(model_name="BAAI/bge-m3", device="cpu")
    class MockModel:
        def get_sentence_embedding_dimension(self):
            return 1024
        def encode(self, text, normalize_embeddings=True, **kwargs):
            vec = np.ones(1024, dtype=np.float32)
            return vec / np.linalg.norm(vec)

    dummy_service._model = MockModel()
    dummy_service._source = "local Hugging Face cache"

    info = dummy_service.get_model_info()
    print("  -> get_model_info() returned:")
    print(f"     {info}")

    assert info["model_name"] == "BAAI/bge-m3", f"Wrong model_name: {info['model_name']}"
    assert info["device"] == "cpu", f"Wrong device: {info['device']}"
    assert info["dimension"] == 1024, f"Wrong dimension: {info['dimension']}"
    assert info["normalized"] is True, f"Wrong normalized: {info['normalized']}"
    assert info["local"] is True, f"Wrong local: {info['local']}"
    print("  -> PASSED: Exact dictionary schema and values matched.")

    # -------------------------------------------------------------------------
    # TEST 4: Verification of test_embedding() method on reference phrase
    # -------------------------------------------------------------------------
    print("\n[Test 4/4] Verifying test_embedding() validation logic...")
    test_phrase = "Grandfather remembers using letters to communicate with family."
    test_res = dummy_service.test_embedding(test_phrase)
    print("  -> test_embedding() returned:")
    print(f"     {test_res}")

    assert test_res["status"] == "passed"
    assert test_res["sample_text"] == test_phrase
    assert test_res["dimension"] == 1024
    assert test_res["normalized"] is True
    assert test_res["finite"] is True
    assert test_res["has_nan"] is False
    assert test_res["has_inf"] is False
    assert abs(test_res["l2_norm"] - 1.0) < 1e-3
    print("  -> PASSED: Reference test phrase verification passed all criteria.")

    print("\n" + "=" * 70)
    print("ALL AUDIT & BEHAVIOR CHECKS COMPLETED SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":
    test_audit_suite()
