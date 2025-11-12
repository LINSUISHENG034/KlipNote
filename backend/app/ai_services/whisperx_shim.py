"""
Utility to expose the vendored WhisperX package under the canonical ``whisperx`` name.

The repo keeps the upstream project checked in under ``app.ai_services.whisperx.whisperx``.
Some modules (e.g., audio helpers) still import ``whisperx.utils`` etc., so we register the
vendored package in :mod:`sys.modules` before those imports run.
"""

from importlib import import_module
import sys

_VENDOR_PACKAGE = "app.ai_services.whisperx.whisperx"


def ensure_whisperx_available() -> None:
    """Register the vendored WhisperX package so absolute imports succeed."""
    if "whisperx" not in sys.modules:
        sys.modules["whisperx"] = import_module(_VENDOR_PACKAGE)

