import sys
import time
import threading
import pyperclip
import pyautogui
import ollama
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer, QPoint, pyqtSignal, QObject
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
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowOpacity(0.0)

        layout = QVBoxLayout()
        self.label = QLabel("A9I Thinking...")
        self.label.setStyleSheet("""
            QLabel {
                background-color: rgba(20, 20, 20, 240);
                color: #00FF99;
                border: 1px solid #333;
                border-radius: 15px;
                padding: 20px;
            }
        """)
        self.label.setFont(QFont("Inter", 11, QFont.Weight.Medium))
        self.label.setWordWrap(True)
        self.label.setFixedWidth(350)
        layout.addWidget(self.label)
        self.setLayout(layout)

        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(250)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        # Connect hide ONCE here, not repeatedly in start_fade_out
        self.fade_animation.finished.connect(self._on_animation_finished)

        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.start_fade_out)
        
        self._fading_out = False

    def _on_animation_finished(self):
        if self._fading_out:
            self._fading_out = False
            self.hide()
            self.setWindowOpacity(0.0)

    def show_translation(self, text, pos):
        # Stop whatever animation is running
        self.fade_animation.stop()
        self.hide_timer.stop()
        self._fading_out = False

        self.label.setText(text)
        self.adjustSize()
        self.move(pos.x() + 25, pos.y() + 25)

        self.show()
        self.fade_animation.setStartValue(self.windowOpacity())  # animate from current opacity
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()

        self.hide_timer.start(7000)

    def start_fade_out(self):
        self.fade_animation.stop()
        self._fading_out = True
        self.fade_animation.setStartValue(self.windowOpacity())  # animate from current opacity
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.start()

    def mousePressEvent(self, event):
        self.hide_timer.stop()
        self.start_fade_out()

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