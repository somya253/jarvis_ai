# utils.py

import os
import json
from pathlib import Path
from dotenv import load_dotenv

SETTINGS_FILE = Path("settings.json")

def load_env():
    """Load environment variables from .env file."""
    load_dotenv()

def load_settings():
    """Load appearance and font settings from a JSON file, or create defaults."""
    default_settings = {"appearance_mode": "dark", "color_theme": "blue", "font_size": 16}
    try:
        if not SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, "w") as f:
                json.dump(default_settings, f, indent=4)
            return default_settings
        
        with open(SETTINGS_FILE, "r") as f:
            settings = json.load(f)
        
        # Ensure all keys exist
        for key in default_settings:
            if key not in settings:
                settings[key] = default_settings[key]
                
        return settings
    except Exception as e:
        print(f"Error loading settings: {e}")
        return default_settings

def save_settings(settings):
    """Save settings dict to JSON file."""
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        print(f"Error saving settings: {e}")