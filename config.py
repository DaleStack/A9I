import yaml

# Model & Hotkey Config
TRANSLATE_MODEL = "a9i-translate:latest"
DEFINE_MODEL = "a9i-define:latest"

TRANSLATE_HOTKEY = "<ctrl>+<alt>+t"
DEFINE_HOTKEY = "<ctrl>+<alt>+d"


# Load YAML Config
def load_languages():
    try:
        with open("config.yaml", "r") as file:
            config = yaml.safe_load(file)
            return config.get("translate_languages", []), config.get(
                "define_languages", []
            )
    except FileNotFoundError:
        print("⚠️ config.yaml not found. Using defaults.")
        return ["Spanish"], ["English"]


TRANSLATE_LANGS, DEFINE_LANGS = load_languages()
