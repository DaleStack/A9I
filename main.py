import time
import threading
import sys
import pyperclip
import pyautogui
import ollama
from pynput import keyboard

MODEL = "translategemma:4b"
HOTKEY_STR = '<ctrl>+<alt>+s'

class Loader:
    def __init__(self):
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._animate, daemon=True)

    def _animate(self):
        chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        i = 0
        while not self.stop_event.is_set():
            sys.stdout.write(f'\r[A9I] {chars[i % len(chars)]} Thinking...')
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1

    def start(self): self.thread.start()
    def stop(self):
        self.stop_event.set()
        self.thread.join()
        sys.stdout.write('\r' + ' ' * 20 + '\r')
        sys.stdout.flush()

_lock = threading.Lock()

def get_selected_text():
    old_clipboard = pyperclip.paste()
    print(f"[DEBUG] 1. Old clipboard: '{old_clipboard}'")
    
    pyperclip.copy('')
    print(f"[DEBUG] 2. Clipboard cleared")
    
    time.sleep(0.5)  # wait before firing Ctrl+C
    pyautogui.hotkey('ctrl', 'c')
    print(f"[DEBUG] 3. Ctrl+C fired")
    
    time.sleep(0.5)
    text = pyperclip.paste()
    print(f"[DEBUG] 4. Clipboard after copy: '{text}'")
    
    text = text.strip()
    if not text:
        pyperclip.copy(old_clipboard)
        return "", old_clipboard
    return text, old_clipboard

def a9i_engine():
    text, old_clipboard = get_selected_text()

    if not text:
        print("[A9I] No text selected.")
        return

    word_count = len(text.split())
    prompt = f"To English: {text}" if word_count > 2 else f"Define and translate: {text}"

    loader = Loader()
    loader.start()

    try:
        response = ollama.generate(model=MODEL, prompt=prompt)
        result = response['response'].strip()
        loader.stop()
        print(f"✨ A9I: {result}")

    except Exception as e:
        loader.stop()
        print(f"\n[A9I] Error: {e}")

    finally:
        pyperclip.copy(old_clipboard)

def _run_engine():
    try:
        a9i_engine()
    finally:
        _lock.release()

def on_hotkey():
    if not _lock.acquire(blocking=False):
        return
    threading.Thread(target=_run_engine, daemon=True).start()

def run_a9i():
    print(f"🚀 A9I Core Active | Hotkey: {HOTKEY_STR}")
    with keyboard.GlobalHotKeys({HOTKEY_STR: on_hotkey}) as h:
        h.join()

if __name__ == "__main__":
    run_a9i()