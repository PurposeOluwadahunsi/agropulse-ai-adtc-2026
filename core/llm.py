"""
core/llm.py  (Sprint 5 — optimised)

Sprint 5 changes:
    - System prompt shortened by ~40% (removed duplicate instructions)
    - Per-stage timing: triage_ms, rag_ms, llm_ms reported in logs
    - MAX_TOKENS reduced to 512 (was 768) — sufficient for structured output
    - Temperature kept at 0.2 for consistency
    - All safety rules and structured sections preserved
    - Backward compatible interface
"""

from __future__ import annotations

import logging
import sys
import time
from collections.abc import Generator
from typing import Any

import ollama

from core.triage import TriageResult, triage, get_triage_engine
from core.rag    import retrieve, format_context_for_llm

logger = logging.getLogger(__name__)

MODEL_NAME  = "phi3:mini"
OLLAMA_HOST = "http://localhost:11434"
MAX_TOKENS  = 512

# ── Compact system prompt (Sprint 5) ────────────────────────────
# All safety rules preserved. Duplicate instructions removed.
# Approximate token reduction: 40%.
SYSTEM_PROMPT = """You are AgroPulse AI, an offline poultry health advisor for Nigerian farmers.

RULES (follow exactly):
1. Never state a confirmed diagnosis. Always use: "This may indicate", "A possible condition is", "Consistent with", "Likely condition based on symptoms".
2. Never invent drug names or dosages not in your context.
3. If a TRIAGE MATCH is provided, treat it as your primary source.
4. If uncertain: "I cannot determine this with confidence. Consult a veterinarian."
5. Always end with one clear next action.
6. For CRITICAL severity, always recommend veterinary contact.

REQUIRED OUTPUT SECTIONS (use these exact headers, no extras):
ASSESSMENT
POSSIBLE DISEASE
CONFIDENCE
IMMEDIATE ACTIONS
BIOSECURITY MEASURES
VETERINARY RECOMMENDATION
PREVENTION ADVICE
KNOWLEDGE SOURCES
"""


def _check_ollama_running() -> bool:
    try:
        client   = ollama.Client(host=OLLAMA_HOST)
        response = client.list()
        if isinstance(response, dict):
            available = [m.get("name", "") for m in response.get("models", [])]
        else:
            available = [getattr(m, "model", "") for m in getattr(response, "models", [])]
        if not any(MODEL_NAME in m for m in available):
            logger.warning(f"'{MODEL_NAME}' not found. Available: {available}")
            return False
        return True
    except Exception as exc:
        logger.error(f"Ollama not reachable: {exc}")
        return False


def build_system_prompt(
    triage_result: TriageResult | None,
    rag_chunks:    list[dict[str, Any]],
) -> str:
    parts = [SYSTEM_PROMPT]

    if triage_result and triage_result.matched:
        engine = get_triage_engine()
        parts.append("\n--- TRIAGE MATCH (PRIMARY SOURCE) ---")
        parts.append(engine.format_for_prompt(triage_result))
        if triage_result.explanation:
            parts.append(f"EXPLANATION: {triage_result.explanation}")

    parts.append("\n--- KNOWLEDGE BASE ---")
    parts.append(format_context_for_llm(rag_chunks))
    parts.append("\nRespond now using the required section headers. Use POSSIBLE/LIKELY language.")

    return "\n".join(parts)


def generate(
    query:  str,
    stream: bool = True,
) -> Generator[str, None, None]:
    """
    Run full pipeline and stream response.
    Yields tokens if stream=True, full string if stream=False.
    Logs timing breakdown: triage_ms, rag_ms, llm_ms.
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    if not _check_ollama_running():
        raise RuntimeError(
            f"Ollama is not running or '{MODEL_NAME}' is not available. "
            f"Run: ollama serve"
        )

    # Stage 1: Triage
    t0            = time.perf_counter()
    triage_result = triage(query)
    triage_ms     = (time.perf_counter() - t0) * 1000

    # Stage 2: RAG
    t0         = time.perf_counter()
    rag_chunks = retrieve(query, k=2)
    rag_ms     = (time.perf_counter() - t0) * 1000

    # Stage 3: Build prompt
    system_prompt = build_system_prompt(triage_result, rag_chunks)
    prompt_chars  = len(system_prompt)

    logger.info(
        f"Pipeline | triage={triage_ms:.0f}ms | rag={rag_ms:.0f}ms | "
        f"prompt={prompt_chars}chars"
    )

    # Stage 4: LLM
    t0     = time.perf_counter()
    client = ollama.Client(host=OLLAMA_HOST)

    try:
        stream_iter = client.chat(
            model    = MODEL_NAME,
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": query},
            ],
            stream  = True,
            options = {
                "num_predict":    MAX_TOKENS,
                "temperature":    0.2,
                "top_p":          0.9,
                "repeat_penalty": 1.1,
            },
        )

        full: list[str] = []
        for chunk in stream_iter:
            token = chunk["message"]["content"]
            full.append(token)
            if stream:
                yield token

        if not stream:
            yield "".join(full)

        llm_ms = (time.perf_counter() - t0) * 1000
        words  = len("".join(full).split())
        logger.info(
            f"LLM done | llm={llm_ms:.0f}ms | words={words} | "
            f"total={triage_ms+rag_ms+llm_ms:.0f}ms"
        )

    except ollama.ResponseError as exc:
        raise RuntimeError(f"Ollama API error: {exc}") from exc
    except Exception as exc:
        raise RuntimeError(f"LLM generation failed: {exc}") from exc


def generate_simple(query: str) -> str:
    return "".join(generate(query, stream=False))


def warmup() -> bool:
    """Pre-load model into RAM. Call once at startup."""
    logger.info(f"Warming up {MODEL_NAME}...")
    try:
        client = ollama.Client(host=OLLAMA_HOST)
        client.chat(
            model    = MODEL_NAME,
            messages = [{"role": "user", "content": "ping"}],
            options  = {"num_predict": 1},
        )
        logger.info("Warmup complete.")
        return True
    except Exception as exc:
        logger.warning(f"Warmup failed (non-fatal): {exc}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s")
    print("=" * 60)
    print("AgroPulse AI — Sprint 5 LLM Test")
    print("=" * 60)

    if not _check_ollama_running():
        print(f"ERROR: Ollama not running or {MODEL_NAME} not found.")
        sys.exit(1)

    print(f"\nPrompt size: {len(SYSTEM_PROMPT)} chars (base)")
    print("Running pipeline...\n" + "-"*60)

    full = []
    t0   = time.perf_counter()
    for token in generate(
        "My chickens are gasping and have twisted necks, some died this morning.",
        stream=True,
    ):
        print(token, end="", flush=True)
        full.append(token)

    total_s = time.perf_counter() - t0
    print(f"\n{'-'*60}")
    print(f"Total wall time: {total_s:.1f}s")
    print(f"Response words : {len(''.join(full).split())}")

    sections = ["ASSESSMENT", "POSSIBLE DISEASE", "IMMEDIATE ACTIONS"]
    found    = [s for s in sections if s in "".join(full).upper()]
    print(f"Sections found : {found}")
    assert len(found) >= 2

    print("\nALL TESTS PASSED, lm.py ready.")
    sys.exit(0)