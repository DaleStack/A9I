import sys
import time
import threading
import pyperclip
import pyautogui
import ollama
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer, QPoint, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QCursor
from pynput import keyboard

# --- Configuration ---
MODEL = "a9i-model:latest"
HOTKEY_STR = '<ctrl>+<alt>+s'

# --- Signal Bridge ---
class Communicate(QObject):
    # This signal carries the result text and the mouse position
    display_signal = pyqtSignal(str, QPoint)

# --- The "Ghost" UI ---
class A9IFrame(QWidget):
    def __init__(self):
        super().__init__()
        # 1. Stripped Frame: No title bar, no taskbar icon, stays on top
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        # 2. Translucent for rounded corners effect
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        layout = QVBoxLayout()
        self.label = QLabel("A9I is thinking...")
        self.label.setStyleSheet("""
            QLabel {
                background-color: rgba(20, 20, 20, 240);
                color: #00FF99;
                border: 1px solid #333;
                border-radius: 15px;
                padding: 20px;
            }
        """)
        # Using a clean font
        self.label.setFont(QFont("Inter", 11, QFont.Weight.Medium))
        self.label.setWordWrap(True)
        self.label.setFixedWidth(350) # Manageable width for definitions
        
        layout.addWidget(self.label)
        self.setLayout(layout)
        
        # 3. Auto-hide timer
        self.hide_timer = QTimer()
        self.hide_timer.timeout.connect(self.hide)

    def show_translation(self, text, pos):
        self.label.setText(text)
        self.adjustSize()
        
        # Move the frame near the cursor (offset slightly so it's not under the mouse)
        self.move(pos.x() + 25, pos.y() + 25)
        self.show()
        
        # Start 7-second countdown to disappear
        self.hide_timer.start(7000)

# --- The Logic Engine ---
def get_selected_text():
    old_clipboard = pyperclip.paste()
    pyperclip.copy('')
    
    time.sleep(0.3) # Wait for finger release
    
    pyautogui.keyDown('ctrl')
    pyautogui.press('c')
    pyautogui.keyUp('ctrl')
    
    for _ in range(7):
        time.sleep(0.1)
        text = pyperclip.paste().strip()
        if text:
            return text, old_clipboard
    return "", old_clipboard

is_running = False

def a9i_worker(comm):
    global is_running
    if is_running: 
        return
    is_running = True

    try:
        text, old_clipboard = get_selected_text()
        if not text:
            is_running = False
            return

        # Capture mouse position right now
        mouse_pos = QCursor.pos()
        
        # Call Ollama
        response = ollama.generate(model=MODEL, prompt=text)
        result = response['response'].strip()
        
        # Emit signal to the UI thread
        comm.display_signal.emit(result, mouse_pos)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        pyperclip.copy(old_clipboard)
        is_running = False

# --- Main Entry ---
def main():
    # Initialize the App
    app = QApplication(sys.argv)
    
    # Setup UI and Signal Bridge
    ghost_frame = A9IFrame()
    comm = Communicate()
    comm.display_signal.connect(ghost_frame.show_translation)

    # Keyboard Listener setup
    def trigger_worker():
        threading.Thread(target=a9i_worker, args=(comm,), daemon=True).start()

    listener = keyboard.GlobalHotKeys({HOTKEY_STR: trigger_worker})
    listener.start()

    print(f"🚀 A9I Ghost Frame Active | {HOTKEY_STR}")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()