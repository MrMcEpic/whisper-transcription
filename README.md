# Whisper Transcription Tool

A professional, modular transcription tool using OpenAI Whisper with speaker diarization, translation, and comprehensive testing.

## ✨ Features

- **🎙️ OpenAI Whisper Integration**: High-quality transcription with multiple models
- **👥 Speaker Diarization**: Automatic speaker identification using pyannote.audio
- **🖥️ Dual Interface**: Modern GUI and powerful CLI
- **🌍 Translation**: Translate to 100+ languages with intelligent caching
- **🎨 Dark/Light Mode**: Modern theme system with automatic OS detection
- **📊 Export Formats**: Text, JSON, SRT, WebVTT subtitles
- **✅ Comprehensive Testing**: 67 tests with robust AI testing strategy
- **📈 Real-time Progress**: Live progress tracking and status updates
- **🎬 Multiple Formats**: MP4, AVI, MOV, MKV, MP3, WAV, M4A, FLAC

## 📦 Installation

### 1. Install FFmpeg (Required)

**Windows (using winget)**:

```bash
winget install FFmpeg
```

**Linux (using apt)**:

```bash
sudo apt update && sudo apt install ffmpeg
```

**macOS (using Homebrew)**:

```bash
brew install ffmpeg
```

### 2. Clone and Setup

```bash
git clone <repository-url>
cd whisper

# Create virtual environment
python -m venv whisper_env

# Activate (Windows)
whisper_env\Scripts\activate

# Activate (Linux/Mac)
source whisper_env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Optional: Speaker Diarization Setup

1. Accept conditions for [pyannote/segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0)
2. Accept conditions for [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)
3. Create access token at [hf.co/settings/tokens](https://hf.co/settings/tokens)
4. Add to `.env` file: `TOKEN=your_huggingface_token`

## 🚀 Quick Start

### GUI Mode (Default)

```bash
python main.py
```

### CLI Mode

```bash
# Basic transcription
python main.py --cli --input audio.mp3 --output transcript.txt

# With speaker diarization
python main.py --cli --input video.mp4 --model large-v3 --output transcript.txt

# Export subtitles
python main.py --cli --input video.mp4 --export-srt subtitles.srt

# Translate
python main.py --cli --input video.mp4 --translate --output english.txt
```

### Quick Test (with test1.mp4)

```bash
# Test with base model (good balance)
python run_test.py

# Test with best accuracy
python run_test.py --model large-v3

# Test without diarization (faster)
python run_test.py --model base --no-diarization
```

## 📚 Usage

### Command-Line Options

```bash
python main.py --cli [OPTIONS]
```

**Core Options**:

- `--input FILE` - Input audio/video file (required)
- `--model NAME` - Whisper model: tiny, base, small, medium, large, large-v2, large-v3, turbo (default: large-v3)
- `--output FILE` - Output transcript file

**Transcription Options**:

- `--no-timestamps` - Disable timestamps
- `--no-word-timestamps` - Disable word-level timestamps
- `--no-speaker-diarization` - Disable speaker identification
- `--clean-format` - Use clean segment format only

**Language Options**:

- `--language CODE` - Source language (auto for auto-detect)
- `--translate` - Translate to English using Whisper

**Export Options**:

- `--export-srt FILE` - Export as SRT subtitles
- `--export-vtt FILE` - Export as WebVTT subtitles
- `--export-srt-translated FILE` - Export translated SRT
- `--export-vtt-translated FILE` - Export translated WebVTT
- `--subtitle-language CODE` - Target language for subtitles (default: es)

### Model Selection

| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| tiny | 39 MB | ⚡⚡⚡⚡⚡ | ⭐ | Quick tests only |
| **base** | 74 MB | ⚡⚡⚡⚡ | ⭐⭐ | **Good balance** |
| small | 244 MB | ⚡⚡⚡ | ⭐⭐⭐ | Better accuracy |
| medium | 769 MB | ⚡⚡ | ⭐⭐⭐⭐ | High accuracy |
| **large-v3** | 1.5 GB | ⚡ | ⭐⭐⭐⭐⭐ | **Best accuracy** |
| turbo | 809 MB | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ | Fast + accurate |

**Note**: `tiny` model may miss words. Use `base` or better for production.

### Examples

**Basic Transcription**:

```bash
python main.py --cli --input meeting.mp3 --model base --output transcript.txt
```

**With Speaker Labels**:

```bash
python main.py --cli --input interview.mp4 --model large-v3 --output interview.txt
```

**Export Subtitles**:

```bash
# English SRT
python main.py --cli --input video.mp4 --export-srt subtitles.srt

# Spanish translated SRT
python main.py --cli --input video.mp4 --export-srt-translated spanish.srt --subtitle-language es

# French WebVTT
python main.py --cli --input video.mp4 --export-vtt-translated french.vtt --subtitle-language fr
```

**Translation**:

```bash
# Transcribe Spanish audio to English
python main.py --cli --input spanish.mp3 --translate --output english.txt

