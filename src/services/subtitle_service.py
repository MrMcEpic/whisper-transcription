"""Subtitle export service for SRT and WebVTT formats."""

from typing import Dict, Any, Optional, Callable
from ..utils.timestamps import format_srt_timestamp, format_vtt_timestamp


class SubtitleService:
    """Handles subtitle file export in various formats."""

    @staticmethod
    def export_srt(
        filename: str,
        transcription_result: Dict[str, Any],
        speaker_callback: Optional[Callable[[float], Optional[str]]] = None,
        translation_callback: Optional[Callable[[str], str]] = None
    ):
        """
        Export transcription as SRT subtitle file.

        Args:
            filename: Output file path
            transcription_result: Transcription result dictionary
            speaker_callback: Optional callback to get speaker at timestamp
            translation_callback: Optional callback to translate text
        """
        with open(filename, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(transcription_result['segments'], 1):
                start_time = format_srt_timestamp(segment['start'])
                end_time = format_srt_timestamp(segment['end'])
                text = segment['text'].strip()

                # Translate if callback provided
                if translation_callback:
                    text = translation_callback(text)

                # Add speaker info if available
                speaker_prefix = ""
                if speaker_callback:
                    speaker = speaker_callback(segment['start'])
                    if speaker:
                        speaker_prefix = f"[{speaker}] "

                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{speaker_prefix}{text}\n\n")

    @staticmethod
    def export_vtt(
        filename: str,
        transcription_result: Dict[str, Any],
        speaker_callback: Optional[Callable[[float], Optional[str]]] = None,
        translation_callback: Optional[Callable[[str], str]] = None
    ):
        """
        Export transcription as WebVTT subtitle file.

        Args:
            filename: Output file path
            transcription_result: Transcription result dictionary
            speaker_callback: Optional callback to get speaker at timestamp
            translation_callback: Optional callback to translate text
        """
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("WEBVTT\n\n")

            for segment in transcription_result['segments']:
                start_time = format_vtt_timestamp(segment['start'])
                end_time = format_vtt_timestamp(segment['end'])
                text = segment['text'].strip()

                # Translate if callback provided
                if translation_callback:
                    text = translation_callback(text)

                # Add speaker info if available
                speaker_prefix = ""
                if speaker_callback:
                    speaker = speaker_callback(segment['start'])
                    if speaker:
                        speaker_prefix = f"[{speaker}] "

                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{speaker_prefix}{text}\n\n")
