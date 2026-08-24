"""
core/rag.py  (Sprint 5 — optimised)

Sprint 5 changes:
    - ChromaDB collection cached in-process (_collection singleton)
    - Results deduplicated by disease+section to reduce prompt size
    - Default k reduced to 2 (was 3)
    - Chunk text truncated to 400 chars in LLM context
    - Timing instrumentation added
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings

from core.embedder import embed_text, embed_batch

logger = logging.getLogger(__name__)

VECTORSTORE_PATH = Path(__file__).parent.parent / "vectorstore"
VETDB_PATH       = Path(__file__).parent.parent / "knowledge" / "vetdb.json"
COLLECTION_NAME  = "agropulse_knowledge"
AUTHORITATIVE    = {"FAO", "OIE", "NVRI", "Merck", "Federal Ministry"}
AUTHORITY_BOOST  = 0.05

_collection: chromadb.Collection | None = None


def _is_authoritative(source: str) -> bool:
    return any(a in source for a in AUTHORITATIVE)


def get_or_create_collection() -> chromadb.Collection:
    global _collection
    if _collection is not None:
        return _collection

    VECTORSTORE_PATH.mkdir(parents=True, exist_ok=True)
    t0     = time.perf_counter()
    client = chromadb.PersistentClient(
        path=str(VECTORSTORE_PATH),
        settings=Settings(anonymized_telemetry=False),
    )

    existing = [c.name for c in client.list_collections()]
    if COLLECTION_NAME not in existing:
        raise RuntimeError(
            "Vector store is empty. Run: python knowledge/ingest.py"
        )

    _collection = client.get_collection(name=COLLECTION_NAME)
    logger.info(
        f"ChromaDB loaded in {(time.perf_counter()-t0)*1000:.0f}ms "
        f"({_collection.count()} docs)."
    )
    return _collection


def retrieve(
    query: str,
    k: int = 2,
    chunk_type_filter: str | None = None,
) -> list[dict[str, Any]]:
    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    t0         = time.perf_counter()
    collection = get_or_create_collection()

    where     = {"chunk_type": {"$eq": chunk_type_filter}} if chunk_type_filter else None
    n_results = min(k + 2, collection.count())

    raw = collection.query(
        query_embeddings=[embed_text(query.strip())],
        n_results=n_results,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    chunks: list[dict[str, Any]] = []
    seen:   set[str]             = set()

    for i, doc in enumerate(raw["documents"][0]):
        meta     = raw["metadatas"][0][i]
        distance = raw["distances"][0][i]
        source   = meta.get("source", "vetdb.json")

        base_conf = max(0.0, 1.0 - distance)
        adj_conf  = (
            min(1.0, base_conf + AUTHORITY_BOOST)
            if _is_authoritative(source) else base_conf
        )

        dedup_key = f"{meta.get('disease_name','')}:{meta.get('chunk_type','')}"
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        chunks.append({
            "text":             doc,
            "disease_name":     meta.get("disease_name", "Unknown"),
            "chunk_type":       meta.get("chunk_type", "unknown"),
            "severity":         meta.get("severity", "unknown"),
            "vet_referral":     meta.get("vet_referral", "False"),
            "source":           source,
            "source_title":     source.split(",")[0].strip(),
            "source_section":   meta.get("section", meta.get("chunk_type", "").title()),
            "distance":         round(distance, 4),
            "confidence_score": round(adj_conf, 4),
        })

        if len(chunks) >= k:
            break

    chunks.sort(key=lambda c: c["confidence_score"], reverse=True)
    logger.info(f"RAG: {len(chunks)} chunks in {(time.perf_counter()-t0)*1000:.0f}ms")
    return chunks


def format_context_for_llm(chunks: list[dict[str, Any]]) -> str:
    if not chunks:
        return "No relevant knowledge base context found."

    lines = ["KNOWLEDGE BASE:"]
    for i, c in enumerate(chunks, 1):
        conf_pct = int(c.get("confidence_score", 0) * 100)
        lines.append(
            f"[{i}] {c['disease_name']} / {c.get('source_section','Info')} "
            f"({conf_pct}% | {c['source_title']})"
        )
        text = c["text"]
        if len(text) > 400:
            text = text[:397] + "..."
        lines.append(text)
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s")
    print("=" * 60)
    print("AgroPulse AI — Sprint 5 RAG Test")
    print("=" * 60)

    t0  = time.perf_counter()
    col = get_or_create_collection()
    print(f"\n[1] {col.count()} docs, {(time.perf_counter()-t0)*1000:.0f}ms")

    t0 = time.perf_counter()
    get_or_create_collection()
    print(f"[2] Cache call: {(time.perf_counter()-t0)*1000:.2f}ms")

    t0 = time.perf_counter()
    results = retrieve("twisted neck circling green diarrhoea", k=2)
    print(f"[3] {len(results)} chunks in {(time.perf_counter()-t0)*1000:.0f}ms")
    for r in results:
        print(f"    [{r['chunk_type']:12s}] {r['disease_name']:28s} conf={r['confidence_score']:.3f}")

    keys = [f"{r['disease_name']}:{r['chunk_type']}" for r in results]
    assert len(keys) == len(set(keys)), "Dedup failed"
    print("    Deduplication: OK")
    print("\nALL TESTS PASSED.")
    sys.exit(0)