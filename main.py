"""
main.py

AgroPulse AI — Terminal Demo (Sprint 2)

End-to-end pipeline:
    Farmer query
        → Triage (rule-based, instant)
        → RAG retrieval (ChromaDB)
        → LLM generation (Phi-3 Mini via Ollama, streamed)
        → Auto-save to farm logbook (SQLite)

Usage:
    python main.py            # interactive REPL
    python main.py --demo     # run 3 preset demo queries non-interactively
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from datetime import datetime

from core.triage  import triage, TriageResult
from core.rag     import retrieve, format_context_for_llm
from core.llm     import generate, warmup, _check_ollama_running, build_system_prompt
from core.logbook import Logbook, LogEntry

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.WARNING,          # Suppress info noise in terminal demo
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler("logs/agropulse.log", encoding="utf-8"),
        logging.StreamHandler(sys.stderr),
    ],
)

# Make sure logs/ directory exists
from pathlib import Path
Path("logs").mkdir(exist_ok=True)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Display helpers
# ─────────────────────────────────────────────

BANNER = """
╔══════════════════════════════════════════════════════╗
║           AgroPulse AI — Poultry Advisory            ║
║      Offline AI Assistant for Nigerian Farmers       ║
╚══════════════════════════════════════════════════════╝
"""

SEPARATOR = "─" * 56


def print_banner() -> None:
    print(BANNER)


def print_triage_result(result: TriageResult) -> None:
    """Print a formatted triage summary to the terminal."""
    if not result.matched:
        return

    severity_colours = {
        "critical": "\033[91m",   # red
        "moderate": "\033[93m",   # yellow
        "low":      "\033[92m",   # green
    }
    reset = "\033[0m"
    colour = severity_colours.get(result.severity or "", "")

    print(f"\n{SEPARATOR}")
    print(f"  TRIAGE RESULT")
    print(f"  Disease   : {result.disease_name}")
    print(f"  Severity  : {colour}{(result.severity or '').upper()}{reset}")
    print(f"  Confidence: {result.confidence}  (score={result.score:.1f})")
    print(f"  Symptoms  : {', '.join(result.matched_symptoms)}")
    if result.vet_referral:
        print(f"  \033[91m⚠  VET REFERRAL REQUIRED\033[0m")
    print(SEPARATOR)


def print_rag_sources(chunks: list[dict]) -> None:
    """Print the RAG sources used for context."""
    if not chunks:
        return
    print(f"\n  Sources consulted:")
    seen: set[str] = set()
    for chunk in chunks:
        src = f"  [{chunk['chunk_type'].upper()}] {chunk['disease_name']} — {chunk['source']}"
        if src not in seen:
            print(src)
            seen.add(src)


# ─────────────────────────────────────────────
# Core pipeline
# ─────────────────────────────────────────────

def run_pipeline(
    query: str,
    session_id: str,
    logbook: Logbook,
) -> str:
    """
    Run the full AgroPulse pipeline for a single farmer query.

    Steps:
        1. Triage
        2. RAG retrieval
        3. LLM streaming generation
        4. Save to logbook

    Args:
        query:      Raw farmer query string.
        session_id: Active session UUID.
        logbook:    Logbook instance for persistence.

    Returns:
        Complete AI response string.
    """
    t_start = time.perf_counter()

    # Step 1: Triage
    triage_result = triage(query)
    print_triage_result(triage_result)

    # Step 2: RAG
    rag_chunks = retrieve(query, k=3)

    # Step 3: Stream LLM response
    print(f"\n\033[1mAgroPulse AI:\033[0m\n")
    response_tokens: list[str] = []

    try:
        for token in generate(query, stream=True):
            print(token, end="", flush=True)
            response_tokens.append(token)
    except RuntimeError as exc:
        error_msg = str(exc)
        print(f"\n[ERROR] {error_msg}", file=sys.stderr)
        logger.error(f"Pipeline error: {exc}")
        return error_msg

    full_response = "".join(response_tokens)
    elapsed_ms = int((time.perf_counter() - t_start) * 1000)

    print(f"\n\n{SEPARATOR}")

    # Step 4: Print sources
    print_rag_sources(rag_chunks)
    print(f"\n  Response time: {elapsed_ms}ms")
    print(SEPARATOR)

    # Step 5: Save to logbook
    entry = LogEntry(
        session_id       = session_id,
        user_input       = query,
        ai_response      = full_response,
        triage_matched   = triage_result.matched,
        disease_hit      = triage_result.disease_name,
        disease_id       = triage_result.disease_id,
        severity         = triage_result.severity,
        triage_score     = triage_result.score,
        triage_conf      = triage_result.confidence,
        matched_symptoms = triage_result.matched_symptoms,
        vet_needed       = triage_result.vet_referral,
        rag_sources      = list({c["source"] for c in rag_chunks}),
        response_ms      = elapsed_ms,
    )
    row_id = logbook.write_entry(entry)
    print(f"  Log entry saved (ID: {row_id})")

    return full_response


# ─────────────────────────────────────────────
# Interactive REPL
# ─────────────────────────────────────────────

HELP_TEXT = """
Commands:
  /log      — show the 5 most recent logbook entries
  /stats    — show session statistics
  /clear    — clear the terminal
  /help     — show this message
  /quit     — exit AgroPulse AI
  (anything else is sent to the AI as a query)
