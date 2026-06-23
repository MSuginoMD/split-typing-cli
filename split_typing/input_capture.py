from __future__ import annotations

import sys
from contextlib import contextmanager

try:
    import termios
    import tty
    _HAVE_TERMIOS = True
except ImportError:
    _HAVE_TERMIOS = False


def supports_raw() -> bool:
    return _HAVE_TERMIOS and sys.stdin.isatty() and sys.stdout.isatty()


@contextmanager
def raw_terminal():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        yield
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def read_keys():
    """Yield one character at a time in raw mode. Ctrl-C -> KeyboardInterrupt."""
    with raw_terminal():
        while True:
            ch = sys.stdin.read(1)
            if ch == "\x03":  # Ctrl-C
                raise KeyboardInterrupt
            yield ch
