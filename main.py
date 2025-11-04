"""Main entry point for the Whisper Transcription Tool."""

# Suppress warnings before any imports
import warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message=".*deprecated.*")
warnings.filterwarnings("ignore", message=".*TensorFloat-32.*")
warnings.filterwarnings("ignore", message=".*torchaudio.*")
warnings.filterwarnings("ignore", message=".*Triton kernels.*")
warnings.filterwarnings("ignore", message=".*torch.backends.*")
warnings.filterwarnings("ignore", message=".*list_audio_backends.*")
warnings.filterwarnings("ignore", message=".*TorchCodec.*")
warnings.filterwarnings("ignore", module="pyannote.*")
warnings.filterwarnings("ignore", module="torchaudio.*")

import sys
import tkinter as tk

from src.cli import create_cli_parser, run_cli_mode
from src.ui import WhisperGUI


def main():
    """Main application entry point."""
    parser = create_cli_parser()
    args = parser.parse_args()

    if args.cli:
        # Run in CLI mode
        return run_cli_mode(args)
    else:
        # Run GUI mode
        root = tk.Tk()
        app = WhisperGUI(root)
        root.mainloop()
        return 0


if __name__ == "__main__":
    sys.exit(main())
