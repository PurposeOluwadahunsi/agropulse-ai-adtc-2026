"""
core/embedder.py  (Sprint 5 — optimised)

Sprint 5 changes:
    - lru_cache ensures model loads exactly once per process
    - embed_text caches results for identical strings (query cache)
    - embed_batch avoids redundant encoding
    - Timing instrumentation added
"""

from __future__ import annotations

import logging
import sys
import os
import time
from functools import lru_cache
from pathlib import Path

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CACHE_DIR  = Path(__file__).parent.parent / "models"

# Simple in-process query cache — avoids re-embedding the same string
# across multiple Streamlit reruns within one session.
_embed_cache: dict[str, list[float]] = {}


@lru_cache(maxsize=1)
def get_embedder() -> SentenceTransformer:
    """
    Load and return the embedding model.
    Called once per process — subsequent calls return the cached instance.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    logger.info(f"Loading embedding model: {MODEL_NAME}")
    # Force offline mode — prevents HuggingFace network calls when Wi-Fi is off
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_DATASETS_OFFLINE"]  = "1"
    try:
        model = SentenceTransformer(MODEL_NAME, cache_folder=str(CACHE_DIR))
        elapsed = time.perf_counter() - t0
        logger.info(f"Embedding model loaded in {elapsed:.2f}s.")
        return model
    except Exception as exc:
        raise RuntimeError(
            f"Could not load embedding model '{MODEL_NAME}': {exc}"
        ) from exc


def embed_text(text: str) -> list[float]:
    """
    Embed a single string.
    Results are cached in-process — identical queries skip re-encoding.
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text must be a non-empty string.")

    key = text.strip()
    if key in _embed_cache:
        logger.debug("Embedding cache hit.")
        return _embed_cache[key]

    model  = get_embedder()
    vector = model.encode(key, convert_to_numpy=True).tolist()
    _embed_cache[key] = vector
    return vector


def embed_batch(texts: list[str]) -> list[list[float]]:
    """
    Embed a list of strings in one forward pass.
    Skips texts already in the cache.
    """
    if not texts:
        raise ValueError("texts list is empty.")

    model   = get_embedder()
    results = []
    to_encode: list[tuple[int, str]] = []

    for i, text in enumerate(texts):
        key = text.strip()
        if key in _embed_cache:
            results.append((i, _embed_cache[key]))
        else:
            to_encode.append((i, key))

    if to_encode:
        indices, raw_texts = zip(*to_encode)
        vectors = model.encode(
            list(raw_texts),
            convert_to_numpy=True,
            batch_size=32,
            show_progress_bar=False,
        )
        for idx, vec in zip(indices, vectors):
            v = vec.tolist()
            _embed_cache[texts[idx].strip()] = v
            results.append((idx, v))

    results.sort(key=lambda x: x[0])
    return [v for _, v in results]


def clear_embed_cache() -> None:
    """Clear the in-process embedding cache. Useful for testing."""
    _embed_cache.clear()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    print("=" * 55)
    print("AgroPulse AI — Sprint 5 Embedder Test")
    print("=" * 55)

    print("\n[1/3] Loading model...")
    t0 = time.perf_counter()
    get_embedder()
    print(f"      Load time: {time.perf_counter() - t0:.2f}s")

    print("\n[2/3] Cache test...")
    embed_text("my chickens are gasping")
    t0 = time.perf_counter()
    embed_text("my chickens are gasping")
    cached_ms = (time.perf_counter() - t0) * 1000
    print(f"      Cached call: {cached_ms:.2f}ms (should be <1ms)")
    assert cached_ms < 5

    print("\n[3/3] Batch embed 3 texts...")
    t0 = time.perf_counter()
    vecs = embed_batch([
        "Newcastle disease twisted neck",
        "bloody diarrhoea pale comb",
        "watery egg white drop in production",
    ])
    print(f"      Batch time: {(time.perf_counter()-t0)*1000:.1f}ms, {len(vecs)} vectors")
    assert len(vecs) == 3

    print("\nALL TESTS PASSED — embedder.py ready.")
    sys.exit(0)