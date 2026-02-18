import time
import threading
import sys
import pyperclip
import pyautogui
import ollama
from pynput import keyboard

MODEL = "a9i-model:latest"
HOTKEY_STR = '<ctrl>+<alt>+s'

class Loader:
    def __init__(self):
        self.stop_event = threading.Event()
        # daemon=True ensures the spinner stops if the main script exits
        self.thread = threading.Thread(target=self._animate, daemon=True)

    def _animate(self):
        chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        i = 0
        while not self.stop_event.is_set():
            # \r moves the cursor back to the start of the line
            sys.stdout.write(f'\r[A9I] {chars[i % len(chars)]} Thinking...')
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1

    def start(self): 
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        self.thread.join()
        # Clean the line after stopping
        sys.stdout.write('\r' + ' ' * 30 + '\r')
        sys.stdout.flush()

# --- The Reliable Grabber ---
def get_selected_text():
    old_clipboard = pyperclip.paste()
    pyperclip.copy('') # Clear to detect a fresh copy
    
    # 1. WAIT for the user to release the physical hotkeys.
    # If Alt is still physically held, Ctrl+C becomes Ctrl+Alt+C.
    time.sleep(0.3) 
    
    # 2. Fire Ctrl+C. 
    # keyDown/keyUp is more forceful than 'hotkey()' for the OS buffer.
    pyautogui.keyDown('ctrl')
    pyautogui.press('c')
    pyautogui.keyUp('ctrl')
    
    # 3. Retry Loop: Wait up to 0.7s for the clipboard to actually update.
    # OS clipboard operations are asynchronous and can be slow.
    for _ in range(7):
        time.sleep(0.1)
        text = pyperclip.paste().strip()
        if text:
            return text, old_clipboard
            
    return "", old_clipboard

# --- The Engine ---
def a9i_engine():
    # Use a global flag to prevent multiple triggers if you spam the key
    global is_running
    if is_running: 
        return
    is_running = True

    try:
        text, old_clipboard = get_selected_text()
        if not text:
            # Silent fail for invisible feel, or debug print:
            # print("[A9I] No text captured.")
            return

        loader = Loader()
        loader.start()

        # Call your custom A9I Modelfile
        response = ollama.generate(model=MODEL, prompt=text)
        result = response['response'].strip()
        
        loader.stop()
        print(f"✨ A9I: {result}")

    except Exception as e:
        if 'loader' in locals(): 
            loader.stop()
        print(f"\n[A9I] Error: {e}")
    finally:
        # Restore the original clipboard so your workflow isn't disrupted
        pyperclip.copy(old_clipboard)
        is_running = False

is_running = False

def on_hotkey():
    # Always run the logic in a separate thread to keep the listener responsive
    threading.Thread(target=a9i_engine, daemon=True).start()

def run_a9i():
    print(f"🚀 A9I Core Active | Hotkey: {HOTKEY_STR}")
    with keyboard.GlobalHotKeys({HOTKEY_STR: on_hotkey}) as h:
        h.join()

if __name__ == "__main__":
    run_a9i()