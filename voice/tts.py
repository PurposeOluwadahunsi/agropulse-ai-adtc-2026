"""
voice/tts.py

Offline Text-to-Speech using pyttsx3.
Uses Windows SAPI voices — no internet, no external API.

Install: pip install pyttsx3
"""

from __future__ import annotations

import logging
import re
import threading
from typing import Optional

logger = logging.getLogger(__name__)

_engine = None
_lock   = threading.Lock()


def _get_engine():
    """Initialise pyttsx3 engine once and return it."""
    global _engine
    if _engine is not None:
        return _engine
    try:
        import pyttsx3
        _engine = pyttsx3.init()
        _engine.setProperty("rate",   160)   # words per minute
        _engine.setProperty("volume", 0.9)
        logger.info("TTS engine initialised.")
        return _engine
    except ImportError:
        raise RuntimeError(
            "pyttsx3 is not installed. Run: pip install pyttsx3"
        )
    except Exception as exc:
        raise RuntimeError(f"TTS engine failed to initialise: {exc}") from exc


def _clean_for_speech(text: str) -> str:
    """
    Strip markdown, HTML tags, and section headers before speaking.
    Keeps the response clear and natural when read aloud.
    """
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Remove markdown bold/italic
    text = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", text)
    # Replace section headers like "ASSESSMENT" with a pause cue
    text = re.sub(r"\b([A-Z]{4,})\b", r". \1.", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def speak(text: str, block: bool = True) -> Optional[str]:
    """
    Speak text aloud using the local TTS engine.

    Args:
        text:  Text to speak. HTML and markdown are stripped automatically.
        block: If True, wait for speech to finish before returning.
               If False, speak in a background thread.

    Returns:
        None on success, error message string on failure.
    """
    if not text or not text.strip():
        return "No text to speak."

    cleaned = _clean_for_speech(text)
    # Limit to first 800 chars to avoid very long readings
    if len(cleaned) > 800:
        cleaned = cleaned[:800] + ". End of summary."

    try:
        engine = _get_engine()
        with _lock:
            if block:
                engine.say(cleaned)
                engine.runAndWait()
            else:
                def _run():
                    engine.say(cleaned)
                    engine.runAndWait()
                threading.Thread(target=_run, daemon=True).start()
        return None
    except RuntimeError as exc:
        return str(exc)
    except Exception as exc:
        logger.error(f"TTS speak failed: {exc}", exc_info=True)
        return "Voice output failed. Please read the response on screen."


def stop() -> None:
    """Stop any currently playing speech."""
    global _engine
    if _engine:
        try:
            _engine.stop()
        except Exception:
            pass


def is_available() -> bool:
    """Return True if TTS is available on this system."""
    try:
        _get_engine()
        return True
    except RuntimeError:
        return False