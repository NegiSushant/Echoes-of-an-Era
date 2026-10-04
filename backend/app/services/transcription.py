"""
transcription.py — Speech-to-Text service using faster-whisper.

Pipeline: Audio file → faster-whisper (large-v3) → {
    full_transcript,
    segments: [{segment_index, start_time, end_time, text, avg_logprob}],
    detected_language,
    language_probability,
    model_used,
    duration_processed
}

Language support: Hindi, Hinglish, English (and any Whisper-supported language).
Original audio is NEVER modified — this is strictly read-only processing.
"""

import os
import time
from typing import List, Dict, Any, Optional

# Suppress HuggingFace symlink warnings on Windows
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

# Fix PyAV 14+ compatibility with faster-whisper (metadata_errors argument removed in newer PyAV)
try:
    import av
    _orig_av_open = av.open
    def _safe_av_open(*args, **kwargs):
        kwargs.pop("metadata_errors", None)
        return _orig_av_open(*args, **kwargs)
    av.open = _safe_av_open
except Exception:
    pass

from dotenv import load_dotenv
load_dotenv()

WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "tiny")
DEVICE = os.getenv("DEVICE", "cpu")


class TranscriptionResult:
    """Structured result from a transcription run."""

    def __init__(
        self,
        segments: List[Dict[str, Any]],
        full_transcript: str,
        detected_language: str,
        language_probability: float,
        model_used: str,
        duration_processed: float,
    ):
        self.segments = segments
        self.full_transcript = full_transcript
        self.detected_language = detected_language
        self.language_probability = language_probability
        self.model_used = model_used
        self.duration_processed = duration_processed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "full_transcript": self.full_transcript,
            "segments": self.segments,
            "detected_language": self.detected_language,
            "language_probability": round(self.language_probability, 4) if self.language_probability is not None else 0.0,
            "model_used": self.model_used,
            "duration_processed": round(self.duration_processed, 2),
            "segment_count": len(self.segments),
        }


class TranscriptionService:
    """
    Singleton wrapper around faster-whisper WhisperModel.

    Model is loaded lazily on first use to avoid blocking app startup.
    Supports Hindi, Hinglish, English, and all other Whisper languages.
    Preserves verbatim timestamps without ever modifying the original audio file.
    """

    def __init__(self, model_size: str = None, device: str = None):
        self.model_size = model_size or WHISPER_MODEL_SIZE
        self.device = device or DEVICE
        self._model = None
        self._active_model_size = None

    def _get_model(self, requested_size: Optional[str] = None):
        """Lazy-load the WhisperModel (int8 on CPU, float16 on CUDA)."""
        target_size = requested_size if (isinstance(requested_size, str) and requested_size.strip()) else self.model_size
        if not isinstance(target_size, str) or not target_size.strip():
            target_size = "tiny"

        if self._model is not None and self._active_model_size == target_size:
            return self._model

        from faster_whisper import WhisperModel

        compute_type = "float16" if self.device == "cuda" else "int8"
        print(f"[STT] Loading faster-whisper '{target_size}' on {self.device} ({compute_type})...")

        try:
            self._model = WhisperModel(
                target_size,
                device=self.device,
                compute_type=compute_type,
            )
            self._active_model_size = target_size
            print(f"[STT] Model '{target_size}' loaded successfully.")
        except Exception as e:
            print(f"[STT Warning] Could not load model '{target_size}': {e}")
            # If target model fails to download (e.g. rate limit / network), fallback to large-v3-turbo or tiny if available
            fallback_models = ["large-v3-turbo", "tiny"]
            for fb in fallback_models:
                if fb == target_size:
                    continue
                try:
                    print(f"[STT] Attempting fallback to '{fb}'...")
                    self._model = WhisperModel(
                        fb,
                        device=self.device,
                        compute_type=compute_type,
                    )
                    self._active_model_size = fb
                    print(f"[STT] Fallback model '{fb}' loaded successfully.")
                    break
                except Exception as fb_err:
                    print(f"[STT Error] Fallback to '{fb}' also failed: {fb_err}")
            
            if self._model is None:
                raise RuntimeError(f"Failed to load Whisper model '{target_size}' and fallbacks: {e}") from e

        return self._model

    def transcribe(
        self,
        audio_file_path: str,
        model_size: Optional[str] = None,
        language: Optional[str] = None,
        initial_prompt: Optional[str] = None,
    ) -> TranscriptionResult:
        """
        Transcribe an audio file with accurate timestamps and language detection.
        Original audio file is strictly preserved and never modified.

        Parameters tuned for grandfather recordings (Hindi / Hinglish / English):
        - beam_size=5            : balanced accuracy/speed
        - vad_filter=True        : removes background noise/silence
        - condition_on_previous  : ensures context continuity across pauses
        - initial_prompt         : primes vocabulary for Indian/family elder speech
        """
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

        clean_model_size = model_size if (isinstance(model_size, str) and model_size.strip()) else None
        clean_language = language if (isinstance(language, str) and language.strip()) else None

        model = self._get_model(clean_model_size)
        used_model_name = self._active_model_size or (clean_model_size or self.model_size)

        t_start = time.time()

        # Context prime for grandfather storytelling in Hindi / Hinglish / English
        prompt_text = initial_prompt or (
            "Grandfather sharing memories, family stories, and life advice. "
            "Humare parivar ki yaadein, bachpan ke kisse, aur anubhav."
        )

        segments_generator, info = model.transcribe(
            audio_file_path,
            beam_size=5,
            best_of=5,
            language=clean_language,  # None = auto-detect Hindi, English, etc.
            initial_prompt=prompt_text,
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=300,
                speech_pad_ms=200,
            ),
            no_speech_threshold=0.4,
            compression_ratio_threshold=3.0,
            log_prob_threshold=-1.2,
            condition_on_previous_text=True,
            word_timestamps=False,
        )

        segments: List[Dict[str, Any]] = []
        for idx, seg in enumerate(segments_generator):
            clean_text = seg.text.strip()
            if clean_text:
                segments.append(
                    {
                        "segment_index": idx,
                        "start_time": round(float(seg.start), 3),
                        "end_time": round(float(seg.end), 3),
                        "text": clean_text,
                        "avg_logprob": round(float(seg.avg_logprob), 4),
                        "no_speech_prob": round(float(seg.no_speech_prob), 4),
                    }
                )

        elapsed = time.time() - t_start

        # Assemble full verbatim transcript
        full_transcript = " ".join(s["text"] for s in segments if s["text"]).strip()

        return TranscriptionResult(
            segments=segments,
            full_transcript=full_transcript,
            detected_language=info.language,
            language_probability=info.language_probability,
            model_used=used_model_name,
            duration_processed=elapsed,
        )


# Module-level singleton
transcription_service = TranscriptionService()
