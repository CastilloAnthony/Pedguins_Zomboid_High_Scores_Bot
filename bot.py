# This file developed by Peter Mann (Pedguin) and includes modifications made by Anthony Castillo (ComradeWolf)
# Last Update: 2026-24-02
# Code for sync command retrieved from https://about.abstractumbra.dev/discord.py/2023/01/29/sync-command-example.html

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
from typing import Literal, Optional

import traceback
import logging
LOGGER: logging.Logger = logging.getLogger("bot")
# discord.utils.setup_logging(level=logging.INFO) # Enables additional logging info from discord, just nice to see sometimes and not to overwhelming, ALSO DUPLICATES DISCORD LOGGING MSGS :(
logging.getLogger('paramiko').setLevel(logging.WARNING) # Surpresses logging info messages about connecting and closing SFTP
from read_discord_settings import read_discord_settings
from read_connection_settings import read_connection_settings
settings_discord = read_discord_settings()
settings_connection = read_connection_settings()
target_bot = 'pedguinBot' #'personalAssistant' #'Pedguins_Zomboid_High_Scores_Bot'
# Examples of Accessing Data:
# settings_discord['target_bot']['botToken']            # target_bot is a sub-dictionary inside of settings_discord, technically, we could have multiple bots listed in the json.
# settings_connection['RCON_HOST']
# polling_rate = 1/60*60 # Seconds (Note: 1/60 * 60 is 1 second)

import player_data_functions
# player_data_functions.merge_duplicate_players()
pz_perk_log = player_data_functions.read_json_file('./pz_perk_log.json') # Memory bank

from agent_player_data import Agent_Player_Data
from agent_perk_log import Agent_Perk_Log
from agent_pz_rcon import Agent_PZ_RCON
player_data_agent = Agent_Player_Data() #player_data_functions.read_json_file('./player_data.json')
pz_perk_log_agent = Agent_Perk_Log()
pz_rcon_agent = Agent_PZ_RCON()

# --------------------
# DISCORD INTENTS
# --------------------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
curr_activity = '' # Keeps track of the last status update, we don't need to send an update out if the bot already has the same activity set.
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
curr_activity = "" # Keeps track of the last status update, we don't need to send an update out if the bot already has the same activity set.

# SAVE_FILE = "player_times.json"
# SEEN_SKILLS_FILE = "seen_skills.json"

# --------------------
# SKILL EMOJIS & ALIASES
# --------------------
SKILL_EMOJIS = {
    "Husbandry": "🐴",
    "Animal Care": "🐴",
    "Fitness": "🤸🏻‍♀️",
    "Carving": "🪵",
    "Farming": "🌾",
    "Agriculture": "🌾",
    "Aiming": "🎯",
    "Art": "🎨",
    "Axe": "🪓",
    "Blacksmith": "⚒️",
    "Blacksmithing": "⚒️",
    "Butchering": "🔪",
    "Woodwork": "🪚",
    "Carpentry": "🪚",
    "Cleaning": "🧹",
    "Cooking": "🍳",
    "Dancing": "💃",
    "Electricity": "💡",
    "Electrical": "💡",
    "Doctor": "💊",
    "First Aid": "💊",
    "Fishing": "🎣",
    "PlantScavenging": "🍄",
    "Foraging": "🍄",
    "Glassmaking": "🔍",
    "FlintKnapping": "🪨",
    "Knapping": "🪨",
    "Lightfoot": "👣",
    "Lightfooted": "👣",
    "LongBlade": "⚔️️",
    "Long Blade": "⚔️️",
    "Blunt": "🏏",
    "Long Blunt": "🏏",
    "Maintenance": "🔧",
    "Masonry": "🧱",
    "Mechanics": "🚗",
    "Meditation": "🧘",
    "Music": "🎵",
    "Nimble": "🩰",
    "Pottery": "🏺",
    "Reloading": "💥",
    "Sprinting": "👟",
    "Running": "👟",
    "SmallBlade": "🗡️",
    "SmallBlunt": "🔨",
    "Short Blade": "🗡️",
    "Short Blunt": "🔨",
    "Sneak": "🥷",
    "Sneaking": "🥷",
    "Spear": "🦯",
    "Strength": "💪",
    "Tailoring": "🪡",
    "Tracking": "🐾",
    "Trapping": "🪤",
    "MetalWelding": "🔩",
    "Welding": "🔩",
}

