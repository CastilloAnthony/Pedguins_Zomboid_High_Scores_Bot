# This file developed by Peter Mann (Pedguin) and includes modifications made by Anthony Castillo (ComradeWolf).
import discord
from discord.ext import commands, tasks
from discord import app_commands 
from mcrcon import MCRcon
import paramiko
import time
import json
import atexit
import os
import re

import logging
LOGGER: logging.Logger = logging.getLogger("bot")
discord.utils.setup_logging(level=logging.INFO) # Enables additional logging info from discord, just nice to see sometimes and not to overwhelming, ALSO DUPLICATES DISCORD LOGGING MSGS :(
logging.getLogger('paramiko').setLevel(logging.WARNING) # Surpresses logging info messages about connecting and closing SFTP
from read_discord_settings import read_discord_settings
from read_connection_settings import read_connection_settings
settings_discord = read_discord_settings()
settings_connection = read_connection_settings()
target_bot = 'Pedguins_Zomboid_High_Scores_Bot'
# Examples of Accessing Data:
# settings_discord['target_bot']['botToken']            # target_bot is a sub-dictionary inside of settings_discord, technically, we could have multiple bots listed in the json.
# settings_connection['RCON_HOST']
polling_rate = 10/60*60 # Seconds (Note: 1/60 * 60 is 1 second)

# --------------------
# DISCORD INTENTS
# --------------------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree  # command tree for slash commands

# --------------------
# DATA
# --------------------
online_players = set()
player_sessions = {}        # tracks last timestamp for session increments
total_times = {}            # cumulative playtime, never resets
player_survival_time = {}   # current survival time, resets on death
player_skills = {}          # {player: {skill: level}}
seen_levelups = set()
seen_deaths = set()
server_online = False
curr_activity = "🔴 Server Offline" # Keeps track of the last status update, we don't need to send an update out if the bot already has the same activity set.

SAVE_FILE = "player_times.json"
SEEN_SKILLS_FILE = "seen_skills.json"

# --------------------
# SKILL EMOJIS & ALIASES
# --------------------
SKILL_EMOJIS = {
    "Husbandry": "🐴",
    "Fitness": "🤸🏻‍♀️",
    "Carving": "🪵",
    "Farming": "🌾",
    "Aiming": "🎯",
    "Art": "🎨",
    "Axe": "🪓",
    "Blacksmith": "⚒️",
    "Butchering": "🔪",
    "Woodwork": "🪚",
    "Cleaning": "🧹",
    "Cooking": "🍳",
    "Dancing": "💃",
    "Electricity": "💡",
    "Doctor": "💊",
    "Fishing": "🎣",
    "PlantScavenging": "🍄",
    "Glassmaking": "🔍",
    "FlintKnapping": "🪨",
    "Lightfoot": "👣",
    "LongBlade": "⚔️️",
    "Blunt": "🏏",
    "Maintenance": "🔧",
    "Masonry": "🧱",
    "Mechanics": "🚗",
    "Meditation": "🧘",
    "Music": "🎵",
    "Nimble": "🩰",
    "Pottery": "🏺",
    "Reloading": "💥",
    "Sprinting": "👟",
    "SmallBlade": "🗡️",
    "SmallBlunt": "🔨",
    "Sneak": "🥷",
    "Spear": "🦯",
    "Strength": "💪",
    "Tailoring": "🪡",
    "Tracking": "🐾",
    "Trapping": "🪤",
    "MetalWelding": "🔩"
}

SKILL_ALIASES = {
    # Tailoring
    "tailor": "Tailoring",
    "tailoring": "Tailoring",

    # Electrical
    "electric": "Electricity",
    "electrical": "Electricity",

    # Welding
    "weld": "MetalWelding",
    "welding": "MetalWelding",

    # Long Blade
    "longblade": "LongBlade",
    "long blade": "LongBlade",

    # Long Blunt
    "longblunt": "Blunt",
    "long blunt": "Blunt",

    # Small Blade
    "smallblade": "SmallBlade",
    "small blade": "SmallBlade",

    # Small Blunt
    "smallblunt": "SmallBlunt",
    "small blunt": "SmallBlunt",

    # Foraging
    "forage": "PlantScavenging",
    "foraging": "PlantScavenging",
    "plantscavenging": "PlantScavenging",

    # First Aid
    "firstaid": "Doctor",
    "first aid": "Doctor",
    "doctor": "Doctor",

    # Knapping
    "knapping": "FlintKnapping",
    "flintknapping": "FlintKnapping",

    # Axe
    "axe": "Axe",

    # Woodworking / Carpentry
    "wood": "Woodwork",
    "woodworking": "Woodwork",
    "carpentry": "Woodwork",
    "woodwork": "Woodwork",

    # Husbandry / Animal Care
    "husbandry": "Husbandry",
    "animalcare": "Husbandry",
    "animal care": "Husbandry",
}

