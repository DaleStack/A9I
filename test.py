from pynput import keyboard
import threading

_lock = threading.Lock()

def on_activate():
    if not _lock.acquire(blocking=False):
        return  # already running, ignore repeat
    try:
        print("Hotkey fired!")
        # your a9i_engine() goes here
    finally:
        _lock.release()

with keyboard.GlobalHotKeys({'<ctrl>+<alt>+s': on_activate}) as h:
    h.join()