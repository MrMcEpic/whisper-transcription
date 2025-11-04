"""Command-line interface for the Whisper Transcription Tool."""

import argparse
import sys
from typing import Optional

from .services import (
    TranscriptionService,
    DiarizationService,
    TranslationService,
    SubtitleService
)
from .utils import format_timestamp, file_exists, convert_to_wav, TempFileManager
from .config import WHISPER_MODELS, DEFAULT_MODEL


class CLI:
    """Command-line interface handler."""

    def __init__(self, args):
        self.args = args
        self.transcription_service = TranscriptionService()
        self.diarization_service = DiarizationService()
        self.translation_service = TranslationService()
        self.subtitle_service = SubtitleService()
        self.temp_manager = TempFileManager()

    def run(self) -> int:
        """
        Run the CLI transcription process.

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        if not file_exists(self.args.input):
            print(f"Error: Input file '{self.args.input}' does not exist.")
            return 1

        try:
            # Load Whisper model
            print(f"Loading Whisper model: {self.args.model}")
            self.transcription_service.load_model(self.args.model)

            # Setup diarization if requested
            diarization_result = None
            if self.args.speaker_diarization:
                diarization_result = self._setup_diarization()

            # Transcribe
            print("Processing audio...")
            result = self._transcribe()

            # Generate output
            output_text = self._format_output(result, diarization_result)

            # Export subtitles
            self._export_subtitles(result, diarization_result)

            # Save or print transcript
            if self.args.output:
                with open(self.args.output, 'w', encoding='utf-8') as f:
                    f.write(output_text)
                print(f"\nTranscript saved to: {self.args.output}")
            elif not self._has_subtitle_exports():
                print("\n" + "=" * 50)
                print("TRANSCRIPT:")
                print("=" * 50)
                print(output_text)

            return 0

        except Exception as e:
            print(f"Error: {e}")
            return 1

        finally:
            self.temp_manager.cleanup()

    def _setup_diarization(self) -> Optional[any]:
        """Setup and perform speaker diarization."""
        if not DiarizationService.is_available():
            print("Warning: Speaker diarization unavailable (pyannote.audio not installed)")
            return None

        try:
            print("Loading speaker diarization model...")
            self.diarization_service.load_pipeline()

            print("Performing speaker diarization...")
            # Convert file if needed
            diarization_file = convert_to_wav(self.args.input)
            if diarization_file and diarization_file != self.args.input:
                self.temp_manager.add(diarization_file)

            if diarization_file:
                return self.diarization_service.diarize(diarization_file)
            else:
                print("Warning: Could not convert file for diarization")
                return None

        except Exception as e:
            print(f"Warning: Speaker diarization failed: {e}")
            return None

    def _transcribe(self):
        """Perform transcription."""
        # Prepare parameters
        language = self.args.language if self.args.language != "auto" else None
        task = "translate" if self.args.translate else "transcribe"

        # Transcribe with progress
        return self.transcription_service.transcribe(
            self.args.input,
            language=language,
            task=task,
            word_timestamps=self.args.word_timestamps,
            verbose=True
        )

    def _format_output(self, result, diarization_result) -> str:
        """Format transcription output based on options."""
        output_lines = []

        if self.args.clean_format:
            for segment in result['segments']:
                start_time = format_timestamp(segment['start'])
                end_time = format_timestamp(segment['end'])
                text = ' '.join(segment['text'].strip().split())

                speaker = self._get_speaker(segment['start'], diarization_result)
                speaker_prefix = f"[{speaker}] " if speaker else ""

                output_lines.append(f"[{start_time} - {end_time}] {speaker_prefix}{text}")

        elif self.args.timestamps and 'segments' in result:
            for segment in result['segments']:
                start_time = format_timestamp(segment['start'])
                end_time = format_timestamp(segment['end'])
                text = segment['text'].strip()

                speaker = self._get_speaker(segment['start'], diarization_result)
                speaker_prefix = f"[{speaker}] " if speaker else ""

                output_lines.append(f"[{start_time} - {end_time}] {speaker_prefix}{text}")
        else:
            output_lines.append(result['text'])

        return '\n'.join(output_lines)

    def _get_speaker(self, timestamp: float, diarization_result) -> Optional[str]:
        """Get speaker at timestamp."""
        if self.args.speaker_diarization and diarization_result:
            return self.diarization_service.get_speaker_at_time(timestamp, diarization_result)
        return None

    def _export_subtitles(self, result, diarization_result):
        """Export subtitle files if requested."""
        speaker_callback = lambda t: self._get_speaker(t, diarization_result)

        # Regular subtitles
        if self.args.export_srt:
            self.subtitle_service.export_srt(
                self.args.export_srt,
                result,
                speaker_callback=speaker_callback
            )
            print(f"\nSRT subtitles exported to: {self.args.export_srt}")

        if self.args.export_vtt:
            self.subtitle_service.export_vtt(
                self.args.export_vtt,
                result,
                speaker_callback=speaker_callback
            )
            print(f"\nWebVTT subtitles exported to: {self.args.export_vtt}")

        # Translated subtitles
        if self.args.export_srt_translated:
            if not TranslationService.is_available():
                print("Warning: Google Translate library not available.")
                return

            print(f"\nTranslating SRT subtitles to {self.args.subtitle_language}...")
            translation_callback = lambda t: self.translation_service.translate(
                t, self.args.subtitle_language
            )

            self.subtitle_service.export_srt(
                self.args.export_srt_translated,
                result,
                speaker_callback=speaker_callback,
                translation_callback=translation_callback
            )
            print(f"Translated SRT subtitles exported to: {self.args.export_srt_translated}")

        if self.args.export_vtt_translated:
            if not TranslationService.is_available():
                print("Warning: Google Translate library not available.")
                return

            print(f"\nTranslating WebVTT subtitles to {self.args.subtitle_language}...")
            translation_callback = lambda t: self.translation_service.translate(
                t, self.args.subtitle_language
            )

            self.subtitle_service.export_vtt(
                self.args.export_vtt_translated,
                result,
                speaker_callback=speaker_callback,
                translation_callback=translation_callback
            )
            print(f"Translated WebVTT subtitles exported to: {self.args.export_vtt_translated}")

    def _has_subtitle_exports(self) -> bool:
        """Check if any subtitle export was requested."""
        return bool(
            self.args.export_srt or
            self.args.export_vtt or
            self.args.export_srt_translated or
            self.args.export_vtt_translated
        )


def create_cli_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description='Whisper Transcription Tool with Speaker Diarization'
    )

    parser.add_argument('--cli', action='store_true', help='Run in CLI mode')
    parser.add_argument('--input', type=str, help='Input audio/video file')
    parser.add_argument(
        '--model', type=str, default=DEFAULT_MODEL,
        choices=WHISPER_MODELS,
        help='Whisper model to use'
    )
    parser.add_argument('--output', type=str, help='Output file path')
    parser.add_argument('--no-timestamps', action='store_true', help='Disable timestamps')
    parser.add_argument('--no-word-timestamps', action='store_true',
                        help='Disable word-level timestamps')
    parser.add_argument('--no-speaker-diarization', action='store_true',
                        help='Disable speaker diarization')
    parser.add_argument('--clean-format', action='store_true',
                        help='Use clean segment format only')
    parser.add_argument('--language', type=str, default='auto',
                        help='Source language (auto for auto-detect)')
    parser.add_argument('--translate', action='store_true',
                        help='Translate to English')
    parser.add_argument('--target-language', type=str, default='en',
                        help='Target language for translation (currently only "en" supported)')
    parser.add_argument('--export-srt', type=str,
                        help='Export as SRT subtitle file to specified path')
    parser.add_argument('--export-vtt', type=str,
                        help='Export as WebVTT subtitle file to specified path')
    parser.add_argument('--export-srt-translated', type=str,
                        help='Export as translated SRT subtitle file to specified path')
    parser.add_argument('--export-vtt-translated', type=str,
                        help='Export as translated WebVTT subtitle file to specified path')
    parser.add_argument('--subtitle-language', type=str, default='es',
                        help='Target language for subtitle translation (default: es for Spanish)')

    return parser


def run_cli_mode(args) -> int:
    """Run in CLI mode."""
    if not args.input:
        print("Error: --input is required in CLI mode")
        return 1

    # Set boolean flags correctly
    args.timestamps = not args.no_timestamps
    args.word_timestamps = not args.no_word_timestamps
    args.speaker_diarization = not args.no_speaker_diarization

    cli = CLI(args)
    return cli.run()
