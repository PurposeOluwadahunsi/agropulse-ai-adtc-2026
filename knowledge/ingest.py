

from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings

from core.embedder import embed_batch

logger = logging.getLogger(__name__)

ROOT_DIR         = Path(__file__).parent.parent
VETDB_PATH       = ROOT_DIR / "knowledge" / "vetdb.json"
DOCS_DIR         = ROOT_DIR / "knowledge" / "docs"
VECTORSTORE_PATH = ROOT_DIR / "vectorstore"
COLLECTION_NAME  = "agropulse_knowledge"
CHUNK_SIZE       = 800
CHUNK_OVERLAP    = 100


def get_client() -> chromadb.PersistentClient:
    VECTORSTORE_PATH.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(
        path=str(VECTORSTORE_PATH),
        settings=Settings(anonymized_telemetry=False),
    )


def reset_collection(client: chromadb.PersistentClient) -> chromadb.Collection:
    existing = [c.name for c in client.list_collections()]
    if COLLECTION_NAME in existing:
        client.delete_collection(COLLECTION_NAME)
        logger.info(f"Deleted existing collection '{COLLECTION_NAME}'.")
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    logger.info(f"Created fresh collection '{COLLECTION_NAME}'.")
    return collection


def _make_chunk(
    chunk_id, section, text, disease_name, severity, vet_referral, sources
):
    return {
        "id":           chunk_id,
        "text":         text.strip(),
        "disease_name": disease_name,
        "chunk_type":   section,
        "severity":     severity,
        "vet_referral": str(vet_referral),
        "source":       sources,
        "section":      section.replace("_", " ").title(),
    }


def ingest_vetdb() -> list[dict[str, str]]:
    if not VETDB_PATH.exists():
        raise FileNotFoundError(f"vetdb.json not found at {VETDB_PATH}.")

    with open(VETDB_PATH, encoding="utf-8") as f:
        db = json.load(f)

    diseases = db.get("diseases", [])
    if not diseases:
        raise ValueError("vetdb.json contains no disease entries.")

    all_chunks = []
    counts = {}

    for disease in diseases:
        name         = disease["name"]
        did          = disease["id"]
        severity     = disease["severity"]
        vet_referral = disease.get("vet_referral", False)
        refs         = disease.get("references", disease.get("sources", ["vetdb.json"]))
        sources      = ", ".join(refs)
        aliases      = ", ".join(disease.get("aliases", []))

        def add(section, text):
            all_chunks.append(_make_chunk(
                f"{did}_{section}", section, text,
                name, severity, vet_referral, sources,
            ))
            counts[section] = counts.get(section, 0) + 1

        add("symptoms",
            f"Disease: {name}. Also known as: {aliases}. Severity: {severity}. "
            f"Affected birds: {', '.join(disease.get('affected_birds', ['poultry']))}. "
            f"Symptoms: {', '.join(disease.get('symptoms', []))}. "
            f"Distinguishing symptoms: {', '.join(disease.get('distinguishing_symptoms', []))}. "
            f"Incubation: {disease.get('incubation_days', 'unknown')} days. "
            f"Mortality: {disease.get('mortality_rate', 'variable')}."
        )

        add("treatment",
            f"First aid and treatment for {name}: "
            f"{disease.get('first_aid', '')} "
            f"Treatment: {disease.get('treatment', '')} "
            f"Vet referral: {vet_referral}. "
            f"When to call vet: {disease.get('when_to_call_vet', '')}"
        )

        zoonotic_note = (
            f"ZOONOTIC WARNING: {disease.get('zoonotic_note', '')}"
            if disease.get("zoonotic") else ""
        )
        add("prevention",
            f"Prevention of {name}: {disease.get('prevention', '')} "
            f"Vaccination: {disease.get('vaccination_notes', '')} "
            f"{'Contagious.' if disease.get('contagious') else 'Not directly contagious.'} "
            f"{zoonotic_note}"
        )

        biosec = disease.get("biosecurity_actions", [])
        if biosec:
            add("biosecurity",
                f"Biosecurity measures for {name}: "
                + " ".join(f"({i+1}) {a}" for i, a in enumerate(biosec))
            )

    logger.info(
        f"vetdb.json: {len(diseases)} diseases => {len(all_chunks)} chunks {counts}"
    )
    return all_chunks


