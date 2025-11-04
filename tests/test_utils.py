"""Test cases for utility functions."""

import pytest
from src.utils.timestamps import (
    format_timestamp,
    format_srt_timestamp,
    format_vtt_timestamp,
    parse_timestamp_to_seconds
)


class TestTimestampFormatting:
    """Test timestamp formatting utilities."""

    def test_format_timestamp_zero(self):
        """Test formatting zero seconds."""
        result = format_timestamp(0)
        assert result == "0:00:00"

    def test_format_timestamp_minutes(self):
        """Test formatting minutes."""
        result = format_timestamp(125)  # 2 minutes 5 seconds
        assert result == "0:02:05"

    def test_format_timestamp_hours(self):
        """Test formatting hours."""
        result = format_timestamp(3665)  # 1 hour 1 minute 5 seconds
        assert result == "1:01:05"

    def test_format_srt_timestamp_zero(self):
        """Test SRT format for zero seconds."""
        result = format_srt_timestamp(0)
        assert result == "00:00:00,000"

    def test_format_srt_timestamp_with_milliseconds(self):
        """Test SRT format with milliseconds."""
        result = format_srt_timestamp(1.234)
        assert result == "00:00:01,234"

    def test_format_srt_timestamp_full(self):
        """Test SRT format with hours, minutes, seconds, milliseconds."""
        result = format_srt_timestamp(3665.5)
        # Use exact floating point value to avoid precision issues
        assert result == "01:01:05,500"

    def test_format_vtt_timestamp_zero(self):
        """Test VTT format for zero seconds."""
        result = format_vtt_timestamp(0)
        assert result == "00:00:00.000"

    def test_format_vtt_timestamp_with_milliseconds(self):
        """Test VTT format with milliseconds (uses dot instead of comma)."""
        result = format_vtt_timestamp(1.234)
        assert result == "00:00:01.234"

    def test_format_vtt_timestamp_full(self):
        """Test VTT format with full timestamp."""
        result = format_vtt_timestamp(3665.5)
        # Use exact floating point value to avoid precision issues
        assert result == "01:01:05.500"

    def test_parse_timestamp_to_seconds_simple(self):
        """Test parsing simple timestamp."""
        result = parse_timestamp_to_seconds("0:00:05")
        assert result == 5

    def test_parse_timestamp_to_seconds_minutes(self):
        """Test parsing timestamp with minutes."""
        result = parse_timestamp_to_seconds("0:02:05")
        assert result == 125

    def test_parse_timestamp_to_seconds_hours(self):
        """Test parsing timestamp with hours."""
        result = parse_timestamp_to_seconds("1:01:05")
        assert result == 3665

    def test_timestamp_roundtrip(self):
        """Test that formatting and parsing are consistent."""
        original_seconds = 3665
        formatted = format_timestamp(original_seconds)
        parsed = parse_timestamp_to_seconds(formatted)
        assert parsed == original_seconds


class TestTimestampEdgeCases:
    """Test edge cases for timestamp formatting."""

    def test_fractional_seconds_rounded(self):
        """Test that fractional seconds are handled correctly."""
        result = format_timestamp(1.9)
        # Should round down to 1 second
        assert result == "0:00:01"

    def test_large_hours(self):
        """Test handling of large hour values."""
        result = format_timestamp(36000)  # 10 hours
        assert result == "10:00:00"

    def test_srt_milliseconds_rounded(self):
        """Test SRT milliseconds rounding."""
        result = format_srt_timestamp(1.9999)
        # Should have 999 milliseconds
        assert "01,999" in result

    def test_vtt_milliseconds_rounded(self):
        """Test VTT milliseconds rounding."""
        result = format_vtt_timestamp(1.9999)
        # Should have 999 milliseconds with dot
        assert "01.999" in result
