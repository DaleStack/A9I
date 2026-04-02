import sys
import threading
from PyQt6.QtWidgets import QApplication
from pynput import keyboard

from config import TRANSLATE_HOTKEY, DEFINE_HOTKEY
from ui import A9IFrame, Communicate
from engine import a9i_text_grabber, a9i_ai_executor


def main():
    app = QApplication(sys.argv)

    comm = Communicate()
    ghost_frame = A9IFrame(comm)

    # 1. UI receives signal to show the dropdown
    comm.request_selection_signal.connect(ghost_frame.show_selection_ui)

    # 2. UI emits signal back when user makes a choice -> Spawns AI thread
    def on_language_selected(mode, target_language, text, pos):
        threading.Thread(
            target=a9i_ai_executor,
            args=(comm, mode, target_language, text, pos),
            daemon=True,
        ).start()

    comm.language_selected_signal.connect(on_language_selected)

    # 3. Standard UI updates
    comm.loading_signal.connect(ghost_frame.show_loading)
    comm.display_signal.connect(ghost_frame.show_translation)

    # --- Hotkey Triggers ---
    def trigger_translate():
        threading.Thread(
            target=a9i_text_grabber, args=(comm, "translate"), daemon=True
        ).start()

    def trigger_define():
        threading.Thread(
            target=a9i_text_grabber, args=(comm, "define"), daemon=True
        ).start()

    listener = keyboard.GlobalHotKeys(
        {TRANSLATE_HOTKEY: trigger_translate, DEFINE_HOTKEY: trigger_define}
    )
    listener.start()

    print("🚀 A9I Configurable UI Active")
    print(f"   [T] Translate: {TRANSLATE_HOTKEY}")
    print(f"   [D] Define:    {DEFINE_HOTKEY}")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
