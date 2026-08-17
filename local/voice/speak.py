"""Text-to-speech. Default engine is pyttsx3 (pure pip install, uses the
OS's own TTS voices - works immediately with zero model downloads). Set
TTS_ENGINE=piper for better-quality fully-local neural TTS once you've
installed the `piper` CLI and a voice model (see local/README.md)."""
import os
import subprocess
import tempfile
import wave

TTS_ENGINE = os.environ.get("TTS_ENGINE", "pyttsx3")
PIPER_EXE = os.environ.get("PIPER_EXE", "piper")
PIPER_MODEL = os.environ.get("PIPER_MODEL")  # path to a .onnx voice model


def speak(text):
    if not text or not text.strip():
        return
    if TTS_ENGINE == "piper":
        try:
            _speak_piper(text)
            return
        except Exception as e:
            print(f"[speak] piper failed ({e}), falling back to pyttsx3")
    _speak_pyttsx3(text)


def _speak_pyttsx3(text):
    import pyttsx3

    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()


def _speak_piper(text):
    if not PIPER_MODEL:
        raise RuntimeError("PIPER_MODEL not set")

    import numpy as np
    import sounddevice as sd

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        wav_path = tmp.name

    try:
        proc = subprocess.run(
            [PIPER_EXE, "--model", PIPER_MODEL, "--output_file", wav_path],
            input=text.encode("utf-8"),
            capture_output=True,
            timeout=30,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.decode(errors="ignore"))

        with wave.open(wav_path, "rb") as wf:
            frames = wf.readframes(wf.getnframes())
            audio = np.frombuffer(frames, dtype="int16")
            sd.play(audio, samplerate=wf.getframerate())
            sd.wait()
    finally:
        try:
            os.remove(wav_path)
        except OSError:
            pass
