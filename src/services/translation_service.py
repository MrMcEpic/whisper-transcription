"""Translation service using Google Translate."""

import asyncio
from typing import Dict, List, Optional

# Optional import for translation
try:
    from googletrans import Translator
    GOOGLETRANS_AVAILABLE = True
except ImportError:
    Translator = None
    GOOGLETRANS_AVAILABLE = False


class TranslationService:
    """Handles text translation using Google Translate."""

    def __init__(self):
        self.translator = Translator() if GOOGLETRANS_AVAILABLE else None
        self.cache: Dict[str, str] = {}

    @staticmethod
    def is_available() -> bool:
        """Check if googletrans is available."""
        return GOOGLETRANS_AVAILABLE

    def translate(self, text: str, target_lang: str = 'es') -> str:
        """
        Translate text to target language.

        Args:
            text: Text to translate
            target_lang: Target language code

        Returns:
            Translated text, or original text if translation fails
        """
        if not GOOGLETRANS_AVAILABLE or not self.translator:
            return text

        # Check cache
        cache_key = f"{text}_{target_lang}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            result = self.translator.translate(text, dest=target_lang)

            # Handle async results
            if asyncio.iscoroutine(result):
                result = self._handle_async_translation(result)

            translated_text = result.text if hasattr(result, 'text') else str(result)

            # Cache the result
            self.cache[cache_key] = translated_text
            return translated_text

        except Exception as e:
            print(f"Translation warning: {e}")
            return text

    def _handle_async_translation(self, coroutine):
        """Handle async translation results."""
        try:
            # Try nest_asyncio for GUI compatibility
            try:
                import nest_asyncio
                nest_asyncio.apply()
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(coroutine)
            except ImportError:
                # Fallback to running in separate thread
                import concurrent.futures

                def run_async():
                    return asyncio.run(coroutine)

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_async)
                    return future.result(timeout=10)

        except Exception as e:
            print(f"Async translation failed: {e}")
            raise

    def translate_segments(
        self,
        segments: List[Dict],
        target_lang: str,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, str]:
        """
        Translate multiple segments.

        Args:
            segments: List of segment dictionaries with 'text', 'start', 'end'
            target_lang: Target language code
            progress_callback: Optional callback for progress (current, total)

        Returns:
            Dictionary mapping segment keys to translated text
        """
        translations = {}
        total = len(segments)

        for i, segment in enumerate(segments):
            text = segment['text'].strip()
            segment_key = f"{segment['start']}_{segment['end']}"

            translated_text = self.translate(text, target_lang)
            translations[segment_key] = translated_text

            if progress_callback:
                progress_callback(i + 1, total)

        return translations

    def clear_cache(self):
        """Clear the translation cache."""
        self.cache = {}

    def map_translated_words_to_timings(
        self,
        original_words: List[Dict],
        translated_text: str
    ) -> List[Dict]:
        """
        Map translated text back to original word timings.

        Args:
            original_words: List of word dictionaries with 'start', 'end', 'word'
            translated_text: Translated text

        Returns:
            List of mapped word dictionaries
        """
        if not translated_text or not original_words:
            return []

        translated_words = translated_text.strip().split()

        # 1:1 mapping if same number of words
        if len(translated_words) == len(original_words):
            return [
                {
                    'start': orig_word['start'],
                    'end': orig_word['end'],
                    'word': trans_word,
                    'original': orig_word['word']
                }
                for orig_word, trans_word in zip(original_words, translated_words)
            ]

        # Proportional distribution if different number of words
        mapped_words = []
        if len(translated_words) > 0:
            total_duration = original_words[-1]['end'] - original_words[0]['start']
            time_per_word = total_duration / len(translated_words)

            start_time = original_words[0]['start']
            for i, trans_word in enumerate(translated_words):
                word_start = start_time + (i * time_per_word)
                word_end = start_time + ((i + 1) * time_per_word)

                # Ensure we don't exceed the original segment end
                if word_end > original_words[-1]['end']:
                    word_end = original_words[-1]['end']

                mapped_words.append({
                    'start': word_start,
                    'end': word_end,
                    'word': trans_word,
                    'original': f"from {len(original_words)} orig words"
                })

        return mapped_words
