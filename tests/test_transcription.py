"""Test cases for transcription functionality using test1.mp4 and test2.txt."""

import pytest
import os
import re
from pathlib import Path

from src.services import TranscriptionService, DiarizationService
from src.utils import format_timestamp


# Test file paths
TEST_VIDEO = Path(__file__).parent.parent / "test1.mp4"
EXPECTED_OUTPUT = Path(__file__).parent.parent / "test2.txt"


@pytest.fixture(scope="module")
def transcription_service():
    """Create a transcription service instance."""
    service = TranscriptionService()
    # Use large-v3 for best accuracy matching test2.txt
    # Note: First run will download the model (~3GB)
    service.load_model("large-v3")
    return service


@pytest.fixture(scope="module")
def diarization_service():
    """Create a diarization service instance."""
    if not DiarizationService.is_available():
        pytest.skip("Speaker diarization not available (pyannote.audio not installed)")

    service = DiarizationService()
    try:
        service.load_pipeline()
        return service
    except Exception as e:
        pytest.skip(f"Could not load diarization pipeline: {e}")


@pytest.fixture(scope="module")
def transcription_result(transcription_service):
    """Transcribe test1.mp4 once for all tests."""
    if not TEST_VIDEO.exists():
        pytest.skip(f"Test video not found: {TEST_VIDEO}")

    result = transcription_service.transcribe(
        str(TEST_VIDEO),
        word_timestamps=True,
        verbose=False
    )
    return result


@pytest.fixture(scope="module")
def diarization_result(diarization_service):
    """Perform diarization on test1.mp4 once for all tests."""
    if not TEST_VIDEO.exists():
        pytest.skip(f"Test video not found: {TEST_VIDEO}")

    # For video files, we need to extract audio first
    from src.utils import convert_to_wav, TempFileManager

    temp_manager = TempFileManager()
    audio_file = convert_to_wav(str(TEST_VIDEO))

    if audio_file and audio_file != str(TEST_VIDEO):
        temp_manager.add(audio_file)

    try:
        result = diarization_service.diarize(audio_file)
        return result
    finally:
        temp_manager.cleanup()


@pytest.fixture
def expected_output():
    """Load expected output from test2.txt."""
    if not EXPECTED_OUTPUT.exists():
        pytest.skip(f"Expected output not found: {EXPECTED_OUTPUT}")

    with open(EXPECTED_OUTPUT, 'r', encoding='utf-8') as f:
        return f.read()


class TestTranscriptionService:
    """Test the TranscriptionService with test1.mp4."""

    def test_service_loads_model(self, transcription_service):
        """Test that the service loads a model successfully."""
        assert transcription_service.is_loaded()
        assert transcription_service.current_model_name == "large-v3"

    def test_transcription_has_segments(self, transcription_result):
        """Test that transcription result contains segments."""
        assert 'segments' in transcription_result
        assert len(transcription_result['segments']) > 0

    def test_transcription_has_text(self, transcription_result):
        """Test that transcription result contains full text."""
        assert 'text' in transcription_result
        assert len(transcription_result['text']) > 0

    def test_segments_have_timestamps(self, transcription_result):
        """Test that segments have start and end timestamps."""
        for segment in transcription_result['segments']:
            assert 'start' in segment
            assert 'end' in segment
            assert segment['start'] < segment['end']

    def test_segments_have_word_timestamps(self, transcription_result):
        """Test that segments have word-level timestamps."""
        for segment in transcription_result['segments']:
            if 'words' in segment:  # Some segments might not have words
                assert len(segment['words']) > 0
                for word in segment['words']:
                    assert 'word' in word
                    assert 'start' in word
                    assert 'end' in word

    def test_transcription_contains_expected_phrases(self, transcription_result):
        """Test that transcription contains expected phrases from the video."""
        full_text = transcription_result['text'].lower()

        # Check for key phrases we expect in the elephant video
        expected_phrases = [
            "elephant",
            "trunk",
            "cool"
        ]

        for phrase in expected_phrases:
            assert phrase in full_text, f"Expected phrase '{phrase}' not found in transcription"


class TestDiarizationService:
    """Test the DiarizationService with test1.mp4."""

    def test_diarization_result_exists(self, diarization_result):
        """Test that diarization produces a result."""
        assert diarization_result is not None

    def test_diarization_has_speakers(self, diarization_result, diarization_service):
        """Test that diarization identifies speakers."""
        speakers = set()
        for turn, _, speaker in diarization_result.itertracks(yield_label=True):
            speakers.add(speaker)

        # The test video should have at least 1 speaker
        assert len(speakers) >= 1

    def test_get_speaker_at_time(self, diarization_result, diarization_service):
        """Test that we can get speaker at specific timestamps."""
        # Test at the beginning (around 0.5 seconds)
        speaker = diarization_service.get_speaker_at_time(0.5, diarization_result)
        assert speaker is not None
        assert speaker.startswith("SPEAKER_")


