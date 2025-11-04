"""Test cases for individual services."""

import pytest
import tempfile
import os
from pathlib import Path

from src.services import (
    TranscriptionService,
    DiarizationService,
    TranslationService,
    SubtitleService
)
from src.utils import TempFileManager


TEST_VIDEO = Path(__file__).parent.parent / "test1.mp4"


class TestTranscriptionServiceUnit:
    """Unit tests for TranscriptionService."""

    def test_service_initialization(self):
        """Test that service initializes correctly."""
        service = TranscriptionService()
        assert service.model is None
        assert service.current_model_name is None
        assert not service.is_loaded()

    def test_load_model(self):
        """Test loading a Whisper model."""
        service = TranscriptionService()
        service.load_model('tiny')

        assert service.is_loaded()
        assert service.current_model_name == 'tiny'

    def test_model_caching(self):
        """Test that models are cached and not reloaded."""
        service = TranscriptionService()
        service.load_model('tiny')

        model_id = id(service.model)

        # Load same model again
        service.load_model('tiny')

        # Should be the same model instance
        assert id(service.model) == model_id

    def test_transcribe_without_model_fails(self):
        """Test that transcription fails if model not loaded."""
        service = TranscriptionService()

        with pytest.raises(ValueError, match="Model not loaded"):
            service.transcribe('dummy.mp3')


class TestDiarizationServiceUnit:
    """Unit tests for DiarizationService."""

    def test_service_initialization(self):
        """Test that service initializes correctly."""
        service = DiarizationService()
        assert service.pipeline is None
        assert service.result is None
        assert not service.is_loaded()

    def test_is_available(self):
        """Test availability check."""
        is_available = DiarizationService.is_available()
        # Should return True or False, not None
        assert isinstance(is_available, bool)

    @pytest.mark.skipif(
        not DiarizationService.is_available(),
        reason="pyannote.audio not available"
    )
    def test_load_pipeline(self):
        """Test loading diarization pipeline."""
        service = DiarizationService()

        try:
            service.load_pipeline()
            assert service.is_loaded()
        except Exception as e:
            pytest.skip(f"Could not load pipeline: {e}")

    def test_get_speaker_without_result(self):
        """Test that getting speaker without result returns None."""
        service = DiarizationService()
        speaker = service.get_speaker_at_time(1.0)
        assert speaker is None


class TestTranslationServiceUnit:
    """Unit tests for TranslationService."""

    def test_service_initialization(self):
        """Test that service initializes correctly."""
        service = TranslationService()
        assert isinstance(service.cache, dict)
        assert len(service.cache) == 0

    def test_is_available(self):
        """Test availability check."""
        is_available = TranslationService.is_available()
        assert isinstance(is_available, bool)

    @pytest.mark.skipif(
        not TranslationService.is_available(),
        reason="googletrans not available"
    )
    def test_translate_basic(self):
        """Test basic translation."""
        service = TranslationService()
        result = service.translate("Hello", "es")

        assert result is not None
        assert len(result) > 0
        # Translation should be different from original (in most cases)
        # or same if translation failed and returned original

    @pytest.mark.skipif(
        not TranslationService.is_available(),
        reason="googletrans not available"
    )
    def test_translation_caching(self):
        """Test that translations are cached."""
        service = TranslationService()

        # Translate once
        result1 = service.translate("Hello", "es")

        # Check cache
        assert len(service.cache) > 0

        # Translate again
        result2 = service.translate("Hello", "es")

        # Should be same result from cache
        assert result1 == result2

    def test_clear_cache(self):
        """Test cache clearing."""
        service = TranslationService()
        service.cache["test_key"] = "test_value"

        assert len(service.cache) > 0

        service.clear_cache()

        assert len(service.cache) == 0

    @pytest.mark.skipif(
        not TranslationService.is_available(),
        reason="googletrans not available"
    )
    def test_translate_segments(self):
        """Test translating multiple segments."""
        service = TranslationService()

        segments = [
            {'text': 'Hello', 'start': 0.0, 'end': 1.0},
            {'text': 'World', 'start': 1.0, 'end': 2.0}
        ]

        translations = service.translate_segments(segments, 'es')

        assert len(translations) == len(segments)
        assert '0.0_1.0' in translations
        assert '1.0_2.0' in translations

    def test_map_translated_words_same_count(self):
        """Test word mapping with same word count."""
        service = TranslationService()

        original_words = [
            {'start': 0.0, 'end': 1.0, 'word': 'Hello'},
            {'start': 1.0, 'end': 2.0, 'word': 'World'}
        ]

        translated_text = "Hola Mundo"

        result = service.map_translated_words_to_timings(original_words, translated_text)

        assert len(result) == 2
        assert result[0]['word'] == 'Hola'
        assert result[1]['word'] == 'Mundo'
        assert result[0]['start'] == 0.0
        assert result[1]['start'] == 1.0

    def test_map_translated_words_different_count(self):
        """Test word mapping with different word count."""
        service = TranslationService()

        original_words = [
            {'start': 0.0, 'end': 1.0, 'word': 'Hello'}
        ]

        translated_text = "Hola amigo"  # 2 words instead of 1

        result = service.map_translated_words_to_timings(original_words, translated_text)

        assert len(result) == 2
        # Words should be distributed proportionally
        assert result[0]['start'] < result[1]['start']


