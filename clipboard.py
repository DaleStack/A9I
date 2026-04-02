import time
import pyperclip
import pyautogui


def get_selected_text():
    """Simulates Ctrl+C and grabs the highlighted text."""
    old_clipboard = pyperclip.paste()
    pyperclip.copy("")

    time.sleep(0.3)
    pyautogui.keyDown("ctrl")
    pyautogui.press("c")
    pyautogui.keyUp("ctrl")

    for _ in range(7):
        time.sleep(0.1)
        text = pyperclip.paste().strip()
        if text:
            return text, old_clipboard

    return "", old_clipboard