def _split_text(text, chunk_size, overlap):
    if len(text) <= chunk_size:
        return [text.strip()] if text.strip() else []
    chunks = []
    start  = 0
    while start < len(text):
        end = start + chunk_size
        if end < len(text):
            boundary = text.rfind(" ", start, end)
            if boundary > start:
                end = boundary
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap
    return chunks


def ingest_pdfs():
    if not DOCS_DIR.exists():
        logger.warning(f"knowledge/docs/ not found. Skipping PDFs.")
        return []
    pdf_files = list(DOCS_DIR.glob("*.pdf"))
    if not pdf_files:
        logger.warning("No PDFs found. Skipping.")
        return []
    try:
        import pypdf
    except ImportError:
        logger.error("pypdf not installed.")
        return []

    all_chunks = []
    for pdf_path in pdf_files:
        try:
            reader    = pypdf.PdfReader(str(pdf_path))
            full_text = "".join((p.extract_text() or "") + "\n" for p in reader.pages)
            if not full_text.strip():
                continue
            text_chunks = _split_text(full_text, CHUNK_SIZE, CHUNK_OVERLAP)
            stem        = pdf_path.stem.replace("_", " ").replace("-", " ")
            for i, ct in enumerate(text_chunks):
                all_chunks.append({
                    "id": f"pdf_{pdf_path.stem}_{i:04d}", "text": ct,
                    "disease_name": stem, "chunk_type": "document",
                    "severity": "unknown", "vet_referral": "False",
                    "source": pdf_path.name, "section": "Document",
                })
        except Exception as exc:
            logger.error(f"Failed {pdf_path.name}: {exc}")
    return all_chunks


def add_to_collection(collection, chunks, batch_size=64):
    total = len(chunks)
    added = 0
    for start in range(0, total, batch_size):
        batch     = chunks[start:start + batch_size]
        texts     = [c["text"] for c in batch]
        ids       = [c["id"]   for c in batch]
        metadatas = [{
            "disease_name": c["disease_name"],
            "chunk_type":   c["chunk_type"],
            "severity":     c["severity"],
            "vet_referral": c["vet_referral"],
            "source":       c["source"],
            "section":      c.get("section", c["chunk_type"]),
        } for c in batch]
        collection.add(
            ids=ids, documents=texts,
            embeddings=embed_batch(texts), metadatas=metadatas,
        )
        added += len(batch)
        logger.info(f"  Embedded {added}/{total} chunks...")


def run_ingestion():
    t0         = time.perf_counter()
    client     = get_client()
    collection = reset_collection(client)
    vetdb_chunks = ingest_vetdb()
    pdf_chunks   = ingest_pdfs()
    all_chunks   = vetdb_chunks + pdf_chunks
    if not all_chunks:
        raise RuntimeError("No chunks to ingest.")
    add_to_collection(collection, all_chunks)
    elapsed = time.perf_counter() - t0
    result  = {
        "vetdb_chunks": len(vetdb_chunks),
        "pdf_chunks":   len(pdf_chunks),
        "total_chunks": collection.count(),
    }
    logger.info(f"Ingestion done in {elapsed:.1f}s. Total: {result['total_chunks']}.")
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s")
    print("=" * 60)
    print("=" * 60)
    stats = run_ingestion()
    print("\n" + "=" * 60)
    print("INGESTION COMPLETE")
    print(f"  vetdb.json chunks : {stats['vetdb_chunks']}")
    print(f"  PDF chunks        : {stats['pdf_chunks']}")
    print(f"  Total in store    : {stats['total_chunks']}")
    print("=" * 60)
    sys.exit(0)