"""
pytest conftest — Python 3.14 stdout/stderr guard.
The app wraps sys.stdout/stderr with TextIOWrapper at import time.
pytest's capture plugin then tries to close those wrappers, which
causes "I/O operation on closed file." This guard prevents re-wrapping
when the buffers are already wrapped.
"""
import sys
import io


def _guard_streams():
    """Replace sys.stdout/stderr with plain StringIO wrappers pytest can safely close."""
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name)
        # If it's already a TextIOWrapper around a buffer, replace with a
        # safe wrapper that won't raise on close
        if hasattr(stream, "buffer"):
            safe = io.TextIOWrapper(
                stream.buffer,
                encoding="utf-8",
                errors="replace",
                line_buffering=True,
            )
            # Prevent double-close errors
            original_close = safe.close
            def _safe_close(orig=original_close):
                try:
                    orig()
                except Exception:
                    pass
            safe.close = _safe_close
            setattr(sys, stream_name, safe)


_guard_streams()
