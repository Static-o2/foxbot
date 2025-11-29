"""
Events Module
Fetches and parses iCal data for specific event types.
"""

import os
import json
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional
import aiohttp
from icalendar import Calendar

# Use data folder for persistence (mounted as Docker volume)
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
EVENTS_FILE = DATA_DIR / "events.json"

# Event types and their keywords case-insensitive
EVENT_TYPES = {
    "dress_day": "dress day",
    "hall": "hall:",
    "late_start": "late start",
    "extended_homeroom": "extended homeroom",
}

# Display names
EVENT_TYPE_DISPLAY = {
    "dress_day": "Dress Day",
    "hall": "Hall",
    "late_start": "Late Start",
    "extended_homeroom": "Extended Homeroom",
}

# Emojis
EVENT_TYPE_EMOJI = {
    "dress_day": "🤵‍♂️",
    "hall": "🏛️",
    "late_start": "⏰",
    "extended_homeroom": "🏠",
}

# Event types that ping @everyone
PING_EVENT_TYPES = {"dress_day", "late_start", "extended_homeroom"}


def format_date(date_str: str) -> str:
    """Format a date string (YYYY-MM-DD) to a friendly format like 'Monday, December 1st'."""
    d = date.fromisoformat(date_str)
    
    # Get day suffix (1st, 2nd, 3rd,)
    day = d.day
    if 11 <= day <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    
    # "Monday, December 1st"
    return d.strftime(f"%A, %B {day}{suffix}")


class CalendarEvents:
    def __init__(self):
        self.events: list[dict] = []
        self._load_from_file()

    def _load_from_file(self) -> None:
        """Load events from JSON file if it exists."""
        if EVENTS_FILE.exists():
            try:
                with open(EVENTS_FILE, "r") as f:
                    self.events = json.load(f)
                print(f"Loaded {len(self.events)} events from cache.")
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading events file: {e}")
                self.events = []

    def _save_to_file(self) -> None:
        """Save events to JSON file."""
        try:
            with open(EVENTS_FILE, "w") as f:
                json.dump(self.events, f, indent=2)
            print(f"Saved {len(self.events)} events to cache.")
        except IOError as e:
            print(f"Error saving events file: {e}")

    def _get_event_type(self, event_name: str) -> Optional[str]:
        """Check if event name matches any keyword and return the event type."""
        event_name_lower = event_name.lower()
        for event_type, keyword in EVENT_TYPES.items():
            if keyword in event_name_lower:
                return event_type
        return None

    async def fetch_and_parse(self, ical_url: Optional[str] = None) -> int:
        """
        Fetch iCal data from URL and parse for matching events.
        Returns the number of events found.
        """
        # Import here to avoid circular import
        from settings import settings
        
        # Priority: passed URL > settings > env variable
        url = ical_url or settings.ical_url or os.getenv("ICAL_URL")
        
        if not url:
            print("Error: No iCal URL provided. Use /set-calendar-url to set one.")
            return 0

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        print(f"Error fetching calendar: HTTP {response.status}")
                        return 0
                    ical_data = await response.text()
        except aiohttp.ClientError as e:
            print(f"Error fetching calendar: {e}")
            return 0

        # Parse the iCal data
        try:
            cal = Calendar.from_ical(ical_data)
        except Exception as e:
            print(f"Error parsing iCal data: {e}")
            return 0

        # Clear existing events + parse new ones
        self.events = []

        for component in cal.walk():
            if component.name == "VEVENT":
                event_name = str(component.get("summary", ""))
                event_type = self._get_event_type(event_name)

                if event_type:
                    # Get the event date
                    dtstart = component.get("dtstart")
                    if dtstart:
                        event_date = dtstart.dt
                        # Handle both date and datetime objects
                        if isinstance(event_date, datetime):
                            event_date = event_date.date()
                        
                        self.events.append({
                            "event_type": event_type,
                            "date": event_date.isoformat(),
                            "event_title": event_name,
                        })

        # Sort by date
        self.events.sort(key=lambda x: x["date"])
        
        # Save to file
        self._save_to_file()
        
        print(f"Found {len(self.events)} matching events.")
        return len(self.events)

    def get_upcoming_by_type(self, event_type: str, limit: int = 5) -> list[dict]:
        """Get upcoming events of a specific type (from today onwards)."""
        today = date.today()
        upcoming = [
            e for e in self.events
            if e["event_type"] == event_type and date.fromisoformat(e["date"]) >= today
        ]
        return upcoming[:limit]

    def get_events_for_date(self, target_date: date) -> list[dict]:
        """Get all events for a specific date."""
        date_str = target_date.isoformat()
        return [e for e in self.events if e["date"] == date_str]

    def get_tomorrow_events(self) -> list[dict]:
        """Get all events for tomorrow (used for 5pm notifications)."""
        tomorrow = date.today() + timedelta(days=1)
        return self.get_events_for_date(tomorrow)

    def get_all_events(self) -> list[dict]:
        """Get all stored events."""
        return self.events


# Global instance for use across the bot
calendar = CalendarEvents()

