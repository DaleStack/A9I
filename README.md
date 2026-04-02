# A9I (Artificial Highlight Intelligence) 🧠✨

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green)
![Ollama](https://img.shields.io/badge/AI-Ollama-black)
![License](https://img.shields.io/badge/License-MIT-orange)

A9I is a system-wide, "invisible" AI tool that provides instant text translations and dictionary definitions without ever breaking your workflow. Built with Python, PyQt6, and local Ollama LLMs, it floats a sleek, auto-dismissing UI right next to your cursor whenever you trigger a hotkey.

No opening new tabs. No context-switching. 100% local and private.

## ✨ Features
* **Global Hotkeys:** Works across your entire OS—whether you are in a browser, VS Code, a PDF reader, or Roblox Studio.
* **Invisible UI:** A PyQt6 "Ghost Frame" that fades in exactly where your eyes are looking, without stealing window focus.
* **Dual-Core LLM Routing:** Maps different hotkeys to highly specialized local models (e.g., `a9i-translate` vs `a9i-define`) for blazing-fast, accurate results.
* **Dynamic Language Selection:** Intercepts translations with a fast, auto-opening dropdown menu powered by a customizable `config.yaml` file.
* **100% Local:** Powered by [Ollama](https://ollama.com/), meaning zero latency from cloud APIs and total data privacy.

---

## 🛠️ Prerequisites

Before you begin, ensure you have the following installed:
1. **Python 3.10+**
2. **[uv](https://docs.astral.sh/uv/)** (Python package manager)
3. **[Ollama](https://ollama.com/)** running locally.

### Custom AI Models
This project relies on two specialized Ollama models. You will need to build them using your own `Modelfile` setups, or rename the variables in `config.py` to match your existing local models:
* `a9i-translate:latest`
* `a9i-define:latest`

---

## 🚀 Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/yourusername/a9i-project.git](https://github.com/yourusername/a9i-project.git)
   cd a9i-project
   ```

2. **Install dependencies using `uv`:**
   ```bash
   uv sync
   ```

3. **Configure your languages:**
   Create or edit the `config.yaml` file in the root directory to define your target languages.
   ```yaml
   # config.yaml
   translate_languages:
     - Spanish
     - Japanese
     - French
     - Tagalog

   define_languages:
     - English
     - Simple English (ELI5)
     - Developer Terms
   ```

---

## 💻 Usage

Start the A9I background daemon:
```bash
uv run main.py
```

Once active, simply highlight any text anywhere on your computer and press:
* **`Ctrl + Alt + T`** 👉 **Translate Mode** (Spawns the language selection UI, then translates).
* **`Ctrl + Alt + D`** 👉 **Define Mode** (Spawns the context selection UI, then defines).

Click anywhere outside the bubble to instantly dismiss it, or wait 7 seconds for the smooth auto-fade.

---

## 📂 Project Structure

A9I is built with a modular, separation-of-concerns architecture:

* `main.py` - The orchestrator that wires signals and keyboard listeners together.
* `ui.py` - The presentation layer (PyQt6 ghost frame, animations, and dropdown logic).
* `engine.py` - The AI logic that communicates with the local Ollama instance.
* `clipboard.py` - Handles OS-level virtual keypresses to grab highlighted text safely.
* `config.py` - Loads models, hotkeys, and parses the `config.yaml` file.

---

## ⚠️ Notes for Windows Users
You may see a terminal warning regarding `SetProcessDpiAwarenessContext() failed`. This is a harmless warning caused by PyQt6 inheriting DPI settings from the terminal. It does not affect A9I's functionality and can be safely ignored.

## 🤝 Contributing
Feel free to open issues or submit pull requests if you have ideas for new features, like adding text-to-speech (TTS) or conversation history logging!