SKILL_DISPLAY = {
    "Tailoring": "Tailoring",
    "Electricity": "Electrical",
    "MetalWelding": "Welding",
    "LongBlade": "Long Blade",
    "Blunt": "Long Blunt",
    "SmallBlade": "Small Blade",
    "SmallBlunt": "Small Blunt",
    "PlantScavenging": "Foraging",
    "Doctor": "First Aid",
    "FlintKnapping": "Knapping",
    "Axe": "Axe",
    "Woodwork": "Carpentry",
    "Husbandry": "Animal Care",
}

# Full default skill levels for all skills in Project Zomboid
# --------------------
DEFAULT_SKILLS = {
    "Fitness": 0,
    "Strength": 0,
    "Cooking": 0,
    "Blunt": 0,
    "Axe": 0,
    "Lightfoot": 0,
    "Nimble": 0,
    "Sprinting": 0,
    "Sneak": 0,
    "Woodwork": 0,
    "Aiming": 0,
    "Reloading": 0,
    "Farming": 0,
    "Fishing": 0,
    "Trapping": 0,
    "PlantScavenging": 0,
    "Doctor": 0,
    "Electricity": 0,
    "Blacksmith": 0,
    "MetalWelding": 0,
    "Mechanics": 0,
    "Spear": 0,
    "Maintenance": 0,
    "SmallBlade": 0,
    "LongBlade": 0,
    "SmallBlunt": 0,
    "Tailoring": 0,
    "Tracking": 0,
    "Husbandry": 0,
    "FlintKnapping": 0,
    "Masonry": 0,
    "Pottery": 0,
    "Carving": 0,
    "Butchering": 0,
    "Glassmaking": 0,
    "Art": 0,
    "Cleaning": 0,
    "Dancing": 0,
    "Meditation": 0,
    "Music": 0,
}


# --------------------
# LOAD / SAVE FUNCTIONS
# --------------------
def load_times():
    global total_times
    try:
        with open(SAVE_FILE, "r") as f:
            total_times.update({k.lower(): float(v) for k, v in json.load(f).items()})
        LOGGER.info("Player total times loaded.")
    except FileNotFoundError:
        total_times.clear()
        LOGGER.info("No previous total times found.")


def save_times():
    global total_times
    with open(SAVE_FILE, "w") as f:
        json.dump(total_times, f, indent=4)
    # LOGGER.info("Player total times saved.") # Not necessary and clogs up the terminal with double print alongside save_seen_skills


def load_seen_skills():
    global player_skills
    try:
        with open(SEEN_SKILLS_FILE, "r") as f:
            player_skills.update(json.load(f))
        LOGGER.info("Seen skills loaded.")
    except FileNotFoundError:
        player_skills.clear()
        LOGGER.info("No previous skill data found.")


def sanitize_player_skills():
    """Force all player keys to lowercase and ensure full DEFAULT_SKILLS"""
    global player_skills
    fixed = {}
    for key, skills in player_skills.items():
        full = DEFAULT_SKILLS.copy()
        if isinstance(skills, dict):
            full.update(skills)
        fixed[key.lower()] = full

    player_skills.clear()
    player_skills.update(fixed)
    LOGGER.info("Player skills sanitized (lowercase keys, defaults filled).")


def save_seen_skills():
    global player_skills
    with open(SEEN_SKILLS_FILE, "w") as f:
        json.dump(player_skills, f, indent=4)
    # LOGGER.info("Seen skills saved.") # Not necessary and clogs up the terminal with double print alongside save_times


# ---- initial load on startup ----
load_times()
load_seen_skills()
sanitize_player_skills()

atexit.register(save_times)
atexit.register(save_seen_skills)

# --------------------
# SERVER STATUS ANNOUNCE
# --------------------
async def announce_server_status(online: bool = server_online):
    channel = bot.get_channel(settings_discord[target_bot]['ANNOUNCE_CHANNEL_ID'])
    if not channel:
        return
    msg = "🟢 - Project Zomboid server is now ONLINE" if online else "🔴 - Project Zomboid server is OFFLINE"
    await channel.send(f"# {msg}")

