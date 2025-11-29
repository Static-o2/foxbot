# FoxBot 🦊

A simple Discord bot built in python for the RL Foxes discord server.

## Setup

### Run with Docker

```bash
# Build and run with Docker Compose
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop the bot
docker-compose down
```

### Or Run Locally (without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot
python main.py
```

## Commands

### General Commands
| Command | Description |
|---------|-------------|
| `/ping` | Check bot latency |
| `/say <message>` | Make FoxBot say something |

### Event Commands
| Command | Description |
|---------|-------------|
| `/upcoming-halls` | Get the next 5 halls |
| `/upcoming-late-starts` | Get the next 5 late start days |
| `/upcoming-dress-days` | Get the next 5 dress days |
| `/upcoming-extended-homerooms` | Get the next 5 extended homeroom days |

### Countdown Commands
| Command | Description |
|---------|-------------|
| `/days-until-midyears` | Countdown to midyear exams |
| `/days-until-winter-break` | Countdown to winter break |
| `/days-until-end-of-school` | Countdown to end of school |

### Admin Commands
| Command | Description |
|---------|-------------|
| `/set-notification-channel` | Set the current channel for event reminders |
| `/set-calendar-url <url>` | Set the iCal calendar URL |
| `/show-settings` | View current bot settings |
| `/toggle-ping-everyone` | Toggle @everyone pings for important events |
| `/refresh-eventdata` | Manually refresh calendar data |

## Automatic Features

- **Daily Event Notifications**: At 5:00 PM, the bot sends a reminder if there are any important events tomorrow
  - Dress days, late starts, and extended homerooms ping `@everyone` (if enabled)
  - Halls don't ping but are still sent
- **Daily Calendar Sync**: Calendar data is automatically refreshed every 24 hours

## Dependencies

- discord.py
- python-dotenv
- icalendar
