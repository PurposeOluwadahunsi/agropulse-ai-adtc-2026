"""
ui/pipeline.py  (Sprint 5 — optimised)

Sprint 5 changes:
    - Per-stage timing added to result dict (triage_ms, rag_ms, llm_ms)
    - run_startup reuses existing ChromaDB collection via module singleton
    - No other interface changes — fully backward compatible
"""

from __future__ import annotations

import logging
import time
from typing import Any

from core.triage  import triage
from core.rag     import retrieve, get_or_create_collection
from core.llm     import generate, warmup, _check_ollama_running
from core.logbook import Logbook, LogEntry

logger = logging.getLogger(__name__)


def run_startup(logbook: Logbook) -> tuple[bool, str, str]:
    """
    Startup checks, ChromaDB pre-warm, LLM warmup.
    Returns (success, session_id, error_message).
    """
    # Pre-warm ChromaDB collection into module-level singleton
    try:
        get_or_create_collection()
    except RuntimeError as exc:
        return False, "", str(exc)

    if not _check_ollama_running():
        return (
            False, "",
            "Ollama is not running. Open a terminal and run: ollama serve",
        )

    warmup()
    session_id = logbook.start_session()
    return True, session_id, ""


def run_analysis(
    query:      str,
    session_id: str,
    logbook:    Logbook,
) -> dict[str, Any]:
    """
    Full pipeline: triage → RAG → LLM → logbook.
    Result dict now includes triage_ms, rag_ms, llm_ms for display.
    """
    t_total = time.perf_counter()

    result: dict[str, Any] = {
        "success":          False,
        "error":            "",
        "query":            query,
        "triage_matched":   False,
        "disease_name":     None,
        "disease_id":       None,
        "severity":         None,
        "confidence":       "none",
        "triage_score":     0.0,
        "matched_symptoms": [],
        "vet_referral":     False,
        "first_aid":        "",
        "treatment":        "",
        "prevention":       "",
        "biosecurity":      [],
        "when_to_call_vet": "",
        "ai_response":      "",
        "rag_sources":      [],
        "response_ms":      0,
        "triage_ms":        0,
        "rag_ms":           0,
        "llm_ms":           0,
        "log_id":           0,
    }

    try:
        # Triage
        t0            = time.perf_counter()
        triage_result = triage(query)
        result["triage_ms"] = int((time.perf_counter() - t0) * 1000)

        result["triage_matched"]   = triage_result.matched
        result["disease_name"]     = triage_result.disease_name
        result["disease_id"]       = triage_result.disease_id
        result["severity"]         = triage_result.severity
        result["confidence"]       = triage_result.confidence
        result["triage_score"]     = triage_result.score
        result["matched_symptoms"] = triage_result.matched_symptoms
        result["vet_referral"]     = triage_result.vet_referral
        result["first_aid"]        = triage_result.first_aid
        result["treatment"]        = triage_result.treatment
        result["prevention"]       = triage_result.prevention
        result["biosecurity"]      = getattr(triage_result, "biosecurity", [])
        result["when_to_call_vet"] = getattr(triage_result, "when_to_call_vet", "")

        # RAG
        t0         = time.perf_counter()
        rag_chunks = retrieve(query, k=2)
        result["rag_ms"]     = int((time.perf_counter() - t0) * 1000)
        result["rag_sources"] = list({c["source"] for c in rag_chunks})

        # LLM
        t0     = time.perf_counter()
        tokens: list[str] = []
        for token in generate(query, stream=True):
            tokens.append(token)
        result["ai_response"] = "".join(tokens)
        result["llm_ms"]      = int((time.perf_counter() - t0) * 1000)

        # Totals
        result["response_ms"] = int((time.perf_counter() - t_total) * 1000)

        # Logbook
        entry = LogEntry(
            session_id       = session_id,
            user_input       = query,
            ai_response      = result["ai_response"],
            triage_matched   = triage_result.matched,
            disease_hit      = triage_result.disease_name,
            disease_id       = triage_result.disease_id,
            severity         = triage_result.severity,
            triage_score     = triage_result.score,
            triage_conf      = triage_result.confidence,
            matched_symptoms = triage_result.matched_symptoms,
            vet_needed       = triage_result.vet_referral,
            rag_sources      = result["rag_sources"],
            response_ms      = result["response_ms"],
        )
        result["log_id"] = logbook.write_entry(entry)
        result["success"] = True

    except Exception as exc:
        result["response_ms"] = int((time.perf_counter() - t_total) * 1000)
        result["error"] = str(exc)
        logger.error(f"Pipeline error: {exc}", exc_info=True)

    return result


def get_farm_status(entries: list[dict[str, Any]]) -> tuple[str, str]:
    if not entries:
        return "No Data", ""
    recent     = entries[:3]
    severities = [e.get("severity") for e in recent]
    if "critical" in severities:
        return "Critical", "critical"
    if "moderate" in severities:
        return "Watch", "watch"
    return "Healthy", "healthy"