"""
Settings Module
Manages bot configuration stored in a JSON file.
"""

import json
from pathlib import Path
from typing import Any, Optional

# Use data folder for persistence (mounted as Docker volume)
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
SETTINGS_FILE = DATA_DIR / "settings.json"

# Default settings
DEFAULT_SETTINGS = {
    "notification_channel_id": None,
    "ical_url": None,
    "ping_everyone": True,  # Ping @everyone for important events
}


class Settings:
    def __init__(self):
        self._settings: dict = {}
        self._load()

    def _load(self) -> None:
        """Load settings from JSON file."""
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r") as f:
                    self._settings = json.load(f)
                print(f"Loaded settings from {SETTINGS_FILE}")
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading settings: {e}")
                self._settings = DEFAULT_SETTINGS.copy()
        else:
            self._settings = DEFAULT_SETTINGS.copy()
            self._save()

    def _save(self) -> None:
        """Save settings to JSON file."""
        try:
            with open(SETTINGS_FILE, "w") as f:
                json.dump(self._settings, f, indent=2)
            print(f"Saved settings to {SETTINGS_FILE}")
        except IOError as e:
            print(f"Error saving settings: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a setting value and save."""
        self._settings[key] = value
        self._save()

    @property
    def notification_channel_id(self) -> Optional[int]:
        """Get the notification channel ID."""
        value = self._settings.get("notification_channel_id")
        return int(value) if value else None

    @notification_channel_id.setter
    def notification_channel_id(self, value: int) -> None:
        """Set the notification channel ID."""
        self.set("notification_channel_id", value)

    @property
    def ical_url(self) -> Optional[str]:
        """Get the iCal URL."""
        return self._settings.get("ical_url")

    @ical_url.setter
    def ical_url(self, value: str) -> None:
        """Set the iCal URL."""
        self.set("ical_url", value)

    @property
    def ping_everyone(self) -> bool:
        """Get whether to ping @everyone for important events."""
        return self._settings.get("ping_everyone", True)

    @ping_everyone.setter
    def ping_everyone(self, value: bool) -> None:
        """Set whether to ping @everyone for important events."""
        self.set("ping_everyone", value)


# Global instance
settings = Settings()
