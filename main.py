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
    # Carries the result text and the mouse position
    display_signal = pyqtSignal(str, QPoint)
    # Triggers the loading state at a given mouse position
    loading_signal = pyqtSignal(QPoint)
    # Dismisses the frame (e.g. no text was selected)
    dismiss_signal = pyqtSignal()

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
        self.label = QLabel("")
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
        self.fade_animation.finished.connect(self._on_animation_finished)

        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.start_fade_out)

        # Animated ellipsis timer for the loading state
        self._dot_count = 0
        self._loading_timer = QTimer()
        self._loading_timer.setInterval(400)
        self._loading_timer.timeout.connect(self._animate_dots)

        self._fading_out = False
        self._is_loading = False

    def _on_animation_finished(self):
        if self._fading_out:
            self._fading_out = False
            self.hide()
            self.setWindowOpacity(0.0)

    def show_loading(self, pos):
        """Called immediately when the hotkey fires."""
        self.fade_animation.stop()
        self.hide_timer.stop()
        self._fading_out = False
        self._is_loading = True
        self._dot_count = 0

        self.label.setStyleSheet("""
            QLabel {
                background-color: rgba(20, 20, 20, 240);
                color: #888888;
                border: 1px solid #2a2a2a;
                border-radius: 15px;
                padding: 20px;
            }
        """)
        self.label.setText("A9I Thinking...")
        self.adjustSize()
        self.move(pos.x() + 25, pos.y() + 25)

        self.show()
        self.fade_animation.setStartValue(self.windowOpacity())
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()

        self._loading_timer.start()

    def _animate_dots(self):
        """Cycles the ellipsis while loading."""
        if not self._is_loading:
            return
        self._dot_count = (self._dot_count + 1) % 4
        dots = "." * self._dot_count
        self.label.setText(f"A9I Thinking{dots}")

    def show_translation(self, text, pos):
        """Called when the AI response is ready."""
        self._loading_timer.stop()
        self._is_loading = False

        self.fade_animation.stop()
        self.hide_timer.stop()
        self._fading_out = False

        self.label.setStyleSheet("""
            QLabel {
                background-color: rgba(20, 20, 20, 240);
                color: #00FF99;
                border: 1px solid #333;
                border-radius: 15px;
                padding: 20px;
            }
        """)
        self.label.setText(text)
        self.adjustSize()
        # Keep the same position if already visible; only reposition if hidden
        if not self.isVisible():
            self.move(pos.x() + 25, pos.y() + 25)

        self.show()
        self.fade_animation.setStartValue(self.windowOpacity())
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()

        self.hide_timer.start(7000)

    def dismiss(self):
        """Called when no text was selected — hide the loading frame."""
        self._loading_timer.stop()
        self._is_loading = False
        self.start_fade_out()

    def start_fade_out(self):
        self._loading_timer.stop()
        self._is_loading = False
        self.fade_animation.stop()
        self._fading_out = True
        self.fade_animation.setStartValue(self.windowOpacity())
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.start()

    def mousePressEvent(self, event):
        self.hide_timer.stop()
        self.start_fade_out()


# --- The Logic Engine ---
def get_selected_text():
    old_clipboard = pyperclip.paste()
    pyperclip.copy('')

    time.sleep(0.3)  # Wait for finger release

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

    old_clipboard = ""
    try:
        # Capture mouse position and show loading state IMMEDIATELY
        mouse_pos = QCursor.pos()
        comm.loading_signal.emit(mouse_pos)

        text, old_clipboard = get_selected_text()
        if not text:
            comm.dismiss_signal.emit()
            return

        # Call Ollama
        response = ollama.generate(model=MODEL, prompt=text)
        result = response['response'].strip()

        # Emit result to the UI thread
        comm.display_signal.emit(result, mouse_pos)

    except Exception as e:
        print(f"Error: {e}")
        comm.dismiss_signal.emit()
    finally:
        pyperclip.copy(old_clipboard)
        is_running = False


# --- Main Entry ---
def main():
    app = QApplication(sys.argv)

    ghost_frame = A9IFrame()
    comm = Communicate()

    # Wire up signals
    comm.loading_signal.connect(ghost_frame.show_loading)
    comm.display_signal.connect(ghost_frame.show_translation)
    comm.dismiss_signal.connect(ghost_frame.dismiss)

    def trigger_worker():
        threading.Thread(target=a9i_worker, args=(comm,), daemon=True).start()

    listener = keyboard.GlobalHotKeys({HOTKEY_STR: trigger_worker})
    listener.start()

    print(f"🚀 A9I Ghost Frame Active | {HOTKEY_STR}")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()