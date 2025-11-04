"""Theme management for the GUI application."""

import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
from typing import Optional

from ..config import DARK_THEME, LIGHT_THEME, DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE
from ..utils.system_utils import detect_windows_dark_mode


class ThemeManager:
    """Manages application theming (light/dark mode)."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.dark_mode = tk.BooleanVar()
        self.app_font = tkfont.Font(family=DEFAULT_FONT_FAMILY, size=DEFAULT_FONT_SIZE)
        self.style = ttk.Style()

        # Detect and apply system theme
        system_dark = detect_windows_dark_mode()
        self.dark_mode.set(system_dark)

    def get_current_theme(self) -> dict:
        """Get the current theme colors."""
        return DARK_THEME if self.dark_mode.get() else LIGHT_THEME

    def get_color(self, color_type: str) -> str:
        """Get a specific color from the current theme."""
        theme = self.get_current_theme()
        return theme.get(color_type, '#cccccc')

    def apply_theme(self):
        """Apply the current theme to all widgets."""
        theme = self.get_current_theme()

        # Configure root window
        self.root.configure(bg=theme['bg'])

        # Use clam theme as base
        self.style.theme_use('clam')

        # Configure frames and labels
        self.style.configure('TFrame', background=theme['bg'], borderwidth=0)
        self.style.configure('TLabel', background=theme['bg'], foreground=theme['fg'])

        # Configure buttons
        self.style.configure(
            'App.TButton',
            background=theme['button_bg'],
            foreground=theme['button_fg'],
            borderwidth=1,
            focuscolor='none',
            relief='flat',
            padding=(10, 6),
            font=self.app_font
        )
        self.style.map(
            'App.TButton',
            background=[('active', theme['button_hover']), ('pressed', theme['select_bg'])],
            relief=[('pressed', 'flat'), ('!pressed', 'flat')]
        )

        # Configure readonly entry
        self.style.configure(
            f'{self._theme_prefix()}.Readonly.TEntry',
            fieldbackground=theme['entry_readonly_bg'],
            foreground=theme['entry_readonly_fg'],
            insertcolor=theme['entry_fg'],
            bordercolor=theme['border'],
            lightcolor=theme['border'],
            darkcolor=theme['border'],
            relief='flat',
            focuscolor='none'
        )

        # Configure combobox
        self.style.configure(
            f'{self._theme_prefix()}.TCombobox',
            fieldbackground=theme['entry_bg'],
            background=theme['entry_bg'],
            foreground=theme['entry_fg'],
            arrowcolor=theme['fg'],
            bordercolor=theme['border'],
            lightcolor=theme['border'],
            darkcolor=theme['border'],
            relief='flat',
            focuscolor=theme['button_bg'],
            selectbackground=theme['select_bg'],
            selectforeground=theme['entry_fg']
        )
        self.style.map(
            f'{self._theme_prefix()}.TCombobox',
            fieldbackground=[('readonly', theme['entry_bg'])],
            background=[('active', theme['entry_bg']), ('!active', theme['entry_bg'])],
            foreground=[('readonly', theme['entry_fg'])]
        )

        # Configure checkbuttons and radiobuttons
        for widget_type in ('TCheckbutton', 'TRadiobutton'):
            self.style.configure(
                widget_type,
                background=theme['bg'],
                foreground=theme['fg'],
                focuscolor='none'
            )
            self.style.map(
                widget_type,
                background=[('active', theme['bg']), ('selected', theme['bg']), ('disabled', theme['bg'])],
                foreground=[('disabled', '#777777' if self.dark_mode.get() else '#888888')]
            )

        # Configure progress bar
        progress_color = theme['button_bg'] if self.dark_mode.get() else '#4caf50'
        self.style.configure(
            'TProgressbar',
            background=progress_color,
            troughcolor=theme['entry_bg'] if self.dark_mode.get() else '#e6e6e6',
            borderwidth=0,
            lightcolor=progress_color,
            darkcolor=progress_color
        )

        # Configure scrollbar
        scrollbar_bg = theme['button_bg'] if self.dark_mode.get() else '#bdbdbd'
        self.style.configure(
            f"{self._theme_prefix()}.Vertical.TScrollbar",
            troughcolor=theme['entry_bg'] if self.dark_mode.get() else '#e6e6e6',
            background=scrollbar_bg,
            bordercolor=theme['border'],
            lightcolor=scrollbar_bg,
            darkcolor=scrollbar_bg,
            arrowcolor=theme['fg']
        )
        self.style.map(
            f"{self._theme_prefix()}.Vertical.TScrollbar",
            background=[('active', theme['button_hover']), ('pressed', theme['select_bg'])]
        )

        # Configure indicator-less radiobutton
        self.style.layout('IndicatorLess.TRadiobutton', [
            ('Radiobutton.padding', {
                'children': [
                    ('Radiobutton.focus', {
                        'children': [('Radiobutton.label', {'sticky': 'nswe'})],
                        'sticky': 'nswe'
                    })
                ],
                'sticky': 'nswe'
            })
        ])
        self.style.configure(
            'IndicatorLess.TRadiobutton',
            background=theme['bg'],
            foreground=theme['fg'],
            focuscolor='none',
            padding=(2, 0)
        )

    def style_text_widget(self, text_widget: tk.Text):
        """Apply theme to a Text widget."""
        theme = self.get_current_theme()

        if self.dark_mode.get():
            text_widget.configure(
                bg=theme['bg'],
                fg=theme['fg'],
                insertbackground="#ffffff",
                selectbackground=theme['select_bg'],
                selectforeground="#ffffff",
                relief='flat'
            )
        else:
            text_widget.configure(
                bg="white",
                fg="black",
                insertbackground="black",
                selectbackground="#0078d4",
                selectforeground="white",
                relief='flat'
            )

    def style_combobox_popup(self, combobox: ttk.Combobox):
        """Style the combobox dropdown list."""
        theme = self.get_current_theme()

        try:
            popdown = combobox.tk.call("ttk::combobox::PopdownWindow", combobox)
            lb_path = f"{popdown}.f.l"

            combobox.tk.call(
                lb_path, "configure",
                "-background", theme['entry_bg'],
                "-foreground", theme['entry_fg'],
                "-selectbackground", theme['select_bg'],
                "-selectforeground", theme['entry_fg'],
                "-borderwidth", 0,
                "-highlightthickness", 0
            )
            combobox.tk.call(
                f"{popdown}.f", "configure",
                "-borderwidth", 0,
                "-background", theme['entry_bg']
            )
        except tk.TclError:
            pass

    def toggle_dark_mode(self):
        """Toggle between light and dark mode."""
        self.dark_mode.set(not self.dark_mode.get())
        self.apply_theme()

    def _theme_prefix(self) -> str:
        """Get the theme prefix for styling."""
        return "Dark" if self.dark_mode.get() else "Light"

    def is_dark_mode(self) -> bool:
        """Check if dark mode is currently active."""
        return self.dark_mode.get()
