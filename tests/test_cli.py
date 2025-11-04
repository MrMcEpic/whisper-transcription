"""Test cases for CLI functionality."""

import pytest
import tempfile
import os
from pathlib import Path
import subprocess
import sys


TEST_VIDEO = Path(__file__).parent.parent / "test1.mp4"
MAIN_SCRIPT = Path(__file__).parent.parent / "main.py"


@pytest.fixture
def temp_output_file():
    """Create a temporary output file."""
    fd, path = tempfile.mkstemp(suffix='.txt')
    os.close(fd)
    yield path
    # Cleanup
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def temp_srt_file():
    """Create a temporary SRT output file."""
    fd, path = tempfile.mkstemp(suffix='.srt')
    os.close(fd)
    yield path
    # Cleanup
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def temp_vtt_file():
    """Create a temporary VTT output file."""
    fd, path = tempfile.mkstemp(suffix='.vtt')
    os.close(fd)
    yield path
    # Cleanup
    if os.path.exists(path):
        os.unlink(path)


class TestCLIBasic:
    """Test basic CLI functionality."""

    def test_cli_help(self):
        """Test that CLI help works."""
        result = subprocess.run(
            [sys.executable, str(MAIN_SCRIPT), '--help'],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode == 0
        assert 'Whisper Transcription Tool' in result.stdout
        assert '--cli' in result.stdout
        assert '--input' in result.stdout
        assert '--model' in result.stdout

    @pytest.mark.skipif(not TEST_VIDEO.exists(), reason="test1.mp4 not found")
    def test_cli_transcription_to_file(self, temp_output_file):
        """Test CLI transcription with output to file."""
        result = subprocess.run(
            [
                sys.executable, str(MAIN_SCRIPT),
                '--cli',
                '--input', str(TEST_VIDEO),
                '--model', 'base',  # Use base model for good accuracy
                '--output', temp_output_file,
                '--no-speaker-diarization'  # Skip diarization for speed
            ],
            capture_output=True,
            text=True,
            timeout=120  # 2 minutes timeout
        )

        # Check that command succeeded
        assert result.returncode == 0, f"CLI failed: {result.stderr}"

        # Check that output file was created
        assert os.path.exists(temp_output_file)

        # Check that output file has content
        with open(temp_output_file, 'r', encoding='utf-8') as f:
            content = f.read()

        assert len(content) > 0
        assert 'elephant' in content.lower() or 'trunk' in content.lower()

    @pytest.mark.skipif(not TEST_VIDEO.exists(), reason="test1.mp4 not found")
    def test_cli_transcription_stdout(self):
        """Test CLI transcription to stdout."""
        result = subprocess.run(
            [
                sys.executable, str(MAIN_SCRIPT),
                '--cli',
                '--input', str(TEST_VIDEO),
                '--model', 'base',
                '--no-speaker-diarization'
            ],
            capture_output=True,
            text=True,
            timeout=120
        )

        assert result.returncode == 0
        assert 'TRANSCRIPT:' in result.stdout
        assert len(result.stdout) > 0

    def test_cli_missing_input(self):
        """Test that CLI fails gracefully when input is missing."""
        result = subprocess.run(
            [
                sys.executable, str(MAIN_SCRIPT),
                '--cli'
            ],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode == 1
        assert 'required' in result.stdout.lower() or 'required' in result.stderr.lower()


class TestCLIOptions:
    """Test various CLI options."""

    @pytest.mark.skipif(not TEST_VIDEO.exists(), reason="test1.mp4 not found")
    def test_cli_clean_format(self, temp_output_file):
        """Test CLI with clean format option."""
        result = subprocess.run(
            [
                sys.executable, str(MAIN_SCRIPT),
                '--cli',
                '--input', str(TEST_VIDEO),
                '--model', 'base',
                '--output', temp_output_file,
                '--clean-format',
                '--no-speaker-diarization'
            ],
            capture_output=True,
            text=True,
            timeout=120
        )

        assert result.returncode == 0

        with open(temp_output_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Clean format should have timestamps
        assert '[' in content and ']' in content

    @pytest.mark.skipif(not TEST_VIDEO.exists(), reason="test1.mp4 not found")
    def test_cli_no_timestamps(self, temp_output_file):
        """Test CLI with timestamps disabled."""
        result = subprocess.run(
            [
                sys.executable, str(MAIN_SCRIPT),
                '--cli',
                '--input', str(TEST_VIDEO),
                '--model', 'base',
                '--output', temp_output_file,
                '--no-timestamps',
                '--no-speaker-diarization'
            ],
            capture_output=True,
            text=True,
            timeout=120
        )

        assert result.returncode == 0

        with open(temp_output_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Should not have timestamp brackets
        assert '[0:00:' not in content


class TestCLISubtitleExport:
    """Test CLI subtitle export functionality."""

    @pytest.mark.skipif(not TEST_VIDEO.exists(), reason="test1.mp4 not found")
    def test_cli_export_srt(self, temp_srt_file):
        """Test exporting SRT subtitles via CLI."""
        result = subprocess.run(
            [
                sys.executable, str(MAIN_SCRIPT),
                '--cli',
                '--input', str(TEST_VIDEO),
                '--model', 'base',
                '--export-srt', temp_srt_file,
                '--no-speaker-diarization'
            ],
            capture_output=True,
            text=True,
            timeout=120
        )

        assert result.returncode == 0
        assert os.path.exists(temp_srt_file)

        with open(temp_srt_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # SRT format checks
        assert '1\n' in content  # First subtitle number
        assert '-->' in content  # SRT timestamp separator
        assert ',' in content  # SRT uses comma for milliseconds

    @pytest.mark.skipif(not TEST_VIDEO.exists(), reason="test1.mp4 not found")
    def test_cli_export_vtt(self, temp_vtt_file):
        """Test exporting WebVTT subtitles via CLI."""
        result = subprocess.run(
            [
                sys.executable, str(MAIN_SCRIPT),
                '--cli',
                '--input', str(TEST_VIDEO),
                '--model', 'base',
                '--export-vtt', temp_vtt_file,
                '--no-speaker-diarization'
            ],
            capture_output=True,
            text=True,
            timeout=120
        )

        assert result.returncode == 0
        assert os.path.exists(temp_vtt_file)

        with open(temp_vtt_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # WebVTT format checks
        assert 'WEBVTT' in content  # WebVTT header
        assert '-->' in content  # VTT timestamp separator
        assert '.' in content  # VTT uses dot for milliseconds


class TestCLIModels:
    """Test different Whisper models via CLI."""

    @pytest.mark.parametrize('model', ['base', 'small'])
    @pytest.mark.skipif(not TEST_VIDEO.exists(), reason="test1.mp4 not found")
    def test_cli_different_models(self, model, temp_output_file):
        """Test that different models work."""
        result = subprocess.run(
            [
                sys.executable, str(MAIN_SCRIPT),
                '--cli',
                '--input', str(TEST_VIDEO),
                '--model', model,
                '--output', temp_output_file,
                '--no-speaker-diarization'
            ],
            capture_output=True,
            text=True,
            timeout=180
        )

        assert result.returncode == 0
        assert os.path.exists(temp_output_file)

        with open(temp_output_file, 'r', encoding='utf-8') as f:
            content = f.read()

        assert len(content) > 0
        # Verify that we get reasonable content
        content_lower = content.lower()
        assert len(content_lower) > 50  # Should have substantial text