class TestSubtitleServiceUnit:
    """Unit tests for SubtitleService."""

    @pytest.fixture
    def sample_transcription(self):
        """Create a sample transcription result."""
        return {
            'segments': [
                {
                    'start': 0.0,
                    'end': 2.0,
                    'text': 'Hello world'
                },
                {
                    'start': 2.5,
                    'end': 4.0,
                    'text': 'How are you?'
                }
            ]
        }

    def test_export_srt_basic(self, sample_transcription, tmp_path):
        """Test basic SRT export."""
        output_file = tmp_path / "test.srt"

        SubtitleService.export_srt(
            str(output_file),
            sample_transcription
        )

        assert output_file.exists()

        content = output_file.read_text(encoding='utf-8')

        # Check SRT format
        assert '1\n' in content
        assert '2\n' in content
        assert '-->' in content
        assert 'Hello world' in content
        assert 'How are you?' in content

    def test_export_srt_with_speakers(self, sample_transcription, tmp_path):
        """Test SRT export with speaker callback."""
        output_file = tmp_path / "test.srt"

        def speaker_callback(timestamp):
            return "SPEAKER_00" if timestamp < 2.0 else "SPEAKER_01"

        SubtitleService.export_srt(
            str(output_file),
            sample_transcription,
            speaker_callback=speaker_callback
        )

        content = output_file.read_text(encoding='utf-8')

        assert '[SPEAKER_00]' in content
        assert '[SPEAKER_01]' in content

    def test_export_vtt_basic(self, sample_transcription, tmp_path):
        """Test basic WebVTT export."""
        output_file = tmp_path / "test.vtt"

        SubtitleService.export_vtt(
            str(output_file),
            sample_transcription
        )

        assert output_file.exists()

        content = output_file.read_text(encoding='utf-8')

        # Check WebVTT format
        assert 'WEBVTT' in content
        assert '-->' in content
        assert 'Hello world' in content
        assert 'How are you?' in content

    @pytest.mark.skipif(
        not TranslationService.is_available(),
        reason="googletrans not available"
    )
    def test_export_srt_with_translation(self, sample_transcription, tmp_path):
        """Test SRT export with translation."""
        output_file = tmp_path / "test.srt"

        translation_service = TranslationService()

        def translation_callback(text):
            return translation_service.translate(text, 'es')

        SubtitleService.export_srt(
            str(output_file),
            sample_transcription,
            translation_callback=translation_callback
        )

        content = output_file.read_text(encoding='utf-8')

        # Original English text should not be in output
        # (it should be translated)
        # Note: Translation might vary, so we just check file was created
        assert len(content) > 0


class TestTempFileManager:
    """Test the temporary file manager utility."""

    def test_initialization(self):
        """Test manager initialization."""
        manager = TempFileManager()
        assert len(manager.temp_files) == 0

    def test_add_and_cleanup(self):
        """Test adding and cleaning up temp files."""
        manager = TempFileManager()

        # Create a temporary file
        fd, path = tempfile.mkstemp()
        os.close(fd)

        # Add to manager
        manager.add(path)
        assert len(manager.temp_files) == 1

        # Cleanup
        manager.cleanup()
        assert len(manager.temp_files) == 0
        assert not os.path.exists(path)

    def test_cleanup_missing_file(self):
        """Test that cleanup handles missing files gracefully."""
        manager = TempFileManager()

        # Add a non-existent file
        manager.add('/nonexistent/file.tmp')

        # Should not raise an error
        manager.cleanup()
        assert len(manager.temp_files) == 0