"""

def show_recent_log(logbook: Logbook, n: int = 5) -> None:
    """Print the n most recent logbook entries."""
    entries = logbook.get_recent(n)
    if not entries:
        print("  No entries in logbook yet.")
        return

    print(f"\n  Last {len(entries)} logbook entries:")
    print(f"  {'ID':>4}  {'Timestamp':<20}  {'Disease':<25}  {'Conf':<8}  {'ms':>6}")
    print("  " + "─" * 70)
    for e in entries:
        print(
            f"  {e['id']:>4}  {e['timestamp']:<20}  "
            f"{(e['disease_hit'] or 'No match'):<25}  "
            f"{(e['triage_conf'] or '-'):<8}  "
            f"{(e['response_ms'] or 0):>6}"
        )


def interactive_loop(logbook: Logbook, session_id: str) -> None:
    """Run the interactive REPL until the user types /quit."""
    print("\nType your question below. Type /help for commands, /quit to exit.\n")

    while True:
        try:
            user_input = input("\033[94mFarmer:\033[0m ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nExiting AgroPulse AI. Goodbye.")
            break

        if not user_input:
            continue

        if user_input.lower() in ("/quit", "/exit", "quit", "exit"):
            print("\nExiting AgroPulse AI. Goodbye.")
            break

        if user_input.lower() == "/help":
            print(HELP_TEXT)
            continue

        if user_input.lower() == "/log":
            show_recent_log(logbook)
            continue

        if user_input.lower() == "/stats":
            stats = logbook.get_stats()
            print(f"\n  Total queries  : {stats['total_queries']}")
            print(f"  Triage hits    : {stats['triage_hits']}")
            print(f"  Vet referrals  : {stats['vet_referrals']}")
            if stats["disease_breakdown"]:
                print(f"  Disease breakdown:")
                for disease, count in stats["disease_breakdown"].items():
                    print(f"    {disease}: {count}")
            continue

        if user_input.lower() == "/clear":
            print("\033c", end="")
            print_banner()
            continue

        run_pipeline(user_input, session_id, logbook)


# ─────────────────────────────────────────────
# Demo mode
# ─────────────────────────────────────────────

DEMO_QUERIES = [
    "My chickens are gasping for air and some have twisted necks. About 10 died this morning.",
    "The chicks have watery diarrhoea and they huddle together picking at their vents.",
    "I found blood in the droppings of my 3-week-old chicks and their combs are pale.",
]


def demo_mode(logbook: Logbook, session_id: str) -> None:
    """Run 3 preset demo queries non-interactively."""
    print("\n\033[1mDEMO MODE — Running 3 preset queries\033[0m\n")

    for i, query in enumerate(DEMO_QUERIES, start=1):
        print(f"\n{'═' * 56}")
        print(f"  DEMO QUERY {i}/{len(DEMO_QUERIES)}")
        print(f"{'═' * 56}")
        print(f"\n\033[94mFarmer:\033[0m {query}\n")
        run_pipeline(query, session_id, logbook)
        time.sleep(1)

    print(f"\n{'═' * 56}")
    print("DEMO COMPLETE")
    show_recent_log(logbook, n=3)
    stats = logbook.get_stats()
    print(f"\n  Total queries saved to logbook: {stats['total_queries']}")
    print(f"{'═' * 56}\n")


# ─────────────────────────────────────────────
# Startup checks
# ─────────────────────────────────────────────

def startup_checks() -> bool:
    """
    Verify all required components are available before starting.

    Returns:
        True if all checks pass, False otherwise.
    """
    print("  Checking components...")
    all_ok = True

    # 1. vetdb.json
    vetdb = Path("knowledge/vetdb.json")
    status = "OK" if vetdb.exists() else "MISSING"
    print(f"  {'vetdb.json':<30} [{status}]")
    if status == "MISSING":
        all_ok = False

    # 2. ChromaDB vectorstore
    vs_path = Path("vectorstore")
    vs_ok = vs_path.exists() and any(vs_path.iterdir()) if vs_path.exists() else False
    status = "OK" if vs_ok else "EMPTY — run: python knowledge/ingest.py"
    print(f"  {'vectorstore/':<30} [{status}]")
    if not vs_ok:
        all_ok = False

    # 3. Ollama
    ollama_ok = _check_ollama_running()
    status = "OK" if ollama_ok else "NOT RUNNING — run: ollama serve"
    print(f"  {'Ollama (phi3:mini)':<30} [{status}]")
    if not ollama_ok:
        all_ok = False

    return all_ok


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="AgroPulse AI — Offline Poultry Advisory System"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run 3 preset demo queries and exit.",
    )
    args = parser.parse_args()

    print_banner()
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Startup checks
    if not startup_checks():
        print("\n  [STARTUP FAILED] Fix the issues above and try again.\n")
        sys.exit(1)

    print("\n  All checks passed. Warming up model...")

    # Warm up Phi-3 (loads it into RAM before first query)
    warmup()
    print("  Model is warm. Ready.\n")

    # Initialise logbook and session
    logbook    = Logbook()
    session_id = logbook.start_session()
    logger.info(f"Session started: {session_id}")

    try:
        if args.demo:
            demo_mode(logbook, session_id)
        else:
            interactive_loop(logbook, session_id)
    finally:
        logbook.end_session(session_id)
        logger.info(f"Session ended: {session_id}")


if __name__ == "__main__":
    main()