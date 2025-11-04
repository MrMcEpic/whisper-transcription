"""System-specific utility functions."""

import winreg


def detect_windows_dark_mode() -> bool:
    """
    Detect if Windows is using dark mode.

    Returns:
        True if dark mode is enabled, False otherwise
    """
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize'
        )
        value, _ = winreg.QueryValueEx(key, 'AppsUseLightTheme')
        winreg.CloseKey(key)
        return value == 0  # 0 = dark mode, 1 = light mode
    except Exception:
        return False  # Default to light mode if detection fails
