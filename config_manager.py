import json
import os

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "geometry": {
        "x": 100,
        "y": 100,
        "width": 300,
        "height": 400
    },
    "background": "transparent",
    "font": {
        "family": "Arial",
        "size": 14,
        "bold": True,
        "italic": False,
        "color": "#ffffff"
    }
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            # Merge with default to ensure keys exist
            merged = DEFAULT_CONFIG.copy()
            merged.update(config)
            return merged
    except Exception as e:
        print(f"Error loading config: {e}")
        return DEFAULT_CONFIG.copy()

def save_config(config):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Error saving config: {e}")
