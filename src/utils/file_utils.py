"""File handling utilities."""

import os
import tempfile
import subprocess
from typing import Optional, List


class TempFileManager:
    """Manages temporary files for cleanup."""

    def __init__(self):
        self.temp_files: List[str] = []

    def add(self, file_path: str):
        """Add a temporary file to track."""
        self.temp_files.append(file_path)

    def cleanup(self):
        """Clean up all tracked temporary files."""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception:
                pass  # Silently continue if cleanup fails
        self.temp_files = []


def convert_to_wav(input_file: str, output_file: Optional[str] = None) -> Optional[str]:
    """
    Convert audio/video file to WAV format using ffmpeg.

    Args:
        input_file: Path to input file
        output_file: Optional path to output file. If None, creates a temp file.

    Returns:
        Path to converted WAV file, or None if conversion failed
    """
    file_ext = os.path.splitext(input_file)[1].lower()

    # Already in a supported format
    supported_formats = ['.wav', '.mp3', '.m4a', '.flac']
    if file_ext in supported_formats and output_file is None:
        return input_file

    try:
        # Create temp file if no output specified
        if output_file is None:
            temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            temp_wav.close()
            output_file = temp_wav.name

        # Use ffmpeg to convert/extract audio
        cmd = [
            'ffmpeg', '-i', input_file,
            '-acodec', 'pcm_s16le',
            '-ar', '16000',
            '-ac', '1',
            '-y', output_file
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            return output_file
        else:
            # Clean up failed conversion
            if os.path.exists(output_file):
                os.unlink(output_file)
            return None

    except Exception:
        return None


def get_file_extension(file_path: str) -> str:
    """Get the file extension in lowercase."""
    return os.path.splitext(file_path)[1].lower()


def file_exists(file_path: str) -> bool:
    """Check if a file exists."""
    return os.path.exists(file_path)
