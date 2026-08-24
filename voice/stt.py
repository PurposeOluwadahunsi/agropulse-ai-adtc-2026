
from __future__ import annotations

import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL", "base")

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"

_whisper_model = None


# ---------------------------------------------------------------------
# Whisper
# ---------------------------------------------------------------------


def _check_ffmpeg() -> None:
    """
    Ensure FFmpeg exists before Whisper is used.
    """
    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "FFmpeg is not installed or not on PATH.\n"
            "Install FFmpeg and restart your terminal."
        )


def _get_model():
    """
    Load Whisper once.
    """

    global _whisper_model

    if _whisper_model is not None:
        return _whisper_model

    _check_ffmpeg()

    try:
        import whisper
    except ImportError:
        raise RuntimeError(
            "openai-whisper is not installed.\n"
            "Run:\n"
            "pip install openai-whisper"
        )

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Loading Whisper model (%s)...", WHISPER_MODEL_SIZE)

    _whisper_model = whisper.load_model(
        WHISPER_MODEL_SIZE,
        download_root=str(MODELS_DIR),
    )

    logger.info("Whisper loaded.")

    return _whisper_model


# ---------------------------------------------------------------------
# Microphone
# ---------------------------------------------------------------------


def _device_priority(name: str) -> int:
    """
    Score microphones.

    Higher score = more preferred.
    """

    n = name.lower()

    score = 0

    if "microphone" in n:
        score += 100

    if "array" in n:
        score += 40

    if "usb" in n:
        score += 25

    if "headset" in n:
        score += 15

    if "bluetooth" in n:
        score -= 20

    if "stereo mix" in n:
        score -= 1000

    return score


def _candidate_devices(sd):

    devices = []

    for idx, dev in enumerate(sd.query_devices()):

        if dev["max_input_channels"] < 1:
            continue

        devices.append(
            (
                _device_priority(dev["name"]),
                idx,
                dev,
            )
        )

    devices.sort(reverse=True)

    return devices


def _find_input_device(sd):
    """
    Find the best working microphone.

    Priority:
        1. Windows WASAPI
        2. Windows DirectSound
        3. MME
        4. Windows WDM-KS

    Returns:
        (device_id, sample_rate)
    """

    import numpy as np

    PRIORITY = {
        "Windows WASAPI": 0,
        "Windows DirectSound": 1,
        "MME": 2,
        "Windows WDM-KS": 3,
    }

    candidates = []

    # Collect all usable input devices
    for device_id, dev in enumerate(sd.query_devices()):

        if dev["max_input_channels"] < 1:
            continue

        api_name = sd.query_hostapis(dev["hostapi"])["name"]

        candidates.append(
            (
                PRIORITY.get(api_name, 999),
                device_id,
                api_name,
                dev,
            )
        )

    # Prefer WASAPI > DirectSound > MME > WDM-KS
    candidates.sort(key=lambda x: x[0])

    for _, device_id, api_name, dev in candidates:

        sample_rate = int(dev["default_samplerate"])

        try:
            print(
                f"Testing device {device_id}: "
                f"{dev['name']} "
                f"({api_name})"
            )

            audio = sd.rec(
                frames=int(sample_rate * 0.5),   # half-second test
                samplerate=sample_rate,
                channels=1,
                dtype="float32",
                device=device_id,
                blocking=True,
            )

            audio = np.asarray(audio)

            # Reject corrupted buffers
            if np.isnan(audio).any():
                print(" -> rejected (NaN)")
                continue

            if np.isinf(audio).any():
                print(" -> rejected (Inf)")
                continue

            peak = float(np.max(np.abs(audio)))

            print(f" -> peak={peak:.6f}")

            # Reject silent microphones
            if peak < 1e-4:
                print(" -> rejected (silence)")
                continue

            print(
                f"\nSelected microphone:\n"
                f"  Device : {device_id}\n"
                f"  Name   : {dev['name']}\n"
                f"  API    : {api_name}\n"
                f"  Rate   : {sample_rate}\n"
            )

            return device_id, sample_rate

        except Exception as e:
            print(f" -> failed ({e})")

    raise RuntimeError(
        "No usable microphone found.\n"
        "Please connect a microphone or enable microphone permissions."
    )


