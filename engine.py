import pyperclip
import ollama
from PyQt6.QtGui import QCursor

from config import TRANSLATE_MODEL, DEFINE_MODEL, TRANSLATE_LANGS, DEFINE_LANGS
from clipboard import get_selected_text

is_running = False


def a9i_text_grabber(comm, mode):
    """Step 1: Grab text and ask UI to show the dropdown."""
    global is_running
    if is_running:
        return
    is_running = True

    try:
        text, old_clipboard = get_selected_text()
        if not text:
            is_running = False
            return

        # Restore clipboard immediately since we have the text stored in memory
        pyperclip.copy(old_clipboard)

        mouse_pos = QCursor.pos()
        langs = TRANSLATE_LANGS if mode == "translate" else DEFINE_LANGS

        # Tell UI to show the language dropdown
        comm.request_selection_signal.emit(mode, langs, text, mouse_pos)

    except Exception as e:
        print(f"Grab Error: {e}")
        is_running = False


def a9i_ai_executor(comm, mode, target_language, text, mouse_pos):
    """Step 2: Take the text and selected language, run AI."""
    global is_running
    try:
        # Tell UI to switch from Dropdown to "Thinking..."
        comm.loading_signal.emit(mouse_pos, mode)

        target_model = TRANSLATE_MODEL if mode == "translate" else DEFINE_MODEL

        # Dynamically inject the YAML language into the prompt
        if mode == "translate":
            prompt = f"Translate the following text into strictly {target_language}. Return ONLY the translation, no explanations:\n\n{text}"
        else:
            prompt = f"Provide a concise dictionary definition for the following text. Format the definition appropriately for a {target_language} context. Return ONLY the definition:\n\n{text}"

        response = ollama.generate(
            model=target_model, prompt=prompt, options={"temperature": 0.1}
        )
        result = response["response"].strip()

        comm.display_signal.emit(result, mouse_pos)

    except Exception as e:
        print(f"AI Error: {e}")
        comm.dismiss_signal.emit()
    finally:
        is_running = False
