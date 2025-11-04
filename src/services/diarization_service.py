"""Speaker diarization service."""

import torch
from typing import Optional, Any

# Optional import for speaker diarization
try:
    from pyannote.audio import Pipeline
    PYANNOTE_AVAILABLE = True
except ImportError:
    Pipeline = None
    PYANNOTE_AVAILABLE = False

from ..config import HF_TOKEN, DIARIZATION_MODEL, SPEAKER_MATCH_THRESHOLD


class DiarizationService:
    """Handles speaker diarization using pyannote.audio."""

    def __init__(self):
        self.pipeline = None
        self.result = None

    @staticmethod
    def is_available() -> bool:
        """Check if pyannote.audio is available."""
        return PYANNOTE_AVAILABLE

    def load_pipeline(self, use_auth_token: Optional[str] = None):
        """
        Load the diarization pipeline.

        Args:
            use_auth_token: HuggingFace authentication token

        Raises:
            ImportError: If pyannote.audio is not available
            Exception: If pipeline loading fails
        """
        if not PYANNOTE_AVAILABLE:
            raise ImportError("pyannote.audio is not installed")

        token = use_auth_token or HF_TOKEN

        try:
            # Try with token first
            self.pipeline = Pipeline.from_pretrained(
                DIARIZATION_MODEL,
                use_auth_token=token
            )
        except Exception:
            # Fallback to huggingface-cli login
            self.pipeline = Pipeline.from_pretrained(
                DIARIZATION_MODEL,
                use_auth_token=True
            )

        # Move to CUDA if available
        if torch.cuda.is_available():
            self.pipeline = self.pipeline.to(torch.device("cuda"))

    def diarize(self, audio_file: str) -> Any:
        """
        Perform speaker diarization on an audio file.

        Args:
            audio_file: Path to the audio file

        Returns:
            Diarization result object

        Raises:
            ValueError: If pipeline is not loaded
        """
        if self.pipeline is None:
            raise ValueError("Pipeline not loaded. Call load_pipeline() first.")

        self.result = self.pipeline(audio_file)
        return self.result

    def get_speaker_at_time(
        self,
        timestamp: float,
        result: Optional[Any] = None
    ) -> Optional[str]:
        """
        Get the speaker at a specific timestamp.

        Args:
            timestamp: Time in seconds
            result: Diarization result (uses self.result if None)

        Returns:
            Speaker label or None if no speaker found
        """
        diarization_result = result or self.result

        if not diarization_result:
            return None

        # First, try exact match
        for turn, _, speaker in diarization_result.itertracks(yield_label=True):
            if turn.start <= timestamp <= turn.end:
                return speaker

        # If no exact match, find the closest speaker
        closest_speaker = None
        min_distance = float('inf')

        for turn, _, speaker in diarization_result.itertracks(yield_label=True):
            if timestamp < turn.start:
                distance = turn.start - timestamp
            elif timestamp > turn.end:
                distance = timestamp - turn.end
            else:
                return speaker

            if distance < min_distance:
                min_distance = distance
                closest_speaker = speaker

        # Only assign speaker if timestamp is very close
        if min_distance <= SPEAKER_MATCH_THRESHOLD:
            return closest_speaker

        return None

    def is_loaded(self) -> bool:
        """Check if pipeline is loaded."""
        return self.pipeline is not None
