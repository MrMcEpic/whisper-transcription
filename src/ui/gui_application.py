"""GUI application for the Whisper Transcription Tool."""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import re
import json
import time

from ..services import (
    TranscriptionService,
    DiarizationService,
    TranslationService,
    SubtitleService
)
from ..utils import (
    format_timestamp,
    format_srt_timestamp,
    format_vtt_timestamp,
    parse_timestamp_to_seconds,
    TempFileManager,
    convert_to_wav
)
from ..config import (
    WHISPER_MODELS,
    DEFAULT_MODEL,
    COMMON_LANGUAGES,
    TRANSLATION_LANGUAGES,
    SUPPORTED_FILE_TYPES,
    DEFAULT_WINDOW_SIZE,
    DIARIZATION_PROGRESS_STEPS
)
from .theme_manager import ThemeManager


class WhisperGUI:
    """Main GUI application for Whisper transcription."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Transcription Tool")
        self.root.geometry(DEFAULT_WINDOW_SIZE)

        # Initialize services
        self.transcription_service = TranscriptionService()
        self.diarization_service = DiarizationService()
        self.translation_service = TranslationService()
        self.subtitle_service = SubtitleService()
        self.temp_manager = TempFileManager()

        # Initialize theme manager
        self.theme_manager = ThemeManager(root)

        # State variables
        self.transcription_result = None
        self.diarization_result = None
        self.translated_segments = {}

        # Setup UI and apply theme
        self.setup_ui()
        self.theme_manager.apply_theme()
        self.apply_widget_styles()

        # Cleanup on window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_ui(self):
        """Setup the main UI components."""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        row = 0

        # File Selection
        row = self._create_file_selection(main_frame, row)

        # Model Selection
        row = self._create_model_selection(main_frame, row)

        # Language Settings
        row = self._create_language_settings(main_frame, row)

        # Options
        row = self._create_options(main_frame, row)

        # Buttons
        row = self._create_buttons(main_frame, row)

        # Progress Bars
        row = self._create_progress_bars(main_frame, row)

        # Status Label
        self.status_label = ttk.Label(
            main_frame,
            text="Ready",
            foreground=self.theme_manager.get_color('success')
        )
        self.status_label.grid(row=row, column=0, columnspan=2, pady=(0, 10))
        row += 1

        # Transcript Display
        self._create_transcript_display(main_frame, row)

        main_frame.rowconfigure(row, weight=1)

    def _create_file_selection(self, parent, row):
        """Create file selection UI."""
        ttk.Label(parent, text="File Selection:", font=('Arial', 12, 'bold')).grid(
            row=row, column=0, sticky=tk.W, pady=(0, 5))
        row += 1

        file_frame = ttk.Frame(parent)
        file_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(0, weight=1)

        self.file_var = tk.StringVar()
        self.file_entry = ttk.Entry(file_frame, textvariable=self.file_var, state="readonly")
        self.file_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))

        self.browse_btn = ttk.Button(
            file_frame,
            text="Browse",
            command=self.browse_file,
            style='App.TButton'
        )
        self.browse_btn.grid(row=0, column=1)

        return row + 1

    def _create_model_selection(self, parent, row):
        """Create model selection UI."""
        ttk.Label(parent, text="Model Selection:", font=('Arial', 12, 'bold')).grid(
            row=row, column=0, sticky=tk.W, pady=(10, 5))
        row += 1

        self.model_var = tk.StringVar(value=DEFAULT_MODEL)
        model_frame = ttk.Frame(parent)
        model_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        self.model_radio_labels = {}
        for i, model in enumerate(WHISPER_MODELS):
            rb = ttk.Radiobutton(
                model_frame,
                text=f"  {model}",
                variable=self.model_var,
                value=model,
                style='IndicatorLess.TRadiobutton'
            )
            rb.grid(row=0, column=i, padx=5)
            self.model_radio_labels[model] = rb

        # Update bullet icons
        def update_model_bullets(*_):
            selected = self.model_var.get()
            for name, rb in self.model_radio_labels.items():
                bullet = "●" if name == selected else "○"
                rb.configure(text=f" {bullet} {name}")

        self.model_var.trace_add('write', update_model_bullets)
        update_model_bullets()

        return row + 1

    def _create_language_settings(self, parent, row):
        """Create language settings UI."""
        ttk.Label(parent, text="Language Settings:", font=('Arial', 12, 'bold')).grid(
            row=row, column=0, sticky=tk.W, pady=(10, 5))
        row += 1

        language_frame = ttk.Frame(parent)
        language_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Label(language_frame, text="Source:").grid(row=0, column=0, sticky=tk.W)
        self.source_language_var = tk.StringVar(value="auto")
        self.source_language_combo = ttk.Combobox(
            language_frame,
            textvariable=self.source_language_var,
            values=COMMON_LANGUAGES,
            width=15,
            state="readonly"
        )
        self.source_language_combo.grid(row=0, column=1, sticky=tk.W, padx=(5, 20))

        self.translate_var = tk.BooleanVar(value=False)
        self.translate_check = ttk.Checkbutton(
            language_frame,
            text="Translate to:",
            variable=self.translate_var,
            command=self.toggle_translation
        )
        self.translate_check.grid(row=0, column=2, sticky=tk.W)

        self.target_language_var = tk.StringVar(value="en")
        self.target_language_combo = ttk.Combobox(
            language_frame,
            textvariable=self.target_language_var,
            values=COMMON_LANGUAGES[1:],
            width=15,
            state="disabled"
        )
        self.target_language_combo.grid(row=0, column=3, sticky=tk.W, padx=(5, 0))

        # Bind popup styling
        for combo in (self.source_language_combo, self.target_language_combo):
            combo.bind("<Button-1>", lambda e, c=combo: self.theme_manager.style_combobox_popup(c))
            self.theme_manager.style_combobox_popup(combo)

        return row + 1

    def _create_options(self, parent, row):
        """Create options UI."""
        ttk.Label(parent, text="Options:", font=('Arial', 12, 'bold')).grid(
            row=row, column=0, sticky=tk.W, pady=(10, 5))
        row += 1

        options_frame = ttk.Frame(parent)
        options_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        self.timestamps_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Include timestamps",
            variable=self.timestamps_var
        ).grid(row=0, column=0, sticky=tk.W)

        self.word_timestamps_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Word-level timestamps",
            variable=self.word_timestamps_var
        ).grid(row=0, column=1, sticky=tk.W, padx=(20, 0))

        self.speaker_diarization_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Speaker diarization",
            variable=self.speaker_diarization_var
        ).grid(row=1, column=0, sticky=tk.W)

        self.clean_format_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            options_frame,
            text="Clean format (segments only)",
            variable=self.clean_format_var
        ).grid(row=1, column=1, sticky=tk.W, padx=(20, 0))

        return row + 1

    def _create_buttons(self, parent, row):
        """Create action buttons."""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=row, column=0, columnspan=2, pady=10)

        self.transcribe_btn = ttk.Button(
            button_frame,
            text="Transcribe",
            command=self.start_transcription,
            style='App.TButton'
        )
        self.transcribe_btn.grid(row=0, column=0, padx=5)

        self.save_btn = ttk.Button(
            button_frame,
            text="Save Transcript",
            command=self.save_transcript,
            state="disabled",
            style='App.TButton'
        )
        self.save_btn.grid(row=0, column=1, padx=5)

        self.format_btn = ttk.Button(
            button_frame,
            text="Format Segments",
            command=self.format_segments,
            state="disabled",
            style='App.TButton'
        )
        self.format_btn.grid(row=0, column=2, padx=5)

        self.export_subtitle_btn = ttk.Button(
            button_frame,
            text="Export Subtitles",
            command=self.export_subtitles,
            state="disabled",
            style='App.TButton'
        )
        self.export_subtitle_btn.grid(row=0, column=3, padx=5)

        self.export_translated_btn = ttk.Button(
            button_frame,
            text="Export Translated Subs",
            command=self.export_translated_subtitles,
            state="disabled",
            style='App.TButton'
        )
        self.export_translated_btn.grid(row=0, column=4, padx=5)

        initial_text = "☀️ Light Mode" if self.theme_manager.is_dark_mode() else "🌙 Dark Mode"
        self.dark_mode_btn = ttk.Button(
            button_frame,
            text=initial_text,
            command=self.toggle_dark_mode,
            style='App.TButton'
        )
        self.dark_mode_btn.grid(row=0, column=5, padx=5)

        return row + 1

    def _create_progress_bars(self, parent, row):
        """Create progress bars."""
        ttk.Label(parent, text="Current Task:", font=('Arial', 10)).grid(
            row=row, column=0, sticky=tk.W, pady=(10, 2))
        row += 1

        self.current_progress = ttk.Progressbar(parent, mode='determinate', maximum=100)
        self.current_progress.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        row += 1

        ttk.Label(parent, text="Overall Progress:", font=('Arial', 10)).grid(
            row=row, column=0, sticky=tk.W, pady=(5, 2))
        row += 1

        self.progress = ttk.Progressbar(parent, mode='determinate', maximum=100)
        self.progress.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        row += 1

        return row

    def _create_transcript_display(self, parent, row):
        """Create transcript display area."""
        ttk.Label(parent, text="Transcript:", font=('Arial', 12, 'bold')).grid(
            row=row, column=0, sticky=tk.W, pady=(10, 5))
        row += 1

        text_holder = ttk.Frame(parent)
        text_holder.grid(row=row, column=0, columnspan=2,
                        sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        text_holder.columnconfigure(0, weight=1)
        text_holder.rowconfigure(0, weight=1)

        self.result_text = tk.Text(
            text_holder,
            height=20,
            wrap=tk.WORD,
            borderwidth=0,
            highlightthickness=0
        )
        self.result_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.result_vscroll = ttk.Scrollbar(
            text_holder,
            orient='vertical',
            command=self.result_text.yview
        )
        self.result_vscroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.result_text.configure(yscrollcommand=self.result_vscroll.set)

        self.theme_manager.style_text_widget(self.result_text)

    def apply_widget_styles(self):
        """Apply theme styles to widgets."""
        prefix = self.theme_manager._theme_prefix()

        if hasattr(self, 'file_entry'):
            self.file_entry.configure(style=f'{prefix}.Readonly.TEntry')
        if hasattr(self, 'source_language_combo'):
            self.source_language_combo.configure(style=f'{prefix}.TCombobox')
            self.theme_manager.style_combobox_popup(self.source_language_combo)
        if hasattr(self, 'target_language_combo'):
            self.target_language_combo.configure(style=f'{prefix}.TCombobox')
            self.theme_manager.style_combobox_popup(self.target_language_combo)

        if hasattr(self, 'result_vscroll'):
            self.result_vscroll.configure(style=f"{prefix}.Vertical.TScrollbar")

    def set_status(self, text: str, status_type: str = 'info'):
        """Set status label with appropriate color."""
        color = self.theme_manager.get_color(status_type)
        self.status_label.config(text=text, foreground=color)

    def toggle_translation(self):
        """Toggle translation language combobox."""
        if self.translate_var.get():
            self.target_language_combo.config(state="readonly")
        else:
            self.target_language_combo.config(state="disabled")

    def browse_file(self):
        """Open file browser dialog."""
        filename = filedialog.askopenfilename(
            title="Select audio/video file",
            filetypes=SUPPORTED_FILE_TYPES
        )
        if filename:
            self.file_var.set(filename)

    def toggle_dark_mode(self):
        """Toggle dark/light mode."""
        self.theme_manager.toggle_dark_mode()
        self.apply_widget_styles()
        self.theme_manager.style_text_widget(self.result_text)

        # Update button text
        if self.theme_manager.is_dark_mode():
            self.dark_mode_btn.config(text="☀️ Light Mode")
        else:
            self.dark_mode_btn.config(text="🌙 Dark Mode")

    def start_transcription(self):
        """Start the transcription process."""
        if not self.file_var.get():
            messagebox.showerror("Error", "Please select a file first.")
            return

        # Reset state
        self.transcription_result = None
        self.diarization_result = None
        self.translated_segments = {}
        self.translation_service.clear_cache()
        self.temp_manager.cleanup()

        # Disable buttons
        self.transcribe_btn.config(state="disabled")
        self.save_btn.config(state="disabled")
        self.format_btn.config(state="disabled")
        self.export_subtitle_btn.config(state="disabled")
        self.export_translated_btn.config(state="disabled")

        # Reset progress
        self.progress['value'] = 0
        self.current_progress['value'] = 0
        self.set_status("Transcribing...", 'info')
        self.result_text.delete(1.0, tk.END)

        # Start transcription thread
        thread = threading.Thread(target=self.transcribe_audio)
        thread.daemon = True
        thread.start()

    def transcribe_audio(self):
        """Perform transcription in background thread."""
        try:
            file_path = self.file_var.get()

            # Load model
            self.root.after(0, lambda: self.set_status("Loading models...", 'info'))
            self.transcription_service.load_model(self.model_var.get())

            # Diarization
            if self.speaker_diarization_var.get():
                self._perform_diarization(file_path)

            # Transcription
            self.root.after(0, lambda: self.set_status("Processing audio...", 'info'))
            self.update_current_progress(0)

            language = self.source_language_var.get()
            task = "translate" if self.translate_var.get() and self.target_language_var.get() == "en" else "transcribe"

            def progress_callback(percentage):
                if self.speaker_diarization_var.get() and self.diarization_result:
                    mapped = 50 + int(percentage * 0.5)
                else:
                    mapped = percentage
                self.update_progress(mapped)
                self.update_current_progress(percentage)

            result = self.transcription_service.transcribe(
                file_path,
                language=language if language != "auto" else None,
                task=task,
                word_timestamps=self.word_timestamps_var.get(),
                verbose=False,
                progress_callback=progress_callback
            )

            self.update_progress(100)
            self.update_current_progress(100)
            self.transcription_result = result

            self.root.after(0, self.display_results)

        except Exception as e:
            self.temp_manager.cleanup()
            error_msg = f"Transcription failed: {str(e)}"
            self.root.after(0, lambda: self.handle_error(error_msg))

    def _perform_diarization(self, file_path: str):
        """Perform speaker diarization."""
        if not DiarizationService.is_available():
            self.root.after(0, lambda: self.set_status(
                "Speaker diarization unavailable (pyannote.audio not installed)", 'warning'))
            return

        try:
            if not self.diarization_service.is_loaded():
                self.root.after(0, lambda: self.set_status(
                    "Loading speaker diarization model...", 'info'))
                self.diarization_service.load_pipeline()

            self.root.after(0, lambda: self.set_status(
                "Performing speaker diarization...", 'info'))

            # Convert file if needed
            diarization_file = convert_to_wav(file_path)
            if diarization_file and diarization_file != file_path:
                self.temp_manager.add(diarization_file)

            if diarization_file:
                # Simulate progress
                self._simulate_diarization_progress()

                # Perform diarization
                self.diarization_result = self.diarization_service.diarize(diarization_file)

                self._diarization_cancelled = True
                self.update_progress(50)
                self.update_current_progress(100)
                self.root.after(0, lambda: self.set_status(
                    "Speaker diarization complete!", 'success'))
                time.sleep(0.5)

        except Exception as e:
            self.root.after(0, lambda: self.set_status(
                "Speaker diarization unavailable, continuing with transcription...", 'warning'))
            self.diarization_result = None

    def _simulate_diarization_progress(self):
        """Simulate diarization progress."""
        def simulate():
            for status, progress, duration in DIARIZATION_PROGRESS_STEPS:
                if hasattr(self, '_diarization_cancelled') and self._diarization_cancelled:
                    break

                def update_ui(s=status, p=progress):
                    self.set_status(s, 'info')
                    self.update_current_progress(p * 2)
                    self.update_progress(p)

                self.root.after(0, update_ui)
                time.sleep(duration)

        self._diarization_cancelled = False
        thread = threading.Thread(target=simulate)
        thread.daemon = True
        thread.start()

    def display_results(self):
        """Display transcription results."""
        self.result_text.delete(1.0, tk.END)

        # Check if translation needed
        if (self.translate_var.get() and
            self.target_language_var.get() != "en" and
            not self.translated_segments and
            self.transcription_result and
            'segments' in self.transcription_result):

            target_lang = self.target_language_var.get()
            self.set_status(f"Starting translation to {target_lang}...", 'info')

            thread = threading.Thread(
                target=self.translate_segments_background,
                args=(target_lang,)
            )
            thread.daemon = True
            thread.start()
            return

        # Display based on format
        if self.clean_format_var.get():
            self._display_clean_format()
        elif self.timestamps_var.get() and 'segments' in self.transcription_result:
            self._display_with_timestamps()
        else:
            text = self.transcription_result['text']
            if self.translate_var.get() and self.target_language_var.get() != "en":
                if "full_text" in self.translated_segments:
                    text = self.translated_segments["full_text"]
            self.result_text.insert(tk.END, text)

        # Update UI state
        self.progress['value'] = 100
        self.current_progress['value'] = 100
        self.set_status("Transcription complete!", 'success')
        self.transcribe_btn.config(state="normal")
        self.save_btn.config(state="normal")
        self.format_btn.config(state="normal")
        self.export_subtitle_btn.config(state="normal")
        self.export_translated_btn.config(state="normal")

    def _display_clean_format(self):
        """Display results in clean format."""
        for segment in self.transcription_result['segments']:
            start_time = format_timestamp(segment['start'])
            end_time = format_timestamp(segment['end'])
            text = ' '.join(segment['text'].strip().split())

            # Translation
            if self.translate_var.get() and self.target_language_var.get() != "en":
                segment_key = f"{segment['start']}_{segment['end']}"
                if segment_key in self.translated_segments:
                    text = self.translated_segments[segment_key]

            # Speaker
            speaker = self._get_speaker_at_segment(segment['start'])
            speaker_prefix = f"[{speaker}] " if speaker else ""

            self.result_text.insert(tk.END, f"[{start_time} - {end_time}] {speaker_prefix}{text}\n")

    def _display_with_timestamps(self):
        """Display results with detailed timestamps."""
        for segment in self.transcription_result['segments']:
            start_time = format_timestamp(segment['start'])
            end_time = format_timestamp(segment['end'])
            text = segment['text'].strip()

            segment_key = f"{segment['start']}_{segment['end']}"
            if self.translate_var.get() and self.target_language_var.get() != "en":
                if segment_key in self.translated_segments:
                    text = self.translated_segments[segment_key]

            speaker = self._get_speaker_at_segment(segment['start'])
            speaker_prefix = f"[{speaker}] " if speaker else ""

            if self.word_timestamps_var.get() and 'words' in segment:
                self.result_text.insert(tk.END, f"[{start_time} - {end_time}] {speaker_prefix}\n")

                # Word-level display (simplified for brevity)
                for word in segment.get('words', []):
                    word_start = format_timestamp(word['start'])
                    word_end = format_timestamp(word['end'])
                    word_text = word['word']
                    word_speaker = self._get_speaker_at_segment(word['start'])
                    word_speaker_prefix = f"[{word_speaker}] " if word_speaker else ""
                    self.result_text.insert(tk.END, f"  {word_start}-{word_end}: {word_speaker_prefix}{word_text}\n")

                self.result_text.insert(tk.END, f"Full segment: {speaker_prefix}{text}\n\n")
            else:
                self.result_text.insert(tk.END, f"[{start_time} - {end_time}] {speaker_prefix}{text}\n\n")

    def _get_speaker_at_segment(self, timestamp: float) -> str:
        """Get speaker at timestamp."""
        if self.speaker_diarization_var.get() and self.diarization_result:
            return self.diarization_service.get_speaker_at_time(timestamp, self.diarization_result)
        return None

    def translate_segments_background(self, target_lang: str):
        """Translate segments in background."""
        try:
            segments = self.transcription_result['segments']

            def progress_cb(current, total):
                progress = int((current / total) * 100)
                self.root.after(0, lambda: self.update_current_progress(progress))

            self.translated_segments = self.translation_service.translate_segments(
                segments,
                target_lang,
                progress_callback=progress_cb
            )

            # Translate full text
            if 'text' in self.transcription_result:
                full_text = self.transcription_result['text']
                self.translated_segments['full_text'] = self.translation_service.translate(
                    full_text, target_lang
                )

            self.root.after(0, lambda: self.update_current_progress(100))
            self.root.after(0, lambda: self.set_status("Translation complete! Updating display...", 'success'))
            self.root.after(0, self.display_results)

        except Exception as e:
            self.root.after(0, lambda: self.set_status(f"Translation error: {e}", 'error'))
            self.root.after(0, self.display_results)

    def update_progress(self, value: int):
        """Update overall progress bar."""
        def update():
            self.progress['value'] = value
        self.root.after(0, update)

    def update_current_progress(self, value: int):
        """Update current task progress bar."""
        def update():
            self.current_progress['value'] = value
        self.root.after(0, update)

    def handle_error(self, error_message: str):
        """Handle errors."""
        self.progress['value'] = 0
        self.current_progress['value'] = 0
        self.set_status("Error occurred", 'error')
        self.transcribe_btn.config(state="normal")
        messagebox.showerror("Error", error_message)

    def save_transcript(self):
        """Save transcript to file."""
        if not self.transcription_result:
            messagebox.showerror("Error", "No transcript to save.")
            return

        filename = filedialog.asksaveasfilename(
            title="Save transcript",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filename:
            try:
                if filename.lower().endswith('.json'):
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(self.transcription_result, f, indent=2, ensure_ascii=False)
                else:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(self.result_text.get(1.0, tk.END))

                messagebox.showinfo("Success", f"Transcript saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")

    def format_segments(self):
        """Format and save segments."""
        if not self.transcription_result:
            messagebox.showerror("Error", "No transcript to format.")
            return

        content = self.result_text.get(1.0, tk.END)
        segments = self._parse_segments_from_text(content)

        if not segments:
            messagebox.showwarning("Warning", "No segments found to format.")
            return

        filename = filedialog.asksaveasfilename(
            title="Save formatted segments",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    for segment in segments:
                        f.write(segment + '\n')
                messagebox.showinfo("Success", f"Processed {len(segments)} segments")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {str(e)}")

    def _parse_segments_from_text(self, content: str):
        """Parse segments from text content."""
        segments = []
        lines = content.strip().split('\n')

        for line in lines:
            line = line.strip()
            if line and re.match(r'\[\d{1,2}:\d{2}:\d{2} - \d{1,2}:\d{2}:\d{2}\]', line):
                segments.append(line)

        return segments

    def export_subtitles(self):
        """Export subtitles."""
        if not self.transcription_result or 'segments' not in self.transcription_result:
            messagebox.showerror("Error", "No transcript to export as subtitles.")
            return

        filename = filedialog.asksaveasfilename(
            title="Export subtitles",
            defaultextension=".srt",
            filetypes=[("SRT files", "*.srt"), ("WebVTT files", "*.vtt"), ("All files", "*.*")]
        )

        if filename:
            try:
                speaker_callback = lambda t: self._get_speaker_at_segment(t)

                if filename.lower().endswith('.vtt'):
                    self.subtitle_service.export_vtt(
                        filename,
                        self.transcription_result,
                        speaker_callback=speaker_callback
                    )
                else:
                    self.subtitle_service.export_srt(
                        filename,
                        self.transcription_result,
                        speaker_callback=speaker_callback
                    )

                messagebox.showinfo("Success", f"Subtitles exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export: {str(e)}")

    def export_translated_subtitles(self):
        """Export translated subtitles with language selection dialog."""
        if not self.transcription_result or 'segments' not in self.transcription_result:
            messagebox.showerror("Error", "No transcript to export.")
            return

        if not TranslationService.is_available():
            messagebox.showerror("Error", "Google Translate library not available.")
            return

        # Create language selection dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Export Translated Subtitles")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()

        # Apply theme
        theme = self.theme_manager.get_current_theme()
        dialog.configure(bg=theme['bg'])

        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Language selection
        ttk.Label(main_frame, text="Target Language:").grid(row=0, column=0, sticky=tk.W, pady=(0, 10))

        lang_var = tk.StringVar(value="Spanish")
        lang_combo = ttk.Combobox(
            main_frame,
            textvariable=lang_var,
            values=list(TRANSLATION_LANGUAGES.keys()),
            state="readonly",
            width=15
        )
        lang_combo.grid(row=0, column=1, sticky=tk.W, pady=(0, 10))

        # Format selection
        ttk.Label(main_frame, text="Format:").grid(row=1, column=0, sticky=tk.W, pady=(0, 10))

        format_var = tk.StringVar(value="SRT")
        format_combo = ttk.Combobox(
            main_frame,
            textvariable=format_var,
            values=["SRT", "WebVTT"],
            state="readonly",
            width=15
        )
        format_combo.grid(row=1, column=1, sticky=tk.W, pady=(0, 10))

        def export():
            target_lang = TRANSLATION_LANGUAGES[lang_var.get()]
            format_type = format_var.get()

            if format_type == "SRT":
                ext = ".srt"
                filetypes = [("SRT files", "*.srt"), ("All files", "*.*")]
            else:
                ext = ".vtt"
                filetypes = [("WebVTT files", "*.vtt"), ("All files", "*.*")]

            filename = filedialog.asksaveasfilename(
                title=f"Export Translated {format_type}",
                defaultextension=ext,
                filetypes=filetypes
            )

            if filename:
                try:
                    speaker_cb = lambda t: self._get_speaker_at_segment(t)
                    trans_cb = lambda text: self.translation_service.translate(text, target_lang)

                    if format_type == "SRT":
                        self.subtitle_service.export_srt(
                            filename,
                            self.transcription_result,
                            speaker_callback=speaker_cb,
                            translation_callback=trans_cb
                        )
                    else:
                        self.subtitle_service.export_vtt(
                            filename,
                            self.transcription_result,
                            speaker_callback=speaker_cb,
                            translation_callback=trans_cb
                        )

                    messagebox.showinfo("Success", f"Translated subtitles exported to {filename}")
                    dialog.destroy()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to export: {str(e)}")

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0))

        ttk.Button(button_frame, text="Export", command=export, style='App.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy, style='App.TButton').pack(side=tk.LEFT, padx=5)

    def on_closing(self):
        """Handle window close event."""
        self.temp_manager.cleanup()
        self.root.destroy()
