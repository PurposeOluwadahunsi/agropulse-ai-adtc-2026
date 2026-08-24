

from __future__ import annotations

import logging
import sys
import os
import time
from functools import lru_cache
from pathlib import Path

# Force offline mode BEFORE importing/initialising model components.
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

BASE_DIR = Path(__file__).parent.parent
CACHE_DIR = BASE_DIR / "models"


MODEL_DIR = (
    CACHE_DIR
    / "models--sentence-transformers--all-MiniLM-L6-v2"
    / "snapshots"
)

# Simple in-process query cache.
_embed_cache: dict[str, list[float]] = {}


def _find_local_model() -> Path:
    """
    Find the locally cached SentenceTransformer snapshot.

    No network access is used.
    """
    if not MODEL_DIR.exists():
        raise RuntimeError(
            f"Local embedding model was not found at:\n{MODEL_DIR}\n\n"
            "The all-MiniLM-L6-v2 model must be downloaded before "
            "running AgroPulse AI offline."
        )

    snapshots = [
        path for path in MODEL_DIR.iterdir()
        if path.is_dir()
    ]

    if not snapshots:
        raise RuntimeError(
            f"No model snapshot was found inside:\n{MODEL_DIR}"
        )

    # Use the first available local snapshot.
    local_model = snapshots[0]

    logger.info(f"Using local embedding model: {local_model}")
    return local_model


@lru_cache(maxsize=1)
def get_embedder() -> SentenceTransformer:
    """
    Load and return the local embedding model.

    Called once per process — subsequent calls return the cached instance.
    """
    t0 = time.perf_counter()

    local_model = _find_local_model()

    logger.info(
        f"Loading offline embedding model from: {local_model}"
    )

    try:
        model = SentenceTransformer(
            str(local_model),
            local_files_only=True,
        )

        elapsed = time.perf_counter() - t0
        logger.info(
            f"Embedding model loaded offline in {elapsed:.2f}s."
        )

        return model

    except Exception as exc:
        raise RuntimeError(
            f"Could not load local embedding model from "
            f"'{local_model}': {exc}"
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

    model = get_embedder()

    vector = model.encode(
        key,
        convert_to_numpy=True
    ).tolist()

    _embed_cache[key] = vector

    return vector


def embed_batch(texts: list[str]) -> list[list[float]]:
    """
    Embed a list of strings in one forward pass.

    Skips texts already in the cache.
    """
    if not texts:
        raise ValueError("texts list is empty.")

    model = get_embedder()

    results = []
    to_encode: list[tuple[int, str]] = []

    for i, text in enumerate(texts):
        key = text.strip()

        if not key:
            raise ValueError(
                f"text at index {i} is empty."
            )

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
    print("AgroPulse AI — Offline Embedder Test")
    print("=" * 55)

    print("\n[1/3] Loading local model...")

    t0 = time.perf_counter()

    get_embedder()

    print(
        f"      Load time: "
        f"{time.perf_counter() - t0:.2f}s"
    )

    print("\n[2/3] Cache test...")

    embed_text("my chickens are gasping")

    t0 = time.perf_counter()

    embed_text("my chickens are gasping")

    cached_ms = (
        time.perf_counter() - t0
    ) * 1000

    print(
        f"      Cached call: "
        f"{cached_ms:.2f}ms"
    )

    assert cached_ms < 5

    print("\n[3/3] Batch embed 3 texts...")

    t0 = time.perf_counter()

    vecs = embed_batch([
        "Newcastle disease twisted neck",
        "bloody diarrhoea pale comb",
        "watery egg white drop in production",
    ])

    print(
        f"      Batch time: "
        f"{(time.perf_counter() - t0) * 1000:.1f}ms, "
        f"{len(vecs)} vectors"
    )

    assert len(vecs) == 3

    print("\nALL TESTS PASSED offline embedder ready.")

    sys.exit(0)