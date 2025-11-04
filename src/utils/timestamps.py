"""Timestamp formatting utilities."""

from datetime import timedelta


def format_timestamp(seconds):
    """Format seconds as HH:MM:SS."""
    return str(timedelta(seconds=int(seconds)))


def format_srt_timestamp(seconds):
    """Format timestamp for SRT format: HH:MM:SS,mmm."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds_remainder = seconds % 60
    milliseconds = int((seconds_remainder - int(seconds_remainder)) * 1000)
    seconds_int = int(seconds_remainder)

    return f"{hours:02d}:{minutes:02d}:{seconds_int:02d},{milliseconds:03d}"


def format_vtt_timestamp(seconds):
    """Format timestamp for VTT format: HH:MM:SS.mmm."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds_remainder = seconds % 60
    milliseconds = int((seconds_remainder - int(seconds_remainder)) * 1000)
    seconds_int = int(seconds_remainder)

    return f"{hours:02d}:{minutes:02d}:{seconds_int:02d}.{milliseconds:03d}"


def parse_timestamp_to_seconds(timestamp_str):
    """Parse timestamp string (HH:MM:SS) to seconds."""
    time_parts = timestamp_str.split(':')
    return int(time_parts[0]) * 3600 + int(time_parts[1]) * 60 + int(time_parts[2])
