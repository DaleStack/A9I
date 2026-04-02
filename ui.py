from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox
from PyQt6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    Qt,
    QTimer,
    QPoint,
    pyqtSignal,
    QObject,
)
from PyQt6.QtGui import QFont


class Communicate(QObject):
    # Step 1: UI needs to know to show the selector
    request_selection_signal = pyqtSignal(str, list, str, QPoint)

    # Step 2: UI tells Engine the user made a choice
    language_selected_signal = pyqtSignal(str, str, str, QPoint)

    # Step 3 & 4: Loading and Display
    loading_signal = pyqtSignal(QPoint, str)
    display_signal = pyqtSignal(str, QPoint)
    dismiss_signal = pyqtSignal()


class A9IFrame(QWidget):
    def __init__(self, comm):
        super().__init__()
        self.comm = comm
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowOpacity(0.0)

        self.layout = QVBoxLayout()

        # --- The Label (For Loading and Results) ---
        self.label = QLabel("")
        self.label.setStyleSheet("""
            QLabel {
                background-color: rgba(20, 20, 20, 240);
                color: #00FF99;
                border: 1px solid #333;
                border-radius: 12px;
                padding: 15px;
            }
        """)
        self.label.setFont(QFont("Inter", 11, QFont.Weight.Medium))
        self.label.setWordWrap(True)
        self.label.setFixedWidth(350)
        self.label.hide()  # Hidden by default

        # --- The Dropdown (For Language Selection) ---
        self.combo = QComboBox()
        self.combo.setStyleSheet("""
            QComboBox {
                background-color: rgba(30, 30, 30, 250);
                color: #FFF;
                border: 1px solid #555;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
            }
            QComboBox::drop-down { border: none; }
        """)
        self.combo.setFixedWidth(250)
        self.combo.hide()  # Hidden by default
        # When an item is selected, trigger the next step
        self.combo.activated.connect(self._on_language_selected)

        self.layout.addWidget(self.combo)
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)

        # Animations & Timers
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(200)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.fade_animation.finished.connect(self._on_animation_finished)

        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.start_fade_out)

        self._loading_timer = QTimer()
        self._loading_timer.setInterval(400)
        self._loading_timer.timeout.connect(self._animate_dots)

        self._current_mode = ""
        self._current_text = ""
        self._current_pos = None
        self._fading_out = False
        self._is_loading = False

    def _on_animation_finished(self):
        if self._fading_out:
            self._fading_out = False
            self.hide()

    def show_selection_ui(self, mode, languages, text, pos):
        """Phase 1: Show the Dropdown"""
        self._current_mode = mode
        self._current_text = text
        self._current_pos = pos

        self.label.hide()
        self.combo.clear()

        # Add a placeholder as the first item so they have to physically select something
        self.combo.addItem(f"Select {mode.capitalize()} Language...")
        self.combo.addItems(languages)
        self.combo.show()

        self.adjustSize()
        self.move(pos.x() + 20, pos.y() + 20)
        self.show()

        # Fade in
        self.fade_animation.stop()
        self._fading_out = False
        self.fade_animation.setStartValue(self.windowOpacity())
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()

    def _on_language_selected(self, index):
        """Phase 2: User made a choice, hide combo, tell Engine"""
        if index == 0:
            return  # Ignored the placeholder

        selected_lang = self.combo.currentText()
        self.combo.hide()  # Hide the dropdown instantly

        # Emit signal to start the AI inference
        self.comm.language_selected_signal.emit(
            self._current_mode, selected_lang, self._current_text, self._current_pos
        )

    def show_loading(self, pos, mode):
        """Phase 3: Show the Thinking text"""
        self._is_loading = True
        self._dot_count = 0
        self.label.setText(f"A9I {mode.capitalize()}ing...")
        self.label.setStyleSheet(
            "QLabel { background-color: rgba(20,20,20,240); color: #888; border: 1px solid #2a2a2a; border-radius: 12px; padding: 15px; }"
        )
        self.label.show()
        self.adjustSize()
        self._loading_timer.start()

    def _animate_dots(self):
        if not self._is_loading:
            return
        self._dot_count = (self._dot_count + 1) % 4
        self.label.setText(
            f"A9I {self._current_mode.capitalize()}ing{'.' * self._dot_count}"
        )

    def show_translation(self, text, pos):
        """Phase 4: Show the Result"""
        self._loading_timer.stop()
        self._is_loading = False

        self.label.setStyleSheet(
            "QLabel { background-color: rgba(20,20,20,240); color: #00FF99; border: 1px solid #333; border-radius: 12px; padding: 15px; }"
        )
        self.label.setText(text)
        self.adjustSize()

        self.hide_timer.start(7000)

    def start_fade_out(self):
        self.fade_animation.stop()
        self._fading_out = True
        self.fade_animation.setStartValue(self.windowOpacity())
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.start()