# ---------------------------------------------------------------------
# Recording
# ---------------------------------------------------------------------


def record_audio(duration_seconds: int = 8) -> str:

    try:
        import sounddevice as sd
        from scipy.io.wavfile import write as wav_write

    except ImportError as exc:

        raise RuntimeError(
            "Missing dependencies.\n"
            "Run:\n"
            "pip install sounddevice scipy"
        ) from exc

    device_id, sample_rate  = _find_input_device(sd)
    print("=" * 50)
    print("Using device:", device_id)
    print(sd.query_devices(device_id)["name"])
    print("Sample rate:", sample_rate)
    print("=" * 50)

    logger.info(
        "Recording %d seconds using '%s'",
        duration_seconds,
    )

    frames = int(duration_seconds * sample_rate)

    try:

        audio = sd.rec(
            frames,
            samplerate=sample_rate,
            channels=1,
            dtype="float32",
            device=device_id,
            blocking=True,
        )

    except Exception as exc:

        raise RuntimeError(
            f"Recording failed on '{device_id}'.\n{exc}"
        ) from exc

    audio = np.clip(audio, -1.0, 1.0)

    audio = (audio * 32767).astype(np.int16)

    tmp = tempfile.NamedTemporaryFile(
        suffix=".wav",
        delete=False,
    )

    wav_write(
        tmp.name,
        sample_rate,
        audio,
    )

    logger.info("Saved recording to %s", tmp.name)

    return tmp.name
# ---------------------------------------------------------------------
# Transcription
# ---------------------------------------------------------------------


def transcribe(
    wav_path: str,
    language: str = "en",
) -> str:
    """
    Transcribe a WAV file using local Whisper.
    """

    path = Path(wav_path)

    if not path.exists():
        raise RuntimeError(f"Audio file not found: {wav_path}")

    model = _get_model()

    lang_map = {
        "en": "english",
        "yo": "yoruba",
        "ig": "igbo",
        "ha": "hausa",
    }

    whisper_language = lang_map.get(language, "english")

    logger.info(
        "Transcribing using language '%s'...",
        whisper_language,
    )

    try:

        result = model.transcribe(
            str(path),
            language=whisper_language,
            fp16=False,
            verbose=False,
        )

        text = result.get("text", "").strip()

        logger.info("Transcription complete.")

        return text

    except Exception as exc:

        raise RuntimeError(
            f"Whisper transcription failed.\n{exc}"
        ) from exc

#    finally:

#        try:
#            path.unlink(missing_ok=True)
#        except Exception:
#            pass


# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------


def record_and_transcribe(
    duration_seconds: int = 8,
    language: str = "en",
) -> tuple[str, Optional[str]]:
    """
    Record audio then transcribe it.

    Returns
    -------
    (text, error)

    Success:
        ("hello world", None)

    Failure:
        ("", "error message")
    """

    try:

        wav = record_audio(duration_seconds)
        print(f"WAV saved at: {wav}")
        text = transcribe(
            wav,
            language,
        )

        if not text:

            return (
                "",
                "No speech detected. Please try again.",
            )

        return (
            text,
            None,
        )

    except RuntimeError as exc:

        logger.error(
            "Speech-to-text failed",
            exc_info=True,
        )

        return (
            "",
            str(exc),
        )

    except Exception as exc:

        logger.exception(
            "Unexpected STT error"
        )

        return (
            "",
            f"Unexpected error: {exc}",
        )


# ---------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------


def list_input_devices() -> list[dict]:
    """
    Return all available microphones.
    """

    try:

        import sounddevice as sd

        devices = []

        for i, dev in enumerate(sd.query_devices()):

            if dev["max_input_channels"] < 1:
                continue

            host = sd.query_hostapis(
                dev["hostapi"]
            )["name"]

            devices.append(
                {
                    "id": i,
                    "name": dev["name"],
                    "hostapi": host,
                    "channels": dev["max_input_channels"],
                    "default_samplerate": int(
                        dev["default_samplerate"]
                    ),
                }
            )

        return devices

    except Exception:

        return []


__all__ = [
    "record_audio",
    "transcribe",
    "record_and_transcribe",
    "list_input_devices",
]