# Transcribe and export with translation
python main.py --cli --input video.mp4 --output original.txt --export-srt-translated spanish.srt --subtitle-language es
```

## Architecture

### Modular Structure

```text
whisper/
├── main.py                          # Application entry point
├── run_test.py                      # Quick test script
├── src/
│   ├── config.py                    # Configuration & constants
│   ├── cli.py                       # CLI interface
│   ├── services/                    # Business logic
│   │   ├── transcription_service.py # Whisper transcription
│   │   ├── diarization_service.py   # Speaker diarization
│   │   ├── translation_service.py   # Translation & caching
│   │   └── subtitle_service.py      # SRT/VTT export
│   ├── ui/                          # User interface
│   │   ├── theme_manager.py         # Theme system
│   │   └── gui_application.py       # GUI application
│   └── utils/                       # Utilities
│       ├── timestamps.py            # Timestamp formatting
│       ├── file_utils.py            # File operations
│       └── system_utils.py          # System utilities
└── tests/                           # Comprehensive test suite
    ├── test_transcription.py        # Integration tests
    ├── test_cli.py                  # CLI tests
    ├── test_services.py             # Unit tests
    └── test_utils.py                # Utility tests
```

## 🧪 Testing

### Run Tests

```bash
# All tests (67 tests)
pytest

# Fast tests only (< 15 seconds)
pytest tests/test_utils.py tests/test_services.py

# Integration tests with test1.mp4
pytest tests/test_transcription.py

# With coverage report
pytest --cov=src --cov-report=html
```

### Quick Test Script

```bash
# Default (base model)
python run_test.py

# Best accuracy
python run_test.py --model large-v3

# Faster (skip diarization)
python run_test.py --model base --no-diarization

# Show options
python run_test.py --help
```

### Test Coverage
- ✅ **67 tests** - All passing
- ✅ **97% coverage** of core services
- ✅ **Robust strategy** for AI variability
- ✅ **Integration tests** with actual transcription

## 📋 Requirements

- **Python 3.8+**
- **FFmpeg** (for video processing)
- **CUDA GPU** (recommended for faster processing)
- **HuggingFace account** (optional, for speaker diarization)

### Python Dependencies

Core:
- openai-whisper
- torch
- tkinter
- python-dotenv

Optional:
- pyannote.audio (speaker diarization)
- googletrans (translation to non-English)

See `requirements.txt` for complete list.

## 📤 Output Formats

1. **Text Transcript**: Plain text with optional timestamps and speakers
2. **Formatted Segments**: Clean segment format with structure
3. **JSON Export**: Complete Whisper output with all metadata
4. **SRT Subtitles**: Industry-standard subtitle format
5. **WebVTT Subtitles**: Web-compatible subtitle format
6. **Translated Versions**: All formats available with translation

### Example Output

```
[0:00:00 - 0:00:03] [SPEAKER_00]
  0:00:00-0:00:01: [SPEAKER_00]  Alright,
  0:00:01-0:00:01: [SPEAKER_01]  so
  0:00:01-0:00:02: [SPEAKER_01]  here
  ...
Full segment: [SPEAKER_00] Alright, so here we are in front of the elephants.

[0:00:04 - 0:00:12] [SPEAKER_01]
  ...
```

## 🎨 GUI Features

- **Modern Interface**: Clean, professional design
- **Theme System**: Dark/light mode with OS detection
- **Model Selection**: Choose any Whisper model
- **Language Settings**: Source language and translation options
- **Options Panel**: All features accessible via checkboxes
- **Progress Tracking**: Real-time progress for each stage
- **Export Buttons**: Quick access to all export formats
- **Status Display**: Clear feedback on current operation

## 🔧 Troubleshooting

### Common Issues

**Models missing words**:

- Use `base` or better (not `tiny`)

**GPU memory errors**:

- Try smaller models (base, small, medium)
- Close other GPU-intensive applications

**Speaker diarization fails**:

- Check HuggingFace token in `.env` file
- Verify you accepted model conditions
- Run with `--no-speaker-diarization` as fallback

**File format errors**:

- Ensure FFmpeg is installed: `ffmpeg -version`
- Check file path is correct
- Try converting file format first

**Tests failing**:

- Run `pytest -v` to see details
- Some AI output variation is normal

### Performance Tips

**Speed up processing**:

- Use `turbo` or `base` model
- Skip diarization with `--no-diarization`
- Use GPU (install CUDA-enabled PyTorch)

**Improve accuracy**:

- Use `large-v3` model
- Specify source language with `--language`
- Enable word-level timestamps

## 📖 Documentation

All documentation is consolidated in this README for easy reference.

---

**Quick Links**:

- [Quick Start](#-quick-start)
- [Architecture](#architecture)
- [Testing](#-testing)
- [Usage](#-usage)
