"""Microphone capture (simple energy-based auto-stop, no wake-word/VAD
dependency needed) and local speech-to-text via faster-whisper."""
import os
import time

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000
CHUNK_MS = 100
CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_MS / 1000)

SILENCE_RMS_THRESHOLD = float(os.environ.get("ULTRON_SILENCE_THRESHOLD", "0.012"))
SILENCE_DURATION_S = float(os.environ.get("ULTRON_SILENCE_DURATION", "1.2"))
MAX_UTTERANCE_S = float(os.environ.get("ULTRON_MAX_UTTERANCE", "20"))
LISTEN_TIMEOUT_S = float(os.environ.get("ULTRON_LISTEN_TIMEOUT", "8"))

_model = None


def _get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel

        size = os.environ.get("WHISPER_MODEL_SIZE", "base.en")
        device = os.environ.get("WHISPER_DEVICE", "cpu")
        compute_type = os.environ.get("WHISPER_COMPUTE_TYPE", "int8")
        _model = WhisperModel(size, device=device, compute_type=compute_type)
    return _model


def record_utterance():
    """Blocks until speech is detected and then trails off into silence.
    Returns a float32 mono numpy array at 16kHz, or None if nothing was
    said before LISTEN_TIMEOUT_S."""
    chunks = []
    speaking = False
    silence_run_s = 0.0
    elapsed_s = 0.0

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32") as stream:
        while elapsed_s < MAX_UTTERANCE_S:
            data, _ = stream.read(CHUNK_SAMPLES)
            data = data[:, 0]
            rms = float(np.sqrt(np.mean(np.square(data)))) if len(data) else 0.0
            elapsed_s += CHUNK_MS / 1000

            if not speaking:
                if rms > SILENCE_RMS_THRESHOLD:
                    speaking = True
                    chunks.append(data)
                elif elapsed_s > LISTEN_TIMEOUT_S:
                    return None
                continue

            chunks.append(data)
            if rms > SILENCE_RMS_THRESHOLD:
                silence_run_s = 0.0
            else:
                silence_run_s += CHUNK_MS / 1000
                if silence_run_s >= SILENCE_DURATION_S:
                    break

    if not chunks:
        return None
    return np.concatenate(chunks)


def transcribe(audio):
    if audio is None or len(audio) == 0:
        return ""
    model = _get_model()
    segments, _info = model.transcribe(audio, language="en", beam_size=5)
    return " ".join(seg.text.strip() for seg in segments).strip()
