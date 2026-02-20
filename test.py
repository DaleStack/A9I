from pynput import keyboard
import threading

_lock = threading.Lock()

def on_activate():
    """Testing hotkey activation."""
    if not _lock.acquire(blocking=False):
        return  # already running, ignore repeat
    try:
        print("Hotkey fired!")
    finally:
        _lock.release()

with keyboard.GlobalHotKeys({'<ctrl>+<alt>+s': on_activate}) as h:
    h.join()