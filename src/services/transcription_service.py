"""Whisper transcription service."""

import sys
import io
import re
import whisper
from typing import Optional, Dict, Any, Callable


class TranscriptionService:
    """Handles audio transcription using Whisper models."""

    def __init__(self):
        self.model = None
        self.current_model_name: Optional[str] = None

    def load_model(self, model_name: str):
        """
        Load a Whisper model.

        Args:
            model_name: Name of the Whisper model to load
        """
        if self.model is None or self.current_model_name != model_name:
            self.model = whisper.load_model(model_name)
            self.current_model_name = model_name

    def transcribe(
        self,
        file_path: str,
        language: Optional[str] = None,
        task: str = "transcribe",
        word_timestamps: bool = True,
        verbose: bool = False,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> Dict[str, Any]:
        """
        Transcribe an audio/video file.

        Args:
            file_path: Path to the audio/video file
            language: Language code (None for auto-detect)
            task: Task type ('transcribe' or 'translate')
            word_timestamps: Whether to include word-level timestamps
            verbose: Whether to show verbose output
            progress_callback: Optional callback for progress updates (percentage)

        Returns:
            Transcription result dictionary
        """
        if self.model is None:
            raise ValueError("Model not loaded. Call load_model() first.")

        # Prepare transcription parameters
        params = {
            "word_timestamps": word_timestamps,
            "verbose": verbose
        }

        if language and language != "auto":
            params["language"] = language

        if task:
            params["task"] = task

        # Capture progress if callback provided
        if progress_callback and not verbose:
            progress_capture = ProgressCapture(progress_callback)
            original_stderr = sys.stderr

            try:
                sys.stderr = progress_capture
                result = self.model.transcribe(file_path, **params)
            finally:
                sys.stderr = original_stderr
        else:
            result = self.model.transcribe(file_path, **params)

        return result

    def is_loaded(self) -> bool:
        """Check if a model is currently loaded."""
        return self.model is not None


class ProgressCapture:
    """Captures progress from Whisper's tqdm output."""

    def __init__(self, callback: Callable[[int], None]):
        self.callback = callback
        self.original_stderr = sys.stderr

    def write(self, text: str):
        """Parse tqdm progress and call callback."""
        if '|' in text and '%' in text:
            try:
                percentage_match = re.search(r'(\d+)%', text)
                if percentage_match:
                    percentage = int(percentage_match.group(1))
                    self.callback(percentage)
            except:
                pass

        # Still write to original stderr
        self.original_stderr.write(text)

    def flush(self):
        """Flush the original stderr."""
        self.original_stderr.flush()
