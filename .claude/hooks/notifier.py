"""
Claude Code hook: plays a short sound notification when Claude finishes
responding (a "Stop" hook).


Cross-platform: detects the OS at runtime and uses the appropriate
mechanism to play a system sound (afplay on macOS, winsound on
Windows, paplay/aplay/canberra-gtk-play on Linux). If no sound backend
is available, falls back to the terminal bell character. Never raises
or blocks -- a notification hook should never break the session it's
attached to.
"""

import platform
import subprocess
import sys

__author__ = "boltelvee"
__version__ = "1.0.0"

MACOS_SOUND_FILE = "/System/Library/Sounds/Glass.aiff"
LINUX_SOUND_CANDIDATES = [
    ("paplay", ["/usr/share/sounds/freedesktop/stereo/complete.oga"]),
    ("aplay", ["/usr/share/sounds/alsa/Front_Center.wav"]),
    ("canberra-gtk-play", ["-i", "complete"]),
]
SUBPROCESS_TIMEOUT_SECONDS = 5


def play_sound_macos() -> bool:
    """
    Play the system sound via afplay. Returns True on success.
    """
    try:
        subprocess.run(
            ["afplay", MACOS_SOUND_FILE], check=True, timeout=SUBPROCESS_TIMEOUT_SECONDS
        )
        return True
    except Exception:
        return False


def play_sound_windows() -> bool:
    """
    Play the system asterisk sound via the built-in winsound module.
    """
    try:
        import winsound

        winsound.MessageBeep(winsound.MB_ICONASTERISK)
        return True
    except Exception:
        return False


def play_sound_linux() -> bool:
    """
    Try known Linux sound players in order until one works.
    """
    for executable, args in LINUX_SOUND_CANDIDATES:
        try:
            subprocess.run(
                [executable, *args],
                check=True,
                timeout=SUBPROCESS_TIMEOUT_SECONDS,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            continue
    return False


def play_terminal_bell() -> None:
    """
    Last-resort fallback: the ASCII bell character most terminals honor.
    """
    sys.stdout.write("\a")
    sys.stdout.flush()


def notify() -> None:
    """
    Play a completion sound using whatever backend fits the current OS.
    """
    system = platform.system()

    played = False
    if system == "Darwin":
        played = play_sound_macos()
    elif system == "Windows":
        played = play_sound_windows()
    elif system == "Linux":
        played = play_sound_linux()

    if not played:
        play_terminal_bell()


def main() -> None:
    # Consume stdin so Claude Code doesn't wait on an unread pipe; the
    # Stop event's payload itself isn't needed for a sound notification.
    sys.stdin.read()

    try:
        notify()
    except Exception:
        # A notification hook must never fail the session it's attached to.
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