# --------------------
# BOT READY
# --------------------
@bot.event
async def on_ready():
    LOGGER.info(f"{bot.user} has connected to Discord!")

    # Sync slash commands
    await tree.sync()
    # await bot.change_presence(status=discord.Status.dnd, activity=discord.Game(name=curr_activity))
    # Start loops that exist
    # poll_players.start()
    # update_status.start()
    periodic_save.start()

    LOGGER.info("Successfully finished startup")

    
# --------------------
# PLAYER POLLING + SURVIVAL + SKILL RESET ON DEATH + LEVEL-UPS
# --------------------
# pending_new_player = None

# @tasks.loop(seconds=polling_rate)
async def poll_players():
    global online_players, player_sessions, total_times, player_survival_time, player_skills, server_online
    now = time.time()
    channel = bot.get_channel(settings_discord[target_bot]['ANNOUNCE_CHANNEL_ID'])
    death_channel = bot.get_channel(settings_discord[target_bot]['ANNOUNCE_CHANNEL_ID'])

    try:
        # --- RCON: get online players ---
        with MCRcon(settings_connection['RCON_HOST'], settings_connection['RCON_PASSWORD'], port=settings_connection['RCON_PORT']) as rcon:
            response = rcon.command("players") or rcon.command("who")
        server_online = True
        current_players = set()

        # --- Parse RCON player list ---
        for line in response.splitlines():
            clean = line.strip().lstrip("-•* ").strip()
            lower = clean.lower()
            if not clean or "unknown command" in lower or lower.startswith(("players","connected","there are","total")):
                continue
            if not clean.replace("_","").isalnum():
                continue
            current_players.add(lower)

        # --- Handle joins ---
        for player in current_players - online_players:
            player_sessions[player] = now
            player_survival_time.setdefault(player, 0)
            player_skills.setdefault(player, DEFAULT_SKILLS.copy())
            if channel:
                await channel.send(f"```🟢 - {player.capitalize()} has joined the server!```")

        # --- Handle leaves ---
        for player in online_players - current_players:
            start = player_sessions.pop(player, now)
            session = now - start
            total_times[player] = total_times.get(player, 0) + session
            player_survival_time[player] = player_survival_time.get(player, 0) + session
            h, m = int(session//3600), int((session%3600)//60)
            if channel:
                await channel.send(f"```🔴 - {player.capitalize()} has left the server.\nSession: {h}h {m}m```")

        # --- Increment survival and total time for current online players ---
        for player in current_players & online_players:
            session = now - player_sessions.get(player, now)
            total_times[player] = total_times.get(player, 0) + session
            player_survival_time[player] = player_survival_time.get(player, 0) + session
            player_sessions[player] = now

        online_players.clear()
        online_players.update(current_players)

        # --- SFTP: Check PerkLog for deaths & level-ups ---
        transport = paramiko.Transport((settings_connection['SFTP_HOST'], settings_connection['SFTP_PORT']))
        transport.connect(username=settings_connection['SFTP_USER'], password=settings_connection['SFTP_PASS'])
        sftp = paramiko.SFTPClient.from_transport(transport)

        files = sftp.listdir(settings_connection['LOG_DIR'])
        perk_logs = [f for f in files if f.endswith("_PerkLog.txt")]

        if perk_logs:
            latest_file = sorted(perk_logs)[-1]
            remote_path = os.path.join(settings_connection['LOG_DIR'], latest_file)

            # --- Correctly indented file reading ---
            with sftp.open(remote_path, "r") as f:
                for line in f:
                    line = line.strip()

                    # --- Death detection ---
                    if "[Died]" in line and line not in seen_deaths:
                        seen_deaths.add(line)
                        try:
                            parts = re.findall(r"\[(.*?)\]", line)
                            player_name = parts[2]  # original name
                            player_key = parts[2].lower()
                            hours_survived = float(parts[-1].replace("Hours Survived: ","").replace(".",""))

                            # Reset skills and survival time
                            player_skills[player_key] = DEFAULT_SKILLS.copy()
                            player_survival_time[player_key] = 0
                            LOGGER.info(f"{player_name.capitalize()}'s skills and survival time reset due to death.")

                            # In-game time
                            in_game_days = int(hours_survived // 24)
                            in_game_hours = int(hours_survived % 24)
                            if hours_survived >= 1:
                                in_game_str = f"{in_game_days} days {in_game_hours} hours" if in_game_days > 0 else f"{in_game_hours} hours"
                            else:
                                in_game_str = "less than 1 hour"

                            # Real-life time
                            real_minutes = hours_survived * 3.75
                            real_days = int(real_minutes // (24*60))
                            real_hours = int((real_minutes % (24*60)) // 60)
                            real_mins = int(real_minutes % 60)
                            if real_minutes >= 1:
                                real_str = f"{real_days} days {real_hours} hours {real_mins} minutes" if real_days > 0 else f"{real_hours} hours {real_mins} minutes"
                            else:
                                real_str = "less than a minute"

                            # Capitalize for display
                            display_name = player_name.capitalize()

                            # Send multi-line death message
                            msg = f"""
                            ```💀 {display_name} has died.
                            Survived in-game: {in_game_str}
                            Real-life: {real_str}```
                            """
                            if death_channel:
                                await death_channel.send(msg)

                        except Exception as e:
                            LOGGER.info(f"Error parsing death line: {e}")

                        continue  # skip other processing for this line

                    # --- Level-up detection ---
                    if line in seen_levelups:
                        continue
                    if "[Created Player" in line:
                        seen_levelups.add(line)
                        continue
                    if "=" in line:
                        try:
                            bracketed = re.findall(r"\[(.*?)\]", line)
                            if len(bracketed) < 5:
                                continue
                            player_key = bracketed[2].lower()
                            display_name = bracketed[2]
                            skills_str = bracketed[4] if "=" in bracketed[4] else ""
                            if not skills_str:
                                continue
                            player_skills.setdefault(player_key, DEFAULT_SKILLS.copy())
                            for pair in skills_str.split(", "):
                                if "=" in pair:
                                    skill_name, lvl = pair.split("=")
                                    skill_name = skill_name.strip()
                                    lvl = int(''.join(filter(str.isdigit, lvl)) or 0)
                                    if skill_name in DEFAULT_SKILLS:
                                        player_skills[player_key][skill_name] = lvl
                            seen_levelups.add(line)
                        except Exception as e:
                            LOGGER.info(f"Error parsing skill line: {e}")

                    if "[Level Changed]" in line:
                        seen_levelups.add(line)
                        try:
                            parts = line.split("][")
                            player_key = parts[1].lower()
                            display_name = parts[1]
                            skill = parts[4]
                            level = int(parts[5].strip("]."))
                            emoji = SKILL_EMOJIS.get(skill, "")
                            player_skills.setdefault(player_key, DEFAULT_SKILLS.copy())[skill] = level
                            display_name_cap = display_name.capitalize()
                            msg = f"```🎉 {display_name_cap} has leveled up their {skill} to {level}! {emoji}```"

                            channel = bot.get_channel(settings_discord[target_bot]['LEVELUP_CHANNEL_ID'])
                            if channel:
                                await channel.send(msg)
                        except Exception:
                            LOGGER.info(f"Error parsing level-up line: {line}")

        sftp.close()
        transport.close()
        save_times()
        save_seen_skills()
        LOGGER.info(f'Players successfully polled and new data is available!') # Also not necessary, but I thought you might like to keep some info in the terminal as you had before.

    except Exception as e:
        if server_online:
            server_online = False
            online_players.clear()
            player_sessions.clear()
            # await announce_server_status(False)
        LOGGER.info(f"Polling error: {e}")


# --------------------
# DISCORD STATUS
# --------------------
# @tasks.loop(seconds=polling_rate)
# async def update_status():
async def update_status():
    global curr_activity, online_players, server_online
    try:
        if server_online:
            activity_name = ""
            if len(online_players)==0:
                activity_name = "🟢 Server Online"
            else:
                activity_name = f"🟢 {len(online_players)} Survivors Online"
            if 'Online' not in curr_activity:
                await announce_server_status(True)
            if curr_activity != activity_name:
                await bot.change_presence(status=discord.Status.online, activity=discord.Game(name=activity_name))
                curr_activity = activity_name
                LOGGER.info(f'Changed discord status to {activity_name}')
        else:
            activity_name = "🔴 Server Offline"
            if 'Offline' not in curr_activity:
                await bot.change_presence(status=discord.Status.dnd, activity=discord.Game(name=activity_name))
                curr_activity = activity_name
                LOGGER.info(f'Changed discord status to 🔴 Server Offline')
                await announce_server_status(False)
    except Exception:
        LOGGER.info(f'Variable server_online is in state {server_online} and curr_activity is set to {curr_activity}')

# --------------------
# SAVE LOOP
# --------------------
@tasks.loop(seconds=polling_rate)
async def periodic_save():
    await poll_players()
    await update_status()
    # We should save whenever we retrieve new data. These has been moved to the end of poll_players()
    # save_times()
    # save_seen_skills()
    

# --------------------
# COMMANDS (Slash)
# --------------------

@tree.command(name="online", description="Show currently online players")
async def online_slash(interaction: discord.Interaction):
    global online_players, player_sessions
    now = time.time()
    if not online_players:
        await interaction.response.send_message("```🟢 - No players are currently online.```")
        return
    lines = []
    for player in sorted(online_players):
        duration = now - player_sessions.get(player, now)
        h, m = int(duration//3600), int((duration%3600)//60)
        lines.append(f"- {player.capitalize()} ({h}h {m}m)")
    await interaction.response.send_message(f"```🟢 - Players Online:\n" + "\n".join(lines) + f"\n\nTotal: {len(online_players)}```")


@tree.command(name="time", description="Show total playtime for a player")
@app_commands.describe(target="Player name or 'all'")
async def time_slash(interaction: discord.Interaction, target: str):
    global online_players, player_sessions, total_times
    now = time.time()
    if target.lower() == "all":
        combined = {p:t for p,t in total_times.items()}
        for p in online_players:
            combined[p] = combined.get(p,0) + (now - player_sessions.get(p,now))
        top = sorted(combined.items(), key=lambda x:x[1], reverse=True)[:10]
        if not top:
            await interaction.response.send_message("```🕒 - No playtime recorded yet.```")
            return
        lines = []
        for p, sec in top:
            h, m = int(sec//3600), int((sec%3600)//60)
            status = "🟢" if p in online_players else "🔴"
            lines.append(f"{status} - {p.capitalize()}: {h}h {m}m")
        await interaction.response.send_message("```🕒 - Top 10 Players by Total Playtime:\n" + "\n".join(lines) + "```")
        return

    player = target.lower()
    total = total_times.get(player,0)
    if player in online_players:
        total += now - player_sessions.get(player,now)
    h, m = int(total//3600), int((total%3600)//60)
    status = "🟢" if player in online_players else "🔴"
    await interaction.response.send_message(f"```{status} - {player.capitalize()} has played {h}h {m}m total.```")


@tree.command(name="skill", description="Show a player's skills or leaderboard for a skill")
@app_commands.describe(target="Skill name, player name, or 'total'")
async def skill_slash(interaction: discord.Interaction, target: str):
    global online_players, player_skills
    target_lower = target.lower()

    # ----------------------
    # TOTAL SKILLS LEADERBOARD
    # ----------------------
    if target_lower == "total":
        combined = {}
        for player_key, skills in player_skills.items():
            full_skills = DEFAULT_SKILLS.copy()
            full_skills.update(skills)
            combined[player_key] = sum(full_skills.values())

        for player in online_players:
            pk = player.lower()
            if pk not in combined:
                combined[pk] = 0

        top = sorted(combined.items(), key=lambda x: x[1], reverse=True)[:10]

        if not top:
            await interaction.response.send_message("```📊 - No skill data yet.```")
            return

        lines = []
        for p, total in top:
            display_name_cap = p.capitalize()
            status = "🟢" if p in [pl.lower() for pl in online_players] else "🔴"
            lines.append(f"{status} - {display_name_cap}: {total}")

        await interaction.response.send_message(
            f"```📊 - Top 10 Players by Total Skills:\n" + "\n".join(lines) + "```"
        )
        return  # <<< THIS RETURN IS CRUCIAL

    # ----------------------
    # SKILL-SPECIFIC LEADERBOARD
    # ----------------------
    skill_key = SKILL_ALIASES.get(target_lower, target.title())
    if skill_key in SKILL_EMOJIS:
        top_list = []
        for player_key, skills in player_skills.items():
            lvl = skills.get(skill_key, 0)
            top_list.append((player_key, lvl))

        for player in online_players:
            pk = player.lower()
            if pk not in [p for p,_ in top_list]:
                top_list.append((pk, 0))

        top = sorted(top_list, key=lambda x:x[1], reverse=True)[:10]
        emoji = SKILL_EMOJIS.get(skill_key, '')
        lines = []
        for p, lvl in top:
            status = "🟢" if p in [pl.lower() for pl in online_players] else "🔴"
            lines.append(f"{status} - {p}: {lvl}")

        await interaction.response.send_message(
            f"```{emoji} - Top 10 Players by {SKILL_DISPLAY.get(skill_key, skill_key)}:\n" + "\n".join(lines) + "```"
        )
        return

    # OTHERWISE TREAT AS PLAYER NAME
    player_key = target_lower
    if player_key not in player_skills:
        player_skills[player_key] = DEFAULT_SKILLS.copy()

    skills = player_skills[player_key]
    display_name = target.capitalize()
    status = "🟢 Online" if player_key in [pl.lower() for pl in online_players] else "🔴 Offline"

    # Sort skills by highest first
    sorted_skills = sorted(skills.items(), key=lambda x: x[1], reverse=True)

    lines = []
    for skill_name, lvl in sorted_skills:
        if lvl == 0:
            continue  # optional: skip 0-level skills
        emoji = SKILL_EMOJIS.get(skill_name, '')
        display_name_skill = SKILL_DISPLAY.get(skill_name, skill_name)
        lines.append(f"{emoji} {display_name_skill}: {lvl}")

    await interaction.response.send_message(f"```{status} - {display_name}'s Skills\n" + "\n".join(lines) + "```")

    # # ----------------------
    # # TOTAL SKILLS LEADERBOARD
    # # ----------------------
    # if target_lower == "total":
    #     combined = {}
    #     for player_key, skills in player_skills.items():
    #         full_skills = DEFAULT_SKILLS.copy()
    #         full_skills.update(skills)
    #         combined[player_key] = sum(full_skills.values())

    #     if not combined:
    #         await ctx.send("```📊 - No skill data yet.```")
    #         return

    #     top = sorted(combined.items(), key=lambda x: x[1], reverse=True)[:10]

    #     lines = []
    #     for p, total in top:
    #         status = "🟢" if p in [pl.lower() for pl in online_players] else "🔴"
    #         lines.append(f"{status} - {p}: {total}")

    #     await ctx.send(
    #         "```📊 - Top 10 Players by Total Skills:\n"
    #         + "\n".join(lines)
    #         + "```"
    #     )
    #     return

    # # ----------------------
    # # OTHERWISE TREAT AS PLAYER NAME
    # # ----------------------
    # player_key = target_lower

    # if player_key not in player_skills:
    #     await ctx.send(f"```❌ - No skill data found for {target.capitalize()}.```")
    #     return

    # skills = player_skills[player_key]
    # display_name = target.capitalize()
    # status = "🟢 Online" if player_key in [pl.lower() for pl in online_players] else "🔴 Offline"

    # # Collect skills above level 0
    # skill_list = []
    # for skill_name, lvl in skills.items():
    #     if lvl > 1:
    #         skill_list.append((skill_name, lvl))

    # # Sort by level (highest first)
    # skill_list.sort(key=lambda x: x[1], reverse=True)

    # lines = []
    # for skill_name, lvl in skill_list:
    #     emoji = SKILL_EMOJIS.get(skill_name, '')
    #     display_name_skill = SKILL_DISPLAY.get(skill_name, skill_name)
    #     lines.append(f"{emoji} {display_name_skill}: {lvl}")

    # if not lines:
    #     await ctx.send(f"```{status} - {display_name} has no learned skills yet.```")
    #     return

    # msg = f"```{status} - {display_name}'s Skills\n" + "\n".join(lines) + "```"
    # await ctx.send(msg)


@tree.command(name="commands", description="Show all available commands")
async def commands_slash(interaction: discord.Interaction):
    await interaction.response.send_message(
        "📜 **Available Commands:**\n"
        "• `/online` — Show currently online players.\n"
        "• `/time [player]` — Show total playtime for a player.\n"
        "• `/time all` — Show top 10 players by playtime.\n"
        "• `/skill [skill]` — Show top 10 players by a skill.\n"
        "• `/skill [player]` — Show a specific players skills.\n"
        "• `/skill total` — Show top 10 players by total skill levels.\n"
        "• `/commands` — Show this list."
    )



# --------------------
# START BOT
# --------------------
bot.run(settings_discord[target_bot]['botToken'])

