#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick test script to verify test1.mp4 transcription works.
This script runs a simple transcription test without pytest.

Usage:
    python run_test.py                    # Uses 'base' model (good accuracy)
    python run_test.py --model small      # Uses 'small' model
    python run_test.py --model large-v3   # Uses 'large-v3' model (best accuracy)
"""

import sys
import argparse
from pathlib import Path
import io

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.services import TranscriptionService, DiarizationService
from src.utils import format_timestamp, convert_to_wav, TempFileManager


def main():
    """Run a simple transcription test."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Quick test for Whisper transcription with test1.mp4'
    )
    parser.add_argument(
        '--model',
        type=str,
        default='base',
        choices=['tiny', 'base', 'small', 'medium', 'large', 'large-v2', 'large-v3', 'turbo'],
        help='Whisper model to use (default: base - good balance of speed and accuracy)'
    )
    parser.add_argument(
        '--no-diarization',
        action='store_true',
        help='Skip speaker diarization'
    )

    args = parser.parse_args()

    test_video = Path("test1.mp4")
    expected_output = Path("test2.txt")

    if not test_video.exists():
        print(f"ERROR: {test_video} not found")
        return 1

    if not expected_output.exists():
        print(f"WARNING: {expected_output} not found")

    print("=" * 60)
    print("Whisper Transcription Tool - Quick Test")
    print("=" * 60)

    # Display model info
    model_info = {
        'tiny': '(fastest, lower accuracy)',
        'base': '(good balance)',
        'small': '(better accuracy)',
        'medium': '(high accuracy)',
        'large': '(very high accuracy)',
        'large-v2': '(very high accuracy, v2)',
        'large-v3': '(best accuracy, matches test2.txt)',
        'turbo': '(fast, high accuracy)'
    }
    print(f"\nUsing model: {args.model} {model_info.get(args.model, '')}")

    # Initialize services
    print("\n1. Initializing services...")
    transcription_service = TranscriptionService()
    temp_manager = TempFileManager()

    # Load model
    print(f"2. Loading Whisper model '{args.model}'...")
    print("   (First run will download the model, please wait...)")
    transcription_service.load_model(args.model)
    print("   [OK] Model loaded")

    # Optional: Try diarization
    diarization_result = None
    if args.no_diarization:
        print("\n3. Speaker diarization skipped (--no-diarization flag)")
    elif DiarizationService.is_available():
        print("\n3. Attempting speaker diarization...")
        try:
            diarization_service = DiarizationService()
            diarization_service.load_pipeline()

            # Convert video to audio
            audio_file = convert_to_wav(str(test_video))
            if audio_file and audio_file != str(test_video):
                temp_manager.add(audio_file)

            diarization_result = diarization_service.diarize(audio_file)
            print("   [OK] Speaker diarization complete")
        except Exception as e:
            print(f"   [WARNING] Diarization skipped: {e}")
    else:
        print("\n3. Speaker diarization unavailable (pyannote.audio not installed)")

    # Transcribe
    print("\n4. Transcribing audio...")
    try:
        result = transcription_service.transcribe(
            str(test_video),
            word_timestamps=True,
            verbose=False
        )
        print("   [OK] Transcription complete")
    except Exception as e:
        print(f"   [ERROR] Transcription failed: {e}")
        temp_manager.cleanup()
        return 1

    # Display results
    print("\n" + "=" * 60)
    print("TRANSCRIPTION RESULTS")
    print("=" * 60)

    print(f"\nFull text:\n{result['text']}\n")

    print(f"Number of segments: {len(result['segments'])}")

    if diarization_result:
        speakers = set()
        for turn, _, speaker in diarization_result.itertracks(yield_label=True):
            speakers.add(speaker)
        print(f"Speakers detected: {len(speakers)} ({', '.join(sorted(speakers))})")

    # Show first few segments
    print("\nFirst 3 segments:")
    for i, segment in enumerate(result['segments'][:3], 1):
        start = format_timestamp(segment['start'])
        end = format_timestamp(segment['end'])
        text = segment['text'].strip()

        speaker = None
        if diarization_result:
            # Get speaker at segment start
            for turn, _, spk in diarization_result.itertracks(yield_label=True):
                if turn.start <= segment['start'] <= turn.end:
                    speaker = spk
                    break

        speaker_label = f"[{speaker}] " if speaker else ""
        print(f"\n{i}. [{start} - {end}] {speaker_label}")
        print(f"   {text}")

        # Show word timestamps if available
        if 'words' in segment and len(segment['words']) > 0:
            print(f"   Words: {len(segment['words'])}")

    # Compare with expected output if available
    if expected_output.exists():
        print("\n" + "=" * 60)
        print("COMPARISON WITH EXPECTED OUTPUT")
        print("=" * 60)

        with open(expected_output, 'r', encoding='utf-8') as f:
            expected = f.read()

        # Basic checks
        checks = {
            "Has timestamps": '[0:00:' in expected,
            "Has speaker labels": '[SPEAKER_' in expected,
            "Has word timestamps": '  0:00:' in expected,
            "Has full segments": 'Full segment:' in expected,
        }

        for check, expected_val in checks.items():
            status = "[OK]" if expected_val else "[MISSING]"
            print(f"{status} {check}")

        # Content checks
        expected_lower = expected.lower()
        content_checks = {
            "Contains 'elephant'": 'elephant' in expected_lower,
            "Contains 'trunks'": 'trunks' in expected_lower,
        }

        result_lower = result['text'].lower()
        print("\nContent verification:")
        for check, expected_val in content_checks.items():
            in_expected = "[OK]" if expected_val else "[NO]"
            in_result = "[OK]" if check.split("'")[1] in result_lower else "[NO]"
            print(f"  {check}: Expected={in_expected}, Got={in_result}")

    # Cleanup
    print("\n" + "=" * 60)
    temp_manager.cleanup()
    print("[DONE] Test complete!")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