SKILL_ALIASES = {
    # Tailoring
    "tailor": "Tailoring",
    "tailoring": "Tailoring",

    # Electrical
    # "electric": "Electricity",
    # "electrical": "Electricity",
    "electric": "Electrical",
    "electrical": "Electrical",

    # Welding
    # "weld": "MetalWelding",
    # "welding": "MetalWelding",
    "weld": "Welding",
    "welding": "Welding",

    # Long Blade
    # "longblade": "LongBlade",
    # "long blade": "LongBlade",
    "longblade": "Long Blade",
    "long blade": "Long Blade",

    # Long Blunt
    # "longblunt": "Blunt",
    # "long blunt": "Blunt",
    "longblunt": "Long Blunt",
    "long blunt": "Long Blunt",

    # Small Blade
    # "smallblade": "SmallBlade",
    # "small blade": "SmallBlade",
    "smallblade": "Small Blade",
    "small blade": "Small Blade",

    # Small Blunt
    # "smallblunt": "SmallBlunt",
    # "small blunt": "SmallBlunt",
    "smallblunt": "Small Blunt",
    "small blunt": "Small Blunt",

    # Foraging
    # "forage": "PlantScavenging",
    # "foraging": "PlantScavenging",
    # "plantscavenging": "PlantScavenging",
    "forage": "Foraging",
    "foraging": "Foraging",
    "plantscavenging": "Foraging",

    # First Aid
    # "firstaid": "Doctor",
    # "first aid": "Doctor",
    # "doctor": "Doctor",
    "firstaid": "First Aid",
    "first aid": "First Aid",
    "doctor": "First Aid",

    # Knapping
    # "knapping": "FlintKnapping",
    # "flintknapping": "FlintKnapping",
    "knapping": "Knapping",
    "flintknapping": "Knapping",

    # Axe
    "axe": "Axe",

    # Woodworking / Carpentry
    # "wood": "Woodwork",
    # "woodworking": "Woodwork",
    # "carpentry": "Woodwork",
    # "woodwork": "Woodwork",
    "wood": "Carpentry",
    "woodworking": "Carpentry",
    "carpentry": "Carpentry",
    "woodwork": "Carpentry",

    # Husbandry / Animal Care
    # "husbandry": "Husbandry",
    # "animalcare": "Husbandry",
    # "animal care": "Husbandry",
    "husbandry": "Animal Care",
    "animalcare": "Animal Care",
    "animal care": "Animal Care",
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
# def load_times():
#     global total_times
#     try:
#         with open(SAVE_FILE, "r") as f:
#             total_times.update({k.lower(): float(v) for k, v in json.load(f).items()})
#         LOGGER.info("Player total times loaded.")
#     except FileNotFoundError:
#         total_times.clear()
#         LOGGER.info("No previous total times found.")


# def save_times():
#     global total_times
#     with open(SAVE_FILE, "w") as f:
#         json.dump(total_times, f, indent=4)
#     # LOGGER.info("Player total times saved.") # Not necessary and clogs up the terminal with double print alongside save_seen_skills


# def load_seen_skills():
#     global player_skills
#     try:
#         with open(SEEN_SKILLS_FILE, "r") as f:
#             player_skills.update(json.load(f))
#         LOGGER.info("Seen skills loaded.")
#     except FileNotFoundError:
#         player_skills.clear()
#         LOGGER.info("No previous skill data found.")


# def sanitize_player_skills():
#     """Force all player keys to lowercase and ensure full DEFAULT_SKILLS"""
#     global player_skills
#     fixed = {}
#     for key, skills in player_skills.items():
#         full = DEFAULT_SKILLS.copy()
#         if isinstance(skills, dict):
#             full.update(skills)
#         fixed[key.lower()] = full

#     player_skills.clear()
#     player_skills.update(fixed)
#     LOGGER.info("Player skills sanitized (lowercase keys, defaults filled).")


# def save_seen_skills():
#     global player_skills
#     with open(SEEN_SKILLS_FILE, "w") as f:
#         json.dump(player_skills, f, indent=4)
#     # LOGGER.info("Seen skills saved.") # Not necessary and clogs up the terminal with double print alongside save_times


# ---- initial load on startup ----
# load_times()
# load_seen_skills()
# sanitize_player_skills()

# temp_player_data = player_data_functions.check_old_player_data()
# if not temp_player_data:
#     pass
# else:
#     for key, value in temp_player_data.items():
#         if key not in player_data:
#             player_data[key] = value

# New data is always saved now
# atexit.register(save_times)
# atexit.register(save_seen_skills)
# atexit.register(player_data_functions.save_json_file, player_data, './player_data.json')
# atexit.register(player_data_functions.save_data_file, pz_perk_log, './pz_perk_log.json')


# --------------------
# SERVER STATUS ANNOUNCE
# --------------------
async def announce_server_status(online: bool = False):
    global settings_discord, target_bot
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
    global bot, tree
    LOGGER.info(f"{bot.user} has connected to Discord!")

    # Sync slash commands ( Syncing here could cause us to become ratelimited by discord )
    # Instead we will sync commands with the /sync command now (and temporarily in the /commands)
    # await tree.sync()  # Will be moved to the sync command in the future (once we verify that command works/is available)
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
    global online_players #, player_sessions, total_times, player_survival_time, player_skills, server_online
    global pz_perk_log_agent, player_data_agent, pz_rcon_agent, settings_discord, target_bot
    channel = bot.get_channel(settings_discord[target_bot]['ANNOUNCE_CHANNEL_ID'])
    death_channel = bot.get_channel(settings_discord[target_bot]['ANNOUNCE_CHANNEL_ID'])

    # try:
    # --- RCON: get online players ---
    # try:
    #     with MCRcon(settings_connection['RCON_HOST'], settings_connection['RCON_PASSWORD'], port=settings_connection['RCON_PORT']) as rcon:
    #         server_online = True
    #         response = rcon.command("players") or rcon.command("who")
    # except Exception:
    #     online_players.clear()
    #     server_online = False
    #     error = traceback.format_exc()
    #     lines = error.split('\n')
    #     LOGGER.info('Can\'t reach Project Zomboid Server '+str(lines[-2]))
    #     return
    # current_players = set()
    # now = time.time()

    # # --- Parse RCON player list ---
    # for line in response.splitlines():
    #     clean = line.strip().lstrip("-•* ").strip()
    #     lower = clean.lower()
    #     if not clean or "unknown command" in lower or lower.startswith(("players","connected","there are","total")):
    #         continue
    #     if not clean.replace("_","").isalnum():
    #         continue
    #     current_players.add(lower)

    # now = time.time()
    
    
    pz_rcon_agent.poll_pz_server()
    player_data_agent.poll_player_data()
    pz_perk_log_agent.poll_perk_log()
    current_players = pz_rcon_agent.get_online_players()
    
    # print('current_players = ', current_players)
    # print('online_players = ', online_players)
    # --- Handle joins ---
    for player in current_players - online_players:
        # player_sessions[player] = now
        # player_survival_time.setdefault(player, 0)
        # player_skills.setdefault(player, DEFAULT_SKILLS.copy())
        if channel and curr_activity != '':
            if player in player_data_agent.get_player_data():
                player_data_agent.update_player_last_login(player, time.time())
                await channel.send(f"```🟢 - {player.capitalize()} has joined the server!```")

    # --- Handle leaves ---
    for player in online_players - current_players:
        # start = player_sessions.pop(player, now)
        # session = now - player_data[player]['lastLogin']
        # total_times[player] = total_times.get(player, 0) + session
        # player_survival_time[player] = player_survival_time.get(player, 0) + session
        duration = time.time() - player_data_agent.get_player_data()[player]['lastLogin']
        h, m, s = int(duration//3600), int((duration%3600)//60), int((duration%3600)%60)
        if channel:
            await channel.send(f"```🔴 - {player.capitalize()} has left the server.\nSession: {h}h {m}m {s}s```")

    # --- Increment survival and total time for current online players ---
    for player in current_players & online_players:
        # session = now - player_sessions.get(player, now)
        # total_times[player] = total_times.get(player, 0) + session
        # player_survival_time[player] = player_survival_time.get(player, 0) + session
        # player_sessions[player] = now
        # print(f'{player} {session} {player_survival_time.get(player, 0)} {total_times.get(player, 0)}')
        if player in player_data_agent.get_player_data():
            player_data_agent.update_player_total_play_time(player)#, time.time() - player_data_agent.get_player_data()[player]['lastPoll'])
            # player_data_agent.update_player_last_poll(player, time.time())
            # player_data[player]['totalPlayTime'] += time.time() - player_data[player]['lastPoll']
            # player_data[player]['lastPoll'] = time.time()
            # player_data[player] = player_data_functions.create_default_player_data(username=player)
            # player_data_functions.save_json_file(json_dict=player_data, file_path='./player_data.json')
        # if 'totalPlayTime' not in player_data[player]: # Temporary until we find the real problem
        #     player_data[player]['totalPlayTime'] = 0
        
    # player_data_functions.save_json_file(json_dict=player_data, file_path='./player_data.json')

    online_players.clear()
    online_players.update(current_players)

    new_perk_log = pz_perk_log_agent.get_new_log().copy()
    for entry in new_perk_log:
        if new_perk_log[entry]['type'] == 'unhandled':
            pz_perk_log_agent.update_new_perk_log(new_perk_log[entry]['timestamp'])
            continue
        if new_perk_log[entry]['type'] == 'skills':
            pz_perk_log_agent.update_new_perk_log(new_perk_log[entry]['timestamp'])
        elif new_perk_log[entry]['type'] == 'login':
            pz_perk_log_agent.update_new_perk_log(new_perk_log[entry]['timestamp'])
        elif new_perk_log[entry]['type'] == 'creation':
            pz_perk_log_agent.update_new_perk_log(new_perk_log[entry]['timestamp'])
        elif new_perk_log[entry]['type'] == 'died':
            # In-game time
            player = player_data_agent.get_player_data()[new_perk_log[entry]['username']]
            in_game_days = int(player['hours_survived'] // (24))
            in_game_hours = int(player['hours_survived'])
            in_game_minutes = int(player['hours_survived'] * 60)
            if player['hours_survived'] >= 1:
                in_game_str = f"{in_game_days} days {in_game_hours} hours {in_game_minutes} minutes" if in_game_days > 0 else f"{in_game_hours} hours {in_game_minutes} minutes"
            else:
                in_game_str = "less than 1 hour"
            # Real-life time 
            # # 1 Full In-Game Day is 1 IRL Hour
            in_game_hours = player['hours_survived']
            real_days = int(in_game_hours // 24*24) # 24 Hours is 576 Zomboid Hours
            real_hours = int(in_game_hours // 24) # 1 Hour is 24 Zomboid Hours
            real_mins = int(in_game_hours // (24/60)) # 1/60 Hours is 0.4 Zomboid Hours
            if real_mins >= 1:
                real_str = f"{real_days} days {real_hours} hours {real_mins} minutes" if real_days > 0 else f"{real_hours} hours {real_mins} minutes"
            else:
                real_str = "less than a minute"
            msg = f"""
            ```💀 {new_perk_log[entry]['username']} has died.
            Survived in-game: {in_game_str}
            Real-life: {real_str}```
            """
            if death_channel:
                await death_channel.send(msg)
            pz_perk_log_agent.update_new_perk_log(new_perk_log[entry]['timestamp'])
        elif new_perk_log[entry]['type'] == 'levelUp':
            # if int(player_data[entry['username']]['skills'][entry['skill']]) < int(entry['level']): # Level Up
            #     player_data[entry['username']]['skills'][entry['skill']] = entry['level']
            #     msg = f"```🎉 {entry['username']} has leveled up their {entry['skill']} to {entry['level']}! {SKILL_EMOJIS.get(entry['skill'], "")}```"
            #     channel = bot.get_channel(settings_discord[target_bot]['LEVELUP_CHANNEL_ID'])
            #     if channel:
            #         await channel.send(msg)
            # else:
            #     player_data[entry['username']]['skills'][entry['skill']] = entry['level']
            pz_perk_log_agent.update_new_perk_log(new_perk_log[entry]['timestamp'])



    # # --- SFTP: Check PerkLog for deaths & level-ups ---
    # try:
    #     transport = paramiko.Transport((settings_connection['SFTP_HOST'], settings_connection['SFTP_PORT']))
    #     transport.connect(username=settings_connection['SFTP_USER'], password=settings_connection['SFTP_PASS'])
    #     sftp = paramiko.SFTPClient.from_transport(transport)

    #     files = sftp.listdir(settings_connection['LOG_DIR'])
    #     perk_logs = [f for f in files if f.endswith("_PerkLog.txt")]

    #     if perk_logs:
    #         latest_file = sorted(perk_logs)[-1]
    #         remote_path = os.path.join(settings_connection['LOG_DIR'], latest_file)

    #         # --- Correctly indented file reading ---
    #         with sftp.open(remote_path, "r") as f:
    #             for line in f:
    #                 parsed = player_data_functions.log_parser(line)
    #                 if parsed['timestamp'] not in pz_perk_log: # This line hasn't been added to the bot yet.
    #                     pz_perk_log[parsed['timestamp']] = parsed

    #                     if parsed['type'] == 'unhandled':
    #                         player_data_functions.save_json_file(json_dict=pz_perk_log, file_path='./pz_perk_log.json')
    #                         continue
    #                     if parsed['username'] not in player_data: # Detected a player not already player_data, creating a default
    #                         player_data[parsed['username']] = player_data_functions.create_default_player_data(username=parsed['username'], user_id=parsed['user_id'])
    #                         player_data_functions.save_json_file(json_dict=player_data, file_path='./player_data.json')
    #                     if player_data[parsed['username']]['user_id'] == 'None' or parsed['user_id'] != player_data[parsed['username']]['user_id']:
    #                         player_data[parsed['username']]['user_id'] = parsed['user_id']
    #                         player_data_functions.save_json_file(json_dict=player_data, file_path='./player_data.json')
    #                     if parsed['type'] == 'skills':
    #                         player_data[parsed['username']]['hoursSurvived'] = parsed['hoursSurvived']
    #                         player_data[parsed['username']]['skills'] = parsed['skills']
    #                         player_data_functions.save_json_file(json_dict=player_data, file_path='./player_data.json')
    #                     elif parsed['type'] == 'login':
    #                         player_data[parsed['username']]['characterLastLogin'] = time.time()
    #                         player_data[parsed['username']]['hoursSurvived'] = parsed['hoursSurvived']
    #                     elif parsed['type'] == 'creation':
    #                         player_data[parsed['username']]['hoursSurvived'] = parsed['hoursSurvived']
    #                         player_data[parsed['username']]['characterLastLogin'] = time.time()
    #                         player_data[parsed['username']]['skills'] = DEFAULT_SKILLS.copy()
    #                         player_data_functions.save_json_file(json_dict=player_data, file_path='./player_data.json')
    #                     elif parsed['type'] == 'died':
    #                         # In-game time
    #                         # print(parsed['hoursSurvived'])
    #                         in_game_days = int(parsed['hoursSurvived'] // 24)
    #                         in_game_hours = int(parsed['hoursSurvived'] % 24)
    #                         if parsed['hoursSurvived'] >= 1:
    #                             in_game_str = f"{in_game_days} days {in_game_hours} hours" if in_game_days > 0 else f"{in_game_hours} hours"
    #                         else:
    #                             in_game_str = "less than 1 hour"
    #                         # Real-life time 
    #                         # # 1 Full In-Game Day is 1 IRL Hour
    #                         in_game_hours = parsed['hoursSurvived']
    #                         real_days = int(in_game_hours // 24*24) # 24 Hours is 576 Zomboid Hours
    #                         real_hours = int(in_game_hours // 24) # 1 Hour is 24 Zomboid Hours
    #                         real_mins = int(in_game_hours // (24/60)) # 1/60 Hours is 0.4 Zomboid Hours
    #                         # real_days = int(real_minutes // (24*60))
    #                         # real_hours = int((real_minutes % (24*60)) // 60)
    #                         # real_mins = int(real_minutes % 60)
    #                         # print(real_days, real_hours, real_mins)
    #                         if real_mins >= 1:
    #                             real_str = f"{real_days} days {real_hours} hours {real_mins} minutes" if real_days > 0 else f"{real_hours} hours {real_mins} minutes"
    #                         else:
    #                             real_str = "less than a minute"
    #                         msg = f"""
    #                         ```💀 {parsed['username']} has died.
    #                         Survived in-game: {in_game_str}
    #                         Real-life: {real_str}```
    #                         """
    #                         if death_channel:
    #                             await death_channel.send(msg)
    #                     elif parsed['type'] == 'levelUp':
    #                         player_data[parsed['username']]['user_id'] = parsed['user_id'] # Probably don't need to be updating this this
    #                         player_data[parsed['username']]['hoursSurvived'] = parsed['hoursSurvived']
    #                         # player_data[parsed['username']]['skills'] = DEFAULT_SKILLS.copy()
    #                         # player_data[parsed['username']]['skills'][parsed['skill']] = parsed['level']
    #                         if int(player_data[parsed['username']]['skills'][parsed['skill']]) < int(parsed['level']): # Level Up
    #                             player_data[parsed['username']]['skills'][parsed['skill']] = parsed['level']
    #                             player_data_functions.save_json_file(json_dict=player_data, file_path='./player_data.json')
    #                             msg = f"```🎉 {parsed['username']} has leveled up their {parsed['skill']} to {parsed['level']}! {SKILL_EMOJIS.get(parsed['skill'], "")}```"
    #                             channel = bot.get_channel(settings_discord[target_bot]['LEVELUP_CHANNEL_ID'])
    #                             if channel:
    #                                 await channel.send(msg)
    #                         else:
    #                             player_data[parsed['username']]['skills'][parsed['skill']] = parsed['level']
    #                             player_data_functions.save_json_file(json_dict=player_data, file_path='./player_data.json')
    #                         # elif int(player_data[parsed['username']]['skills'][parsed['skill']]) > int(parsed['level']): # Level Down
    #                         #     player_data[parsed['username']]['skills'][parsed['skill']] = parsed['level']
    #                         #     player_data_functions.save_data_file(player_data)
    #                         #     msg = f"```🎉 {parsed['username']} has leveled down their {parsed['skill']} to {parsed['level']}! {SKILL_EMOJIS.get(parsed['skill'], "")}```"
    #                         #     channel = bot.get_channel(settings_discord[target_bot]['LEVELUP_CHANNEL_ID'])
    #                         #     if channel:
    #                         #         await channel.send(msg)
    #                     player_data_functions.save_json_file(json_dict=pz_perk_log, file_path='./pz_perk_log.json')
    #                 else:
    #                     continue
    #     sftp.close()
    #     transport.close()
    # except:
    #     error = traceback.format_exc()
    #     lines = error.split('\n')
    #     LOGGER.info('Can\'t reach Bisect Hosting '+str(lines[-2]))
    #     return
    # save_times()
    # save_seen_skills()
                # line = line.strip()

                # # --- Death detection ---
                # if "[Died]" in line and line not in seen_deaths:
                #     seen_deaths.add(line)
                #     try:
                #         parts = re.findall(r"\[(.*?)\]", line)
                #         player_name = parts[2]  # original name
                #         player_key = parts[1]
                #         hours_survived = float(parts[-1].replace("Hours Survived: ","").replace(".",""))

                #         # Reset skills and survival time
                #         player_skills[player_key] = DEFAULT_SKILLS.copy()
                #         player_survival_time[player_key] = 0
                #         LOGGER.info(f"{player_name.capitalize()}'s skills and survival time reset due to death.")

                #         # In-game time
                #         in_game_days = int(hours_survived // 24)
                #         in_game_hours = int(hours_survived % 24)
                #         if hours_survived >= 1:
                #             in_game_str = f"{in_game_days} days {in_game_hours} hours" if in_game_days > 0 else f"{in_game_hours} hours"
                #         else:
                #             in_game_str = "less than 1 hour"

                #         # Real-life time
                #         real_minutes = hours_survived * 3.75
                #         real_days = int(real_minutes // (24*60))
                #         real_hours = int((real_minutes % (24*60)) // 60)
                #         real_mins = int(real_minutes % 60)
                #         if real_minutes >= 1:
                #             real_str = f"{real_days} days {real_hours} hours {real_mins} minutes" if real_days > 0 else f"{real_hours} hours {real_mins} minutes"
                #         else:
                #             real_str = "less than a minute"

                #         # Capitalize for display
                #         display_name = player_name.capitalize()

                #         # Send multi-line death message
                #         msg = f"""
                #         ```💀 {display_name} has died.
                #         Survived in-game: {in_game_str}
                #         Real-life: {real_str}```
                #         """
                #         if death_channel:
                #             await death_channel.send(msg)

                #     except Exception as e:
                #         LOGGER.info(f"Error parsing death line: {e}")

                #     continue  # skip other processing for this line

                # # --- Level-up detection ---
                # if line in seen_levelups:
                #     continue
                # if "[Created Player" in line:
                #     seen_levelups.add(line)
                #     continue
                # if "=" in line:
                #     try:
                #         bracketed = re.findall(r"\[(.*?)\]", line)
                #         if len(bracketed) < 5:
                #             continue
                #         player_key = bracketed[1]
                #         display_name = bracketed[2]
                #         skills_str = bracketed[4] if "=" in bracketed[4] else ""
                #         if not skills_str:
                #             continue
                #         player_skills.setdefault(player_key, DEFAULT_SKILLS.copy())
                #         for pair in skills_str.split(", "):
                #             if "=" in pair:
                #                 skill_name, lvl = pair.split("=")
                #                 skill_name = skill_name.strip()
                #                 lvl = int(''.join(filter(str.isdigit, lvl)) or 0)
                #                 if skill_name in DEFAULT_SKILLS:
                #                     player_skills[player_key][skill_name] = lvl
                #         seen_levelups.add(line)
                #     except Exception as e:
                #         LOGGER.info(f"Error parsing skill line: {e}")

                # if "[Level Changed]" in line:
                #     seen_levelups.add(line)
                #     try:
                #         parts = line.split("][")
                #         player_key = parts[1].lower()
                #         display_name = parts[1]
                #         skill = parts[4]
                #         level = int(parts[5].strip("]."))
                #         emoji = SKILL_EMOJIS.get(skill, "")
                #         player_skills.setdefault(player_key, DEFAULT_SKILLS.copy())[skill] = level
                #         display_name_cap = display_name.capitalize()
                #         msg = f"```🎉 {display_name_cap} has leveled up their {skill} to {level}! {emoji}```"

                #         channel = bot.get_channel(settings_discord[target_bot]['LEVELUP_CHANNEL_ID'])
                #         if channel:
                #             await channel.send(msg)
                #     except Exception:
                #         LOGGER.info(f"Error parsing level-up line: {line}")

    # sftp.close()
    # transport.close()
    # save_times()
    # save_seen_skills()
    # LOGGER.info(f'Players successfully polled and new data is available!') # Also not necessary, but I thought you might like to keep some info in the terminal as you had before.

    # except Exception as e:
    #     if server_online:
    #         server_online = False
    #         online_players.clear()
    #         player_sessions.clear()
    #         # await announce_server_status(False)
    #     LOGGER.info(f"Polling error: {e}")


# --------------------
# DISCORD STATUS
# --------------------
# @tasks.loop(seconds=polling_rate)
async def update_status():
    global curr_activity #, online_players, server_online
    try:
        if pz_rcon_agent.get_server_status():
            activity_name = ""
            if len(pz_rcon_agent.get_online_players())==0:
                activity_name = "🟢 Server Online"
            else:
                activity_name = f"🟢 {len(pz_rcon_agent.get_online_players())} Survivors Online"
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
@tasks.loop(seconds=settings_connection['POLLING_RATE'])
async def periodic_save():
    await poll_players()
    await update_status()
    # We should save whenever we retrieve new data. These has been moved to the end of poll_players()
    # save_times()
    # save_seen_skills()
# end periodic_save

# --------------------
# COMMANDS (Slash)
# --------------------

@tree.command(name="online", description="Show currently online players.")
async def online_slash(interaction: discord.Interaction):
    global pz_rcon_agent
    global player_data_agent

    if not pz_rcon_agent.get_online_players():
        await interaction.response.send_message("```🟢 - No players are currently online.```")
        return
    lines = []
    now = time.time()
    for player in sorted(pz_rcon_agent.get_online_players()):
        if player in player_data_agent.get_player_data():
            duration = now - player_data_agent.get_player_data()[player]['lastLogin'] #player_sessions.get(player, now)
            h, m, s = int(duration//3600), int((duration%3600)//60), int((duration%(60*60)%60))
            lines.append(f"- {player.capitalize()} ({h}h {m}m {s}s)")
    await interaction.response.send_message(f"```🟢 - Players Online (Session Time):\n" + "\n".join(lines) + f"\n\nTotal: {len(pz_rcon_agent.get_online_players())}```")
# end online_slash

@tree.command(name="time", description="Show total playtime for a player.")
@app_commands.describe(target="Player name or 'all'")
async def time_slash(interaction: discord.Interaction, target: str):
    global pz_rcon_agent #, player_sessions, total_times
    global player_data_agent

    if target.lower() == "all":
        player_times = []
        for player in player_data_agent.get_player_data():
            player_data = player_data_agent.get_player_data()[player]
            if player in pz_rcon_agent.get_online_players():
                player_times.append((player, player_data['totalPlayTime']+(time.time()-player_data['lastPoll'])))
            else:
                player_times.append((player, player_data['totalPlayTime']))
        player_times = sorted(player_times, key=lambda tup: tup[1], reverse=True)
        lines = []
        for p, sec in player_times[:10]: # Top 10 (arrays/lists start at 0 and this syntax goes up to, but does not include the last index)
            h, m, s = int(sec//3600), int((sec%3600)//60), int((sec%3600)%60)
            status = "🟢" if p in pz_rcon_agent.get_online_players() else "🔴"
            lines.append(f"{status} - {p.capitalize()}: {h}h {m}m {s}s")
        await interaction.response.send_message("```🕒 - Top 10 Players by Total Playtime:\n" + "\n".join((lines)) + "```")
    elif target.lower() in player_data_agent.get_player_data(): # A Singlar Player
        player_data = player_data_agent.get_player_data()[target.lower()]
        h, m, s = 0, 0, 0
        if target.lower() in pz_rcon_agent.get_online_players():
            player_time = player_data['totalPlayTime']+(time.time()-player_data['lastPoll'])
            h, m, s = int(player_time//3600), int((player_time%3600)//60), int((player_time%3600)%60)
        else:
            h, m, s = int(player_data['totalPlayTime']//3600), int((player_data['totalPlayTime']%3600)//60), int((player_data['totalPlayTime']%3600)%60)
        status = "🟢" if target.lower() in pz_rcon_agent.get_online_players() else "🔴"
        await interaction.response.send_message(f"```{status} - {target.capitalize()} has played for {h}h {m}m {s}s in total.```")
    else:
        await interaction.response.send_message(f'```Could not find a player named {target}.```')
            
    # now = time.time()
    # if target.lower() == "all":
    #     combined = {p:t for p,t in total_times.items()}
    #     for p in online_players:
    #         combined[p] = combined.get(p,0) + (now - player_sessions.get(p,now))
    #     top = sorted(combined.items(), key=lambda x:x[1], reverse=True)[:10]
    #     if not top:
    #         await interaction.response.send_message("```🕒 - No playtime recorded yet.```")
    #         return
    #     lines = []
    #     for p, sec in top:
    #         h, m = int(sec//3600), int((sec%3600)//60)
    #         status = "🟢" if p in online_players else "🔴"
    #         lines.append(f"{status} - {p.capitalize()}: {h}h {m}m")
    #     await interaction.response.send_message("```🕒 - Top 10 Players by Total Playtime:\n" + "\n".join(lines) + "```")
    #     return

    # player = target.lower()
    # total = total_times.get(player,0)
    # if player in online_players:
    #     total += now - player_sessions.get(player,now)
    # h, m = int(total//3600), int((total%3600)//60)
    # status = "🟢" if player in online_players else "🔴"
    # await interaction.response.send_message(f"```{status} - {player.capitalize()} has played {h}h {m}m total.```")
# end time_slash

@tree.command(name="survived", description="Shows the total time a player's current character has survived for in in-game hours.")
@app_commands.describe(target="Player name or 'all'")
async def survived_slash(interaction: discord.Interaction, target: str):
    global pz_rcon_agent
    global player_data_agent
    
    if target.lower() == "all":
        player_times = []
        for player in player_data_agent.get_player_data():
            player_data = player_data_agent.get_player_data()[player]
            player_times.append((player_data['username'], player_data['hours_survived']%24, player_data['hours_survived']//24, player_data['hours_survived']))
        player_times = sorted(player_times, key=lambda tup: tup[3], reverse=True)
        lines = []
        for p, hours, days, _ in player_times[:10]: # Top 10 (arrays/lists start at 0 and this syntax goes up to, but does not include the last index)
            status = "🟢" if p in pz_rcon_agent.get_online_players() else "🔴"
            lines.append(f"{status} - {p.capitalize()}: {int(days)} days {int(hours)} hours")
        await interaction.response.send_message("```🕒 - Top 10 Current Character by In-Game Survival Hours:\n" + "\n".join((lines)) + "```")
    elif target.lower() in player_data_agent.get_player_data(): # A Singlar Player
        player_data = player_data_agent.get_player_data()[target.lower()]
        days = int(player_data['hours_survived']//24)
        hours = int(player_data['hours_survived']%24)
        status = "🟢" if target.lower() in pz_rcon_agent.get_online_players() else "🔴"
        await interaction.response.send_message(f"```{status} - {target.capitalize()} has survived for {days} days and {hours} hours in-game.```")
    else:
        await interaction.response.send_message(f'```Could not find a player named {target}.```')
# end survived_slash

@tree.command(name="zombies", description="Shows a player's total zombie kills.")
@app_commands.describe(target="Player name or 'all'")
async def zombies_slash(interaction: discord.Interaction, target: str):
    global pz_rcon_agent
    global player_data_agent
    
    if target.lower() == "all":
        player_times = []
        for player in player_data_agent.get_player_data():
            player_data = player_data_agent.get_player_data()[player]
            player_times.append((player_data['username'], player_data['zombie_kills']))
        player_times = sorted(player_times, key=lambda tup: tup[1], reverse=True)
        lines = []
        for p, kills in player_times[:10]: # Top 10 (arrays/lists start at 0 and this syntax goes up to, but does not include the last index)
            status = "🟢" if p in pz_rcon_agent.get_online_players() else "🔴"
            lines.append(f"{status} - {p.capitalize()}: {kills} zombies")
        await interaction.response.send_message("```🕒 - Top 10 Current Character by Zombie Kills:\n" + "\n".join((lines)) + "```")
    elif target.lower() in player_data_agent.get_player_data(): # A Singlar Player
        player_data = player_data_agent.get_player_data()[target.lower()]
        zombies = player_data['zombie_kills']
        status = "🟢" if target.lower() in pz_rcon_agent.get_online_players() else "🔴"
        await interaction.response.send_message(f"```{status} - {target.capitalize()} has killed {zombies} zombies.```")
    else:
        await interaction.response.send_message(f'```Could not find a player named {target}.```')
# end zombies_slash

# @tree.command(name="survivors", description="Shows a player's total survivor kills.")
# @app_commands.describe(target="Player name or 'all'")
# async def survivors_slash(interaction: discord.Interaction, target: str):
#     global pz_rcon_agent
#     global player_data_agent
    
#     if target.lower() == "all":
#         player_times = []
#         for player in player_data_agent.get_player_data():
#             player_data = player_data_agent.get_player_data()[player]
#             player_times.append((player_data['username'], player_data['survivor_kills']))
#         player_times = sorted(player_times, key=lambda tup: tup[1], reverse=True)
#         lines = []
#         for p, kills in player_times[:10]: # Top 10 (arrays/lists start at 0 and this syntax goes up to, but does not include the last index)
#             status = "🟢" if p in pz_rcon_agent.get_online_players() else "🔴"
#             lines.append(f"{status} - {p.capitalize()}: {kills} survivors")
#         await interaction.response.send_message("```🕒 - Top 10 Current Character by Survivors Kills:\n" + "\n".join((lines)) + "```")
#     elif target.lower() in player_data_agent.get_player_data(): # A Singlar Player
#         player_data = player_data_agent.get_player_data()[target.lower()]
#         survivors = player_data['survivor_kills']
#         status = "🟢" if target.lower() in pz_rcon_agent.get_online_players() else "🔴"
#         await interaction.response.send_message(f"```{status} - {target.capitalize()} has killed {survivors} survivors.```")
#     else:
#         await interaction.response.send_message(f'```Could not find a player named {target}.```')
# # end zombies_slash

@tree.command(name="skill", description="Show a player's skills or leaderboard for a skill")
@app_commands.describe(target="Skill name, player name, 'total' or 'all'.")
async def skill_slash(interaction: discord.Interaction, target: str):
    global pz_rcon_agent #online_players, player_skills
    global player_data_agent
    target_lower = target.lower()

    # ----------------------
    # TOTAL SKILLS LEADERBOARD
    # ----------------------
    if target_lower == "total" or target_lower == 'all':
        combined = {}
        # for player_key, skills in player_skills.items():
        #     full_skills = DEFAULT_SKILLS.copy()
        #     full_skills.update(skills)
        #     combined[player_key] = sum(full_skills.values())

        # for player in online_players:
        #     pk = player.lower()
        #     if pk not in combined:
        #         combined[pk] = 0

        for player in player_data_agent.get_player_data():
            player_data = player_data_agent.get_player_data()[player]
            combined[player] = sum(player_data['perks'].values())

        top = sorted(combined.items(), key=lambda x: x[1], reverse=True)[:10]

        if not top:
            await interaction.response.send_message("```📊 - No skill data yet.```")
            return

        lines = []
        for p, total in top:
            display_name_cap = p.capitalize()
            status = "🟢" if p in [pl.lower() for pl in pz_rcon_agent.get_online_players()] else "🔴"
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
        # for player_key, skills in player_skills.items():
        #     lvl = skills.get(skill_key, 0)
        #     top_list.append((player_key, lvl))

        for player in player_data_agent.get_player_data():
            player_data = player_data_agent.get_player_data()[player]
            top_list.append((player, player_data_agent.get_player_data()[player]['perks'][skill_key]))

        for player in pz_rcon_agent.get_online_players():
            pk = player.lower()
            if pk not in [p for p,_ in top_list]:
                top_list.append((pk, 0))
        

        top = sorted(top_list, key=lambda x:x[1], reverse=True)[:10]
        emoji = SKILL_EMOJIS.get(skill_key, '')
        lines = []
        for p, lvl in top:
            status = "🟢" if p in [pl.lower() for pl in pz_rcon_agent.get_online_players()] else "🔴"
            lines.append(f"{status} - {p}: {lvl}")

        await interaction.response.send_message(
            f"```{emoji} - Top 10 Players by {SKILL_DISPLAY.get(skill_key, skill_key)}:\n" + "\n".join(lines) + "```"
        )
        return

    # OTHERWISE TREAT AS PLAYER NAME
    player_key = target_lower
    if player_key not in player_data_agent.get_player_data():
        await interaction.response.send_message(f"```Could not find player with name {player_key}```")
        return
        # player_skills[player_key] = DEFAULT_SKILLS.copy()

    # skills = player_skills[player_key]
    skills = player_data_agent.get_player_data()[player_key]['perks']
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
# end skill_slash

# @tree.command(name='sync', description='Owner only')
# async def sync_slash(interaction: discord.Integration):
#     global tree
#     moderators = [
#         member.id
#         for member in interaction.guild.members
#         if member.guild_permissions.administrator
#     ]
#     if interaction.user.id in moderators:
#         await tree.sync()
#         LOGGER.info('Command tree synced.')
#     else:
#         await interaction.responce.send_message('You must be the owner to use this command!')
# # end sync_slash

# Code for sync command retrieved from https://about.abstractumbra.dev/discord.py/2023/01/29/sync-command-example.html
@bot.command()
@commands.guild_only()
@commands.is_owner()
async def sync(ctx: commands.Context, guilds: commands.Greedy[discord.Object], spec: Optional[Literal["~", "*", "^"]] = None) -> None:
    LOGGER.info(f'Attempting to sync commands... Please wait.')
    if not guilds:
        if spec == "~":
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "*":
            ctx.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "^":
            ctx.bot.tree.clear_commands(guild=ctx.guild)
            await ctx.bot.tree.sync(guild=ctx.guild)
            synced = []
        else:
            synced = await ctx.bot.tree.sync()

        await ctx.send(
            f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
        )
        LOGGER.info(f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}")
        return

    ret = 0
    for guild in guilds:
        try:
            await ctx.bot.tree.sync(guild=guild)
        except discord.HTTPException:
            pass
        else:
            ret += 1

    await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")
    LOGGER.info(f"Synced the tree to {ret}/{len(guilds)}.")

@tree.command(name="commands", description="Show all available commands")
async def commands_slash(interaction: discord.Interaction):    
    await interaction.response.send_message(
        "📜 **Available Commands:**\n"
        "• `/online` — Show currently online players.\n"
        "• `/time [player]` — Show total playtime for a player.\n"
        "• `/time all` — Show top 10 players by playtime.\n"
        "• `/survived [player]` — Show total hours survived for a player.\n"
        "• `/survived all` — Show top 10 players by survival time.\n"
        "• `/zombies [player]` — Show total zombie kills for a player.\n"
        "• `/zombies all` — Show top 10 players by zombie kills.\n"
        "• `/skill [skill]` — Show top 10 players by a skill.\n"
        "• `/skill [player]` — Show a specific players skills.\n"
        "• `/skill total` — Show top 10 players by total skill levels.\n"
        "• `/commands` — Show this list."
    )
# end commands_slash


# --------------------
# START BOT
# --------------------
if __name__ == '__main__': # This prevents the bot being ran multiple times in different threads, just a safety precaution
    bot.run(settings_discord[target_bot]['botToken'], root_logger=True)

