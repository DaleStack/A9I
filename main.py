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
# 1. Define your two specialized models here
TRANSLATE_MODEL = "a9i-translate:latest"
DEFINE_MODEL = "a9i-define:latest"

# 2. Define your hotkeys
TRANSLATE_HOTKEY = '<ctrl>+<alt>+t'
DEFINE_HOTKEY = '<ctrl>+<alt>+d'

# --- Signal Bridge ---
class Communicate(QObject):
    display_signal = pyqtSignal(str, QPoint)
    loading_signal = pyqtSignal(QPoint, str) 
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

        self._dot_count = 0
        self._loading_timer = QTimer()
        self._loading_timer.setInterval(400)
        self._loading_timer.timeout.connect(self._animate_dots)

        self._fading_out = False
        self._is_loading = False
        self._action_text = "Thinking"

    def _on_animation_finished(self):
        if self._fading_out:
            self._fading_out = False
            self.hide()
            self.setWindowOpacity(0.0)

    def show_loading(self, pos, mode):
        self.fade_animation.stop()
        self.hide_timer.stop()
        self._fading_out = False
        self._is_loading = True
        self._dot_count = 0
        
        # Update text based on mode
        self._action_text = "Translating" if mode == "translate" else "Defining"

        self.label.setStyleSheet("""
            QLabel {
                background-color: rgba(20, 20, 20, 240);
                color: #888888;
                border: 1px solid #2a2a2a;
                border-radius: 15px;
                padding: 20px;
            }
        """)
        self.label.setText(f"A9I {self._action_text}...")
        self.adjustSize()
        self.move(pos.x() + 25, pos.y() + 25)

        self.show()
        self.fade_animation.setStartValue(self.windowOpacity())
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()
        self._loading_timer.start()

    def _animate_dots(self):
        if not self._is_loading: 
            return
        self._dot_count = (self._dot_count + 1) % 4
        dots = "." * self._dot_count
        self.label.setText(f"A9I {self._action_text}{dots}")

    def show_translation(self, text, pos):
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
        if not self.isVisible():
            self.move(pos.x() + 25, pos.y() + 25)

        self.show()
        self.fade_animation.setStartValue(self.windowOpacity())
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()
        self.hide_timer.start(7000)

    def dismiss(self):
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
    time.sleep(0.3) 
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

def a9i_worker(comm, mode):
    global is_running
    if is_running: 
        return
    is_running = True

    try:
        mouse_pos = QCursor.pos()
        comm.loading_signal.emit(mouse_pos, mode)

        text, old_clipboard = get_selected_text()
        if not text:
            comm.dismiss_signal.emit()
            is_running = False
            return

        # 3. SELECT THE CORRECT MODEL
        if mode == "translate":
            target_model = TRANSLATE_MODEL
        else:
            target_model = DEFINE_MODEL
            
        # 4. SEND RAW TEXT (Let the specialized model handle the logic)
        response = ollama.generate(
            model=target_model, 
            prompt=text,
            options={"temperature": 0.0}
        )
        result = response['response'].strip()

        comm.display_signal.emit(result, mouse_pos)

    except Exception as e:
        print(f"Error: {e}")
        comm.dismiss_signal.emit()
    finally:
        # Restore clipboard if we grabbed something
        if 'old_clipboard' in locals() and old_clipboard:
            pyperclip.copy(old_clipboard)
        is_running = False


# --- Main Entry ---
def main():
    app = QApplication(sys.argv)
    ghost_frame = A9IFrame()
    comm = Communicate()

    comm.loading_signal.connect(ghost_frame.show_loading)
    comm.display_signal.connect(ghost_frame.show_translation)
    comm.dismiss_signal.connect(ghost_frame.dismiss)

    # 5. Define separate triggers
    def trigger_translate():
        threading.Thread(target=a9i_worker, args=(comm, "translate"), daemon=True).start()

    def trigger_define():
        threading.Thread(target=a9i_worker, args=(comm, "define"), daemon=True).start()

    # 6. Map hotkeys to triggers
    listener = keyboard.GlobalHotKeys({
        TRANSLATE_HOTKEY: trigger_translate,
        DEFINE_HOTKEY: trigger_define
    })
    listener.start()

    print("🚀 A9I Dual-Core Active")
    print(f"   [T] Translate: {TRANSLATE_HOTKEY} -> {TRANSLATE_MODEL}")
    print(f"   [D] Define:    {DEFINE_HOTKEY}    -> {DEFINE_MODEL}")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()