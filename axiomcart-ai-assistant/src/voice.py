"""
Voice I/O layer.

VoiceRecorder – microphone → WAV → Whisper STT → text
VoiceSpeaker  – text → OpenAI TTS → playback
"""

from __future__ import annotations

import io
import os
import tempfile
import time
import uuid

import numpy as np
import sounddevice as sd
import soundfile as sf

from src.config import get_logger, openai_client

logger = get_logger("voice")


# ═══════════════════════════════════════════════════════════
#  Speech-to-Text
# ═══════════════════════════════════════════════════════════

class VoiceRecorder:
    """Record from the microphone and transcribe with Whisper."""

    def __init__(self, sample_rate: int = 16_000):
        self.sample_rate = sample_rate

    def record(self, duration: int = 5, countdown: bool = True) -> np.ndarray:
        """Record *duration* seconds of mono audio."""
        if countdown:
            for i in range(3, 0, -1):
                logger.info("Recording starts in %d …", i)
                time.sleep(1)

        logger.info("Recording for %d s — speak now!", duration)
        audio = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
        )
        sd.wait()
        logger.info("Recording complete")
        return audio

    def transcribe(self, audio: np.ndarray, language: str = "en") -> str:
        """Send audio to Whisper and return the transcript."""
        buf = io.BytesIO()
        sf.write(buf, audio, self.sample_rate, format="WAV")
        buf.seek(0)
        buf.name = "recording.wav"

        try:
            result = openai_client.audio.transcriptions.create(
                model="whisper-1", file=buf, language=language,
            )
            logger.info("Transcription: %r", result.text)
            return result.text
        except Exception:
            logger.exception("Whisper transcription failed")
            return ""

    def record_and_transcribe(self, duration: int = 5) -> tuple[str, str]:
        """Full pipeline: record → save WAV → transcribe.

        Returns (wav_path, transcript).
        """
        audio = self.record(duration)
        wav_path = os.path.join(tempfile.gettempdir(), f"rec_{uuid.uuid4().hex[:8]}.wav")
        sf.write(wav_path, audio, self.sample_rate)
        text = self.transcribe(audio)
        return wav_path, text


# ═══════════════════════════════════════════════════════════
#  Text-to-Speech
# ═══════════════════════════════════════════════════════════

VOICE_OPTIONS = {
    "alloy":   "Neutral, professional",
    "echo":    "Male, clear and steady",
    "fable":   "British accent, expressive",
    "onyx":    "Deep male, authoritative",
    "nova":    "Female, warm and friendly",
    "shimmer": "Female, soft and gentle",
}


class VoiceSpeaker:
    """Convert text to speech and play it back."""

    def __init__(self, voice: str = "nova", speed: float = 1.0):
        self.voice = voice
        self.speed = speed
        self._out_dir = tempfile.gettempdir()

    def synthesise(self, text: str) -> str:
        """Generate an MP3 file and return its path. Each call gets a
        unique filename so previous responses are never overwritten."""
        out_path = os.path.join(self._out_dir, f"tts_{uuid.uuid4().hex[:8]}.mp3")
        try:
            resp = openai_client.audio.speech.create(
                model="tts-1", voice=self.voice, input=text, speed=self.speed,
            )
            resp.stream_to_file(out_path)
            logger.info("TTS saved → %s", out_path)
            return out_path
        except Exception:
            logger.exception("TTS synthesis failed")
            return ""

    def play(self, audio_file: str) -> None:
        """Play an audio file through the default output device."""
        try:
            data, sr = sf.read(audio_file)
            sd.play(data, sr)
            sd.wait()
        except Exception:
            logger.exception("Audio playback failed")

    def speak(self, text: str, play: bool = True) -> str:
        """Synthesise *text* and optionally play it. Returns the file path."""
        logger.info("Agent says: %s", text[:120])
        path = self.synthesise(text)
        if play and path:
            self.play(path)
        return path
