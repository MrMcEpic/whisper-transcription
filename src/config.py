"""Configuration and constants for the Whisper Transcription Tool."""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Whisper model options
WHISPER_MODELS = ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3", "turbo"]
DEFAULT_MODEL = "large-v3"

# Common languages for transcription
COMMON_LANGUAGES = [
    "auto", "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko",
    "zh", "ar", "hi", "nl", "pl", "tr", "sv", "da", "no", "fi"
]

# Language names for translation export
TRANSLATION_LANGUAGES = {
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Italian": "it",
    "Portuguese": "pt",
    "Russian": "ru",
    "Japanese": "ja",
    "Korean": "ko",
    "Chinese": "zh",
    "Arabic": "ar",
    "Hindi": "hi",
    "Dutch": "nl"
}

# File types for file dialog
SUPPORTED_FILE_TYPES = [
    ("All supported", "*.mp4 *.avi *.mov *.mkv *.mp3 *.wav *.m4a *.flac"),
    ("Video files", "*.mp4 *.avi *.mov *.mkv"),
    ("Audio files", "*.mp3 *.wav *.m4a *.flac"),
    ("All files", "*.*")
]

# Supported audio formats for diarization (without conversion)
DIARIZATION_SUPPORTED_FORMATS = ['.wav', '.mp3', '.m4a', '.flac']

# HuggingFace token for speaker diarization
HF_TOKEN = os.getenv('TOKEN')

# Diarization model
DIARIZATION_MODEL = "pyannote/speaker-diarization-3.1"

# Progress simulation for diarization
DIARIZATION_PROGRESS_STEPS = [
    ("Speaker diarization: loading models...", 0, 0.5),
    ("Speaker diarization: segmentation...", 10, 1.0),
    ("Speaker diarization: embeddings...", 25, 2.0),
    ("Speaker diarization: clustering...", 40, 1.0),
    ("Speaker diarization: finalizing...", 48, 0.5),
]

# Speaker matching threshold (seconds)
SPEAKER_MATCH_THRESHOLD = 0.8

# UI Configuration
DEFAULT_WINDOW_SIZE = "950x700"
DEFAULT_FONT_FAMILY = 'Segoe UI'
DEFAULT_FONT_SIZE = 10

# Theme colors
DARK_THEME = {
    'bg': "#1e1e1e",
    'fg': "#cccccc",
    'entry_bg': "#3c3c3c",
    'entry_fg': "#ffffff",
    'entry_readonly_bg': "#2a2a2a",
    'entry_readonly_fg': "#999999",
    'button_bg': "#0e639c",
    'button_fg': "#ffffff",
    'button_hover': "#1177bb",
    'select_bg': "#264f78",
    'border': "#464647",
    'info': '#4fc1ff',
    'success': '#73c991',
    'warning': '#ffcc02',
    'error': '#f85149'
}

LIGHT_THEME = {
    'bg': "#f5f5f5",
    'fg': "#222222",
    'entry_bg': "#ffffff",
    'entry_fg': "#000000",
    'entry_readonly_bg': "#ffffff",
    'entry_readonly_fg': "#444444",
    'button_bg': "#e1e1e1",
    'button_fg': "#222222",
    'button_hover': "#d6d6d6",
    'select_bg': "#dcdcdc",
    'border': "#bdbdbd",
    'info': 'blue',
    'success': 'green',
    'warning': 'orange',
    'error': 'red'
}
