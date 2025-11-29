import os
import discord
from datetime import time, datetime
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv
from events import calendar, EVENT_TYPE_DISPLAY, EVENT_TYPE_EMOJI, PING_EVENT_TYPES, format_date
from settings import settings

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)


#------------ Helper Functions---------

def format_events_embed(events: list[dict], title: str, emoji: str, color: discord.Color) -> discord.Embed:
    """Format a list of events into a Discord embed."""
    embed = discord.Embed(title=f"{emoji} {title}", color=color)
    
    if not events:
        embed.description = "No upcoming events found."
    else:
        for event in events:
            formatted_date = format_date(event["date"])
            embed.add_field(
                name=formatted_date,
                value=event["event_title"],
                inline=False
            )
    
    return embed


def get_event_color(event_type: str) -> discord.Color:
    """Get the color for a specific event type."""
    return discord.Color.red()


# ------------ scheduled stuff------

@tasks.loop(time=time(hour=17, minute=0))  # 5:00 PM daily
async def daily_notification():
    """Send individual notifications at 5pm for tomorrow's events."""
    channel_id = settings.notification_channel_id
    if not channel_id:
        print("Notification channel not set, skipping daily notification.")
        return
    
    channel = bot.get_channel(channel_id)
    if not channel:
        print(f"Could not find channel {channel_id}")
        return
    
    tomorrow_events = calendar.get_tomorrow_events()
    
    # Send message for each event
    for event in tomorrow_events:
        event_type = event["event_type"]
        emoji = EVENT_TYPE_EMOJI.get(event_type, "📌")
        display_name = EVENT_TYPE_DISPLAY.get(event_type, event_type)
        color = get_event_color(event_type)
        
        embed = discord.Embed(
            title=f"{emoji} {display_name} Tomorrow!",
            description=event["event_title"],
            color=color
        )
        embed.add_field(name="Date", value=format_date(event["date"]), inline=False)
        
        should_ping = settings.ping_everyone and event_type in PING_EVENT_TYPES
        
        if should_ping:
            await channel.send(content="@everyone", embed=embed)
        else:
            await channel.send(embed=embed)


@tasks.loop(hours=24)
async def daily_calendar_sync():
    """Sync calendar data once per day."""
    await calendar.fetch_and_parse()
    print("Daily calendar sync complete.")


# -------- Events ------

@bot.event
async def on_ready():
    print(f'{bot.user} is online!')
    
    # Initial calendar sync
    await calendar.fetch_and_parse()
    
    # Start scheduled tasks
    if not daily_notification.is_running():
        daily_notification.start()
    if not daily_calendar_sync.is_running():
        daily_calendar_sync.start()
    
    # Sync slash commands with Discord
    await bot.tree.sync()
    print('Slash commands synced!')


# ---- Commands ------

@bot.tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 Pong! {round(bot.latency * 1000)}ms")


# ------- Countdown Commands -----

# dates
MIDYEARS_DATE = datetime(2025, 12, 15, 8, 30)
WINTER_BREAK_DATE = datetime(2025, 12, 18, 14, 0)
END_OF_SCHOOL_DATE = datetime(2026, 5, 29, 11, 0)


def format_countdown(target: datetime) -> str:
    """Format the time remaining until a target date."""
    now = datetime.now()
    
    if now >= target:
        return "already happened! 🎉"
    
    delta = target - now
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes = remainder // 60
    
    if days > 0:
        return f"**{days}** days, **{hours}** hours, **{minutes}** minutes"
    elif hours > 0:
        return f"**{hours}** hours, **{minutes}** minutes"
    else:
        return f"**{minutes}** minutes"


@bot.tree.command(name="days-until-midyears", description="Countdown to midyear exams")
async def days_until_midyears(interaction: discord.Interaction):
    countdown = format_countdown(MIDYEARS_DATE)
    embed = discord.Embed(
        title="📚 Midyears Countdown",
        description=f"Time until midyears:\n{countdown}",
        color=discord.Color.red()
    )
    embed.add_field(name="Date", value="December 15, 2025 at 8:30 AM", inline=False)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="days-until-winter-break", description="Countdown to winter break")
async def days_until_winter_break(interaction: discord.Interaction):
    countdown = format_countdown(WINTER_BREAK_DATE)
    embed = discord.Embed(
        title="❄️ Winter Break Countdown",
        description=f"Time until winter break:\n{countdown}",
        color=discord.Color.blue()
    )
    embed.add_field(name="Date", value="December 18, 2025 at 2:00 PM", inline=False)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="days-until-end-of-school", description="Countdown to end of school")
async def days_until_end_of_school(interaction: discord.Interaction):
    countdown = format_countdown(END_OF_SCHOOL_DATE)
    embed = discord.Embed(
        title="🎓 End of School Countdown",
        description=f"Time until end of school:\n{countdown}",
        color=discord.Color.green()
    )
    embed.add_field(name="Date", value="May 29, 2026 at 11:00 AM", inline=False)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="refresh-eventdata", description="Manually refresh calendar event data")