class TestFullTranscriptionWithDiarization:
    """Test full transcription with speaker diarization matching test2.txt."""

    def test_output_format_matches_expected(
        self,
        transcription_result,
        diarization_result,
        diarization_service,
        expected_output
    ):
        """Test that the output format matches test2.txt structure."""
        # Generate output in the same format as test2.txt
        output_lines = []

        for segment in transcription_result['segments']:
            start_time = format_timestamp(segment['start'])
            end_time = format_timestamp(segment['end'])
            text = segment['text'].strip()

            # Get speaker for this segment
            speaker = diarization_service.get_speaker_at_time(segment['start'], diarization_result)
            speaker_prefix = f"[{speaker}] " if speaker else ""

            # Add segment header
            output_lines.append(f"[{start_time} - {end_time}] {speaker_prefix}")

            # Add word-level timestamps if available
            if 'words' in segment:
                for word in segment['words']:
                    word_start = format_timestamp(word['start'])
                    word_end = format_timestamp(word['end'])
                    word_text = word['word']

                    # Get speaker for this word
                    word_speaker = diarization_service.get_speaker_at_time(word['start'], diarization_result)
                    word_speaker_prefix = f"[{word_speaker}] " if word_speaker else ""

                    output_lines.append(f"  {word_start}-{word_end}: {word_speaker_prefix}{word_text}")

            # Add full segment
            output_lines.append(f"Full segment: {speaker_prefix}{text}")
            output_lines.append("")  # Empty line between segments

        generated_output = '\n'.join(output_lines)

        # Compare structure (we check that both have similar patterns)
        # We use regex to be flexible with exact timing differences

        # Check that both outputs have segment headers
        segment_pattern = r'\[\d{1,2}:\d{2}:\d{2} - \d{1,2}:\d{2}:\d{2}\] \[SPEAKER_\d+\]'
        expected_segments = re.findall(segment_pattern, expected_output)
        generated_segments = re.findall(segment_pattern, generated_output)

        assert len(expected_segments) > 0, "Expected output has no segments"
        assert len(generated_segments) > 0, "Generated output has no segments"

        # Check for "Full segment:" lines
        assert "Full segment:" in expected_output
        assert "Full segment:" in generated_output

    def test_segment_count_matches(self, transcription_result):
        """Test that we have the expected number of segments."""
        # From test2.txt, we can see there are 4 main segments
        segments = transcription_result['segments']

        # Should have at least 3-5 segments (allowing for slight variations)
        assert 3 <= len(segments) <= 6, f"Expected 3-6 segments, got {len(segments)}"

    def test_speakers_identified(self, diarization_result):
        """Test that multiple speakers are identified."""
        speakers = set()
        for turn, _, speaker in diarization_result.itertracks(yield_label=True):
            speakers.add(speaker)

        # The test video has 2 speakers
        assert len(speakers) >= 2, f"Expected at least 2 speakers, found {len(speakers)}"


class TestOutputFormatting:
    """Test various output formatting options."""

    def test_clean_format(self, transcription_result, diarization_result, diarization_service):
        """Test clean format output (segment only)."""
        output_lines = []

        for segment in transcription_result['segments']:
            start_time = format_timestamp(segment['start'])
            end_time = format_timestamp(segment['end'])
            text = ' '.join(segment['text'].strip().split())

            speaker = diarization_service.get_speaker_at_time(segment['start'], diarization_result)
            speaker_prefix = f"[{speaker}] " if speaker else ""

            output_lines.append(f"[{start_time} - {end_time}] {speaker_prefix}{text}")

        output = '\n'.join(output_lines)

        # Should have timestamps and speaker labels
        assert re.search(r'\[\d{1,2}:\d{2}:\d{2} - \d{1,2}:\d{2}:\d{2}\]', output)
        assert '[SPEAKER_' in output

        # Should NOT have word-level timestamps
        assert '  0:00:' not in output  # Word timestamps are indented

    def test_timestamps_only(self, transcription_result):
        """Test output with timestamps but no speaker diarization."""
        output_lines = []

        for segment in transcription_result['segments']:
            start_time = format_timestamp(segment['start'])
            end_time = format_timestamp(segment['end'])
            text = segment['text'].strip()

            output_lines.append(f"[{start_time} - {end_time}] {text}")

        output = '\n'.join(output_lines)

        # Should have timestamps
        assert re.search(r'\[\d{1,2}:\d{2}:\d{2} - \d{1,2}:\d{2}:\d{2}\]', output)

        # Should NOT have speaker labels
        assert '[SPEAKER_' not in output

    def test_plain_text_output(self, transcription_result):
        """Test plain text output (no timestamps, no speakers)."""
        text = transcription_result['text']

        # Should be plain text without formatting
        assert '[' not in text  # No timestamp brackets
        assert 'SPEAKER_' not in text  # No speaker labels
        assert len(text) > 0


@pytest.mark.skipif(not TEST_VIDEO.exists(), reason="test1.mp4 not found")
def test_video_file_exists():
    """Verify that test1.mp4 exists and is accessible."""
    assert TEST_VIDEO.exists()
    assert TEST_VIDEO.is_file()
    assert TEST_VIDEO.stat().st_size > 0


@pytest.mark.skipif(not EXPECTED_OUTPUT.exists(), reason="test2.txt not found")
def test_expected_output_exists():
    """Verify that test2.txt exists and is accessible."""
    assert EXPECTED_OUTPUT.exists()
    assert EXPECTED_OUTPUT.is_file()
    assert EXPECTED_OUTPUT.stat().st_size > 0