@app_commands.default_permissions(administrator=True)
async def refresh_eventdata(interaction: discord.Interaction):
    await interaction.response.defer()
    count = await calendar.fetch_and_parse()
    await interaction.followup.send(f"✅ Refreshed calendar data. Found **{count}** events.")


@bot.tree.command(name="upcoming-halls", description="Get the next 5 hall events")
async def upcoming_halls(interaction: discord.Interaction):
    events = calendar.get_upcoming_by_type("hall", limit=5)
    embed = format_events_embed(
        events,
        "Upcoming Halls",
        EVENT_TYPE_EMOJI["hall"],
        discord.Color.purple()
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="upcoming-late-starts", description="Get the next 5 late start days")
async def upcoming_late_starts(interaction: discord.Interaction):
    events = calendar.get_upcoming_by_type("late_start", limit=5)
    embed = format_events_embed(
        events,
        "Upcoming Late Starts",
        EVENT_TYPE_EMOJI["late_start"],
        discord.Color.orange()
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="upcoming-dress-days", description="Get the next 5 dress days")
async def upcoming_dress_days(interaction: discord.Interaction):
    events = calendar.get_upcoming_by_type("dress_day", limit=5)
    embed = format_events_embed(
        events,
        "Upcoming Dress Days",
        EVENT_TYPE_EMOJI["dress_day"],
        discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="upcoming-extended-homerooms", description="Get the next 5 extended homeroom days")
async def upcoming_extended_homerooms(interaction: discord.Interaction):
    events = calendar.get_upcoming_by_type("extended_homeroom", limit=5)
    embed = format_events_embed(
        events,
        "Upcoming Extended Homerooms",
        EVENT_TYPE_EMOJI["extended_homeroom"],
        discord.Color.teal()
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="say", description="Make foxbot say something")
@app_commands.describe(message="What should it say?")
async def say(interaction: discord.Interaction, message: str):
    await interaction.response.send_message(message)


# ---------- settings commands ------

@bot.tree.command(name="set-notification-channel", description="Set this channel for school event reminders")
@app_commands.default_permissions(administrator=True)
async def set_notification_channel(interaction: discord.Interaction):
    settings.notification_channel_id = interaction.channel_id
    await interaction.response.send_message(
        f"✅ This channel ({interaction.channel.mention}) will now receive school event reminders at 5pm!",
        ephemeral=True
    )


@bot.tree.command(name="set-calendar-url", description="Set the iCal calendar URL")
@app_commands.describe(url="The iCal URL to fetch events from")
@app_commands.default_permissions(administrator=True)
async def set_calendar_url(interaction: discord.Interaction, url: str):
    settings.ical_url = url
    await interaction.response.defer(ephemeral=True)
    
    # Refresh calendar with new URL
    count = await calendar.fetch_and_parse()
    
    await interaction.followup.send(
        f"✅ Calendar URL updated! Found **{count}** events.",
        ephemeral=True
    )


@bot.tree.command(name="show-settings", description="Show current bot settings")
@app_commands.default_permissions(administrator=True)
async def show_settings(interaction: discord.Interaction):
    channel_id = settings.notification_channel_id
    ical_url = settings.ical_url
    ping_everyone = settings.ping_everyone
    
    embed = discord.Embed(title="⚙️ FoxBot Settings", color=discord.Color.blurple())
    
    # Notification channel
    if channel_id:
        channel = bot.get_channel(channel_id)
        channel_text = channel.mention if channel else f"ID: {channel_id} (not found)"
    else:
        channel_text = "Not set"
    embed.add_field(name="Notification Channel", value=channel_text, inline=False)
    
    # iCal URL
    if ical_url:
        # Truncate URL if too long
        url_display = ical_url if len(ical_url) < 50 else ical_url[:47] + "..."
    else:
        url_display = "Not set"
    embed.add_field(name="Calendar URL", value=url_display, inline=False)
    
    # Ping everyone setting
    ping_status = "✅ Enabled" if ping_everyone else "❌ Disabled"
    embed.add_field(name="Ping @everyone", value=ping_status, inline=False)
    
    # Event count
    event_count = len(calendar.get_all_events())
    embed.add_field(name="Cached Events", value=str(event_count), inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="toggle-ping-everyone", description="Toggle @everyone pings for important events")
@app_commands.default_permissions(administrator=True)
async def toggle_ping_everyone(interaction: discord.Interaction):
    current = settings.ping_everyone
    settings.ping_everyone = not current
    
    if settings.ping_everyone:
        await interaction.response.send_message(
            " @everyone pings **enabled** for dress days, late starts, and extended homerooms.",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            " @everyone pings **disabled**. All notifications will be sent without pinging.",
            ephemeral=True
        )


bot.run(TOKEN)

