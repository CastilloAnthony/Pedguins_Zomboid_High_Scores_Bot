# This file developed by Peter Mann (Pedguin) and includes modifications made by Anthony Castillo (ComradeWolf)
# Last Update: 2026-24-02
# Code for sync command retrieved from https://about.abstractumbra.dev/discord.py/2023/01/29/sync-command-example.html

# Native Modules
import time
from typing import Literal, Optional
import logging

# Publicly Available Modules
import discord
from discord.ext import commands, tasks
from discord import app_commands 

# Custom Modules
from read_discord_settings import read_discord_settings
from read_connection_settings import read_connection_settings
from agent_player_data import Agent_Player_Data
# from agent_perk_log import Agent_Perk_Log
from agent_pz_rcon import Agent_PZ_RCON
from player_data_functions import read_json_file

# Variable Initializations
LOGGER: logging.Logger = logging.getLogger("bot")
logging.getLogger('paramiko').setLevel(logging.WARNING) # Surpresses logging info messages about connecting and closing SFTP
settings_discord = read_discord_settings()
settings_connection = read_connection_settings()
target_bot = 'pedguinBot' #'personalAssistant' #'Pedguins_Zomboid_High_Scores_Bot'
pz_perk_log = read_json_file('./pz_perk_log.json') # Memory bank

# Data Agents
player_data_agent = Agent_Player_Data() #player_data_functions.read_json_file('./player_data.json')
# pz_perk_log_agent = Agent_Perk_Log()
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

# --------------------
# SKILL EMOJIS & ALIASES
# --------------------
# SKILL_EMOJIS = {
#     "Husbandry": "🐴",
#     "Animal Care": "🐴",
#     "Fitness": "🤸🏻‍♀️",
#     "Carving": "🪵",
#     "Farming": "🌾",
#     "Agriculture": "🌾",
#     "Aiming": "🎯",
#     "Art": "🎨",
#     "Axe": "🪓",
#     "Blacksmith": "⚒️",
#     "Blacksmithing": "⚒️",
#     "Butchering": "🔪",
#     "Woodwork": "🪚",
#     "Carpentry": "🪚",
#     "Cleaning": "🧹",
#     "Cooking": "🍳",
#     "Dancing": "💃",
#     "Electricity": "💡",
#     "Electrical": "💡",
#     "Doctor": "💊",
#     "First Aid": "💊",
#     "Fishing": "🎣",
#     "PlantScavenging": "🍄",
#     "Foraging": "🍄",
#     "Glassmaking": "🔍",
#     "FlintKnapping": "🪨",
#     "Knapping": "🪨",
#     "Lightfoot": "👣",
#     "Lightfooted": "👣",
#     "LongBlade": "⚔️️",
#     "Long Blade": "⚔️️",
#     "Blunt": "🏏",
#     "Long Blunt": "🏏",
#     "Maintenance": "🔧",
#     "Masonry": "🧱",
#     "Mechanics": "🚗",
#     "Meditation": "🧘",
#     "Music": "🎵",
#     "Nimble": "🩰",
#     "Pottery": "🏺",
#     "Reloading": "💥",
#     "Sprinting": "👟",
#     "Running": "👟",
#     "SmallBlade": "🗡️",
#     "SmallBlunt": "🔨",
#     "Short Blade": "🗡️",
#     "Short Blunt": "🔨",
#     "Sneak": "🥷",
#     "Sneaking": "🥷",
#     "Spear": "🦯",
#     "Strength": "💪",
#     "Tailoring": "🪡",
#     "Tracking": "🐾",
#     "Trapping": "🪤",
#     "MetalWelding": "🔩",
#     "Welding": "🔩",
# }

# SKILL_ALIASES = {
#     # Tailoring
#     "tailor": "Tailoring",
#     "tailoring": "Tailoring",

#     # Electrical
#     # "electric": "Electricity",
#     # "electrical": "Electricity",
#     "electric": "Electrical",
#     "electrical": "Electrical",

#     # Welding
#     # "weld": "MetalWelding",
#     # "welding": "MetalWelding",
#     "weld": "Welding",
#     "welding": "Welding",

#     # Long Blade
#     # "longblade": "LongBlade",
#     # "long blade": "LongBlade",
#     "longblade": "Long Blade",
#     "long blade": "Long Blade",

#     # Long Blunt
#     # "longblunt": "Blunt",
#     # "long blunt": "Blunt",
#     "longblunt": "Long Blunt",
#     "long blunt": "Long Blunt",

#     # Small Blade
#     # "smallblade": "SmallBlade",
#     # "small blade": "SmallBlade",
#     "smallblade": "Small Blade",
#     "small blade": "Small Blade",

#     # Small Blunt
#     # "smallblunt": "SmallBlunt",
#     # "small blunt": "SmallBlunt",
#     "smallblunt": "Small Blunt",
#     "small blunt": "Small Blunt",

#     # Foraging
#     # "forage": "PlantScavenging",
#     # "foraging": "PlantScavenging",
#     # "plantscavenging": "PlantScavenging",
#     "forage": "Foraging",
#     "foraging": "Foraging",
#     "plantscavenging": "Foraging",

#     # First Aid
#     # "firstaid": "Doctor",
#     # "first aid": "Doctor",
#     # "doctor": "Doctor",
#     "firstaid": "First Aid",
#     "first aid": "First Aid",
#     "doctor": "First Aid",

#     # Knapping
#     # "knapping": "FlintKnapping",
#     # "flintknapping": "FlintKnapping",
#     "knapping": "Knapping",
#     "flintknapping": "Knapping",

#     # Axe
#     "axe": "Axe",

#     # Woodworking / Carpentry
#     # "wood": "Woodwork",
#     # "woodworking": "Woodwork",
#     # "carpentry": "Woodwork",
#     # "woodwork": "Woodwork",
#     "wood": "Carpentry",
#     "woodworking": "Carpentry",
#     "carpentry": "Carpentry",
#     "woodwork": "Carpentry",

#     # Husbandry / Animal Care
#     # "husbandry": "Husbandry",
#     # "animalcare": "Husbandry",
#     # "animal care": "Husbandry",
#     "husbandry": "Animal Care",
#     "animalcare": "Animal Care",
#     "animal care": "Animal Care",
# }

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
# end announce_server_status

# --------------------
# PLAYER POLLING + SURVIVAL + SKILL RESET ON DEATH + LEVEL-UPS
# --------------------
async def poll_players():
    global online_players
    global player_data_agent, pz_rcon_agent, settings_discord, target_bot #pz_perk_log_agent
    channel = bot.get_channel(settings_discord[target_bot]['ANNOUNCE_CHANNEL_ID'])
    death_channel = bot.get_channel(settings_discord[target_bot]['ANNOUNCE_CHANNEL_ID'])   
    
    await pz_rcon_agent.poll_pz_server()
    await player_data_agent.poll_player_data()
    # await pz_perk_log_agent.poll_perk_log()
    current_players = pz_rcon_agent.get_online_players()

    # --- Handle joins ---
    for player in current_players - online_players:
        if channel and curr_activity != '':
            if player in player_data_agent.get_player_data():
                player_data_agent.update_player_last_login(player, time.time())
                await channel.send(f"```🟢 - {player.capitalize()} has joined the server!```")

    # --- Handle leaves ---
    for player in online_players - current_players:
        duration = time.time() - player_data_agent.get_player_data()[player]['lastLogin']
        h, m, s = int(duration//3600), int((duration%3600)//60), int((duration%3600)%60)
        if channel:
            await channel.send(f"```🔴 - {player.capitalize()} has left the server.\nSession: {h}h {m}m {s}s```")

    # --- Increment survival and total time for current online players ---
    for player in current_players & online_players:
        if player in player_data_agent.get_player_data():
            player_data_agent.update_player_total_play_time(player)

    online_players.clear()
    online_players.update(current_players)
    level_ups = player_data_agent.get_level_ups()
    skill_emojis = read_json_file('./skill_emojis.json')
    for player_name, perk, new_level, old_level in level_ups:
        msg = f"```🎉 {player_name} has leveled up their {perk} to {new_level}! {skill_emojis.get(perk, "")}```"
        channel = bot.get_channel(settings_discord[target_bot]['LEVELUP_CHANNEL_ID'])
        if channel:
            await channel.send(msg)
    deaths = player_data_agent.get_deaths()
    for player_name, hours_survived, zombie_kills, sum_of_perks, highest_skill, skill_level in deaths:
        # In-game time
        in_game_days = int(hours_survived // (24))
        in_game_hours = int(hours_survived)
        in_game_minutes = int(hours_survived * 60)
        if hours_survived >= 1:
            in_game_str = f"{in_game_days} days {in_game_hours} hours {in_game_minutes} minutes" if in_game_days > 0 else f"{in_game_hours} hours {in_game_minutes} minutes"
        else:
            in_game_str = "less than 1 hour"
        # Real-life time # 1 Full In-Game Day is 1 IRL Hour
        real_days = int(hours_survived // (24*24)) # 24 Hours is 576 Zomboid Hours
        real_hours = int(hours_survived // 24) # 1 Hour is 24 Zomboid Hours
        real_mins = int(hours_survived // (24/60)) # 1/60 Hours is 0.4 Zomboid Hours
        if real_mins >= 1:
            real_str = f"{real_days} days {real_hours} hours {real_mins} minutes" if real_days > 0 else f"{real_hours} hours {real_mins} minutes"
        else:
            real_str = "less than a minute"
        skill_emojis = read_json_file('./skill_emojis.json')
        emoji = skill_emojis.get(highest_skill, '')
        message = [
            f' {player_name} has died.',
            f'Survived in-game: {in_game_str}.',
            f'Real-life: {real_str}.',
            f'Zombie Kills: {zombie_kills}.',
            f'Total Skills: {sum_of_perks}.',
            f'Highest Skill: {highest_skill} at {skill_level}.',
        ] # String is formatted all the way to the left, leave it there!
        # await pz_rcon_agent.say_to_pz_server(' '.join(message))
        message[0] = '💀 '+message[0]
        message[5] = emoji+' '+message[5]
        if death_channel:
            await death_channel.send(f'```{"\n".join(message)}```')
# end poll_players

# async def check_perk_logs(): 
#     new_perk_log = pz_perk_log_agent.get_new_log().copy()
#     for entry in new_perk_log:
#         if new_perk_log[entry]['type'] == 'unhandled': # Do not care for these anymore
#             pz_perk_log_agent.update_new_perk_log(new_perk_log[entry]['timestamp'])
#             continue
#         if new_perk_log[entry]['type'] == 'skills': # Do not care for these anymore
#             pz_perk_log_agent.update_new_perk_log(new_perk_log[entry]['timestamp'])
#         elif new_perk_log[entry]['type'] == 'login': # Do not care for these anymore
#             pz_perk_log_agent.update_new_perk_log(new_perk_log[entry]['timestamp'])
#         elif new_perk_log[entry]['type'] == 'creation': # Do not care for these anymore
#             pz_perk_log_agent.update_new_perk_log(new_perk_log[entry]['timestamp'])
#         elif new_perk_log[entry]['type'] == 'died': # IMPORTANT!
#             # In-game time
#             player = player_data_agent.get_player_data()[new_perk_log[entry]['username']]
#             in_game_days = int(player['hours_survived'] // (24))
#             in_game_hours = int(player['hours_survived'])
#             in_game_minutes = int(player['hours_survived'] * 60)
#             if player['hours_survived'] >= 1:
#                 in_game_str = f"{in_game_days} days {in_game_hours} hours {in_game_minutes} minutes" if in_game_days > 0 else f"{in_game_hours} hours {in_game_minutes} minutes"
#             else:
#                 in_game_str = "less than 1 hour"
#             # Real-life time # 1 Full In-Game Day is 1 IRL Hour
#             in_game_hours = player['hours_survived']
#             real_days = int(in_game_hours // 24*24) # 24 Hours is 576 Zomboid Hours
#             real_hours = int(in_game_hours // 24) # 1 Hour is 24 Zomboid Hours
#             real_mins = int(in_game_hours // (24/60)) # 1/60 Hours is 0.4 Zomboid Hours
#             if real_mins >= 1:
#                 real_str = f"{real_days} days {real_hours} hours {real_mins} minutes" if real_days > 0 else f"{real_hours} hours {real_mins} minutes"
#             else:
#                 real_str = "less than a minute"
#             msg = f"""
#             ```💀 {new_perk_log[entry]['username']} has died.
#             Survived in-game: {in_game_str}
#             Real-life: {real_str}```
#             """
#             if death_channel:
#                 await death_channel.send(msg)
#             pz_perk_log_agent.update_new_perk_log(new_perk_log[entry]['timestamp'])
#         elif new_perk_log[entry]['type'] == 'levelUp': # WIP
#             # if int(player_data[entry['username']]['skills'][entry['skill']]) < int(entry['level']): # Level Up
#             #     player_data[entry['username']]['skills'][entry['skill']] = entry['level']
#             #     msg = f"```🎉 {entry['username']} has leveled up their {entry['skill']} to {entry['level']}! {SKILL_EMOJIS.get(entry['skill'], "")}```"
#             #     channel = bot.get_channel(settings_discord[target_bot]['LEVELUP_CHANNEL_ID'])
#             #     if channel:
#             #         await channel.send(msg)
#             # else:
#             #     player_data[entry['username']]['skills'][entry['skill']] = entry['level']
#             pz_perk_log_agent.update_new_perk_log(new_perk_log[entry]['timestamp'])
# # end check_perk_logs

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
# end update_status

# --------------------
# SAVE LOOP
# --------------------
@tasks.loop(seconds=settings_connection['POLLING_RATE'])
async def periodic_save():
    await poll_players()
    await update_status()
    # await check_perk_logs()
# end periodic_save

# --------------------
# BOT READY
# --------------------
@bot.event
async def on_ready():
    global bot, tree
    LOGGER.info(f"{bot.user} has connected to Discord!")
    periodic_save.start()
    LOGGER.info("Successfully finished startup")
# end on_ready

# --------------------
# COMMANDS (Slash)
# --------------------
@tree.command(name="online", description="Show currently online players.")
async def online_slash(interaction: discord.Interaction):
    global pz_rcon_agent, player_data_agent
    await interaction.response.defer(thinking=True)

    if not pz_rcon_agent.get_online_players():
        await interaction.response.send_message("```🟢 - No players are currently online.```")
        # await interaction.followup.send("```🟢 - No players are currently online.```")
        return
    lines = []
    for player in sorted(pz_rcon_agent.get_online_players()):
        if player in player_data_agent.get_player_data():
            duration = time.time() - player_data_agent.get_player_data()[player]['lastLogin'] #player_sessions.get(player, now)
            h, m, s = int(duration//3600), int((duration%3600)//60), int((duration%(60*60)%60))
            lines.append(f"- {player.capitalize()} ({h}h {m}m {s}s)")
    # await interaction.response.send_message(f"```🟢 - Players Online (Session Time):\n" + "\n".join(lines) + f"\n\nTotal: {len(pz_rcon_agent.get_online_players())}```")
    await interaction.followup.send(f"```🟢 - Players Online (Session Time):\n" + "\n".join(lines) + f"\n\nTotal: {len(pz_rcon_agent.get_online_players())}```")
# end online_slash

@tree.command(name="time", description="Show total playtime for a player.")
@app_commands.describe(target="Player name or 'all'")
async def time_slash(interaction: discord.Interaction, target: str):
    global pz_rcon_agent, player_data_agent
    await interaction.response.defer(thinking=True)

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
        # await interaction.response.send_message("```🕒 - Top 10 Players by Total Playtime:\n" + "\n".join((lines)) + "```")
        await interaction.followup.send("```🕒 - Top 10 Players by Total Playtime:\n" + "\n".join((lines)) + "```")
    elif target.lower() in player_data_agent.get_player_data(): # A Singlar Player
        player_data = player_data_agent.get_player_data()[target.lower()]
        h, m, s = 0, 0, 0
        if target.lower() in pz_rcon_agent.get_online_players():
            player_time = player_data['totalPlayTime']+(time.time()-player_data['lastPoll'])
            h, m, s = int(player_time//3600), int((player_time%3600)//60), int((player_time%3600)%60)
        else:
            h, m, s = int(player_data['totalPlayTime']//3600), int((player_data['totalPlayTime']%3600)//60), int((player_data['totalPlayTime']%3600)%60)
        status = "🟢" if target.lower() in pz_rcon_agent.get_online_players() else "🔴"
        # await interaction.response.send_message(f"```{status} - {target.capitalize()} has played for {h}h {m}m {s}s in total.```")
        await interaction.followup.send(f"```{status} - {target.capitalize()} has played for {h}h {m}m {s}s in total.```")
    else:
        # await interaction.response.send_message(f'```Could not find a player named {target}.```')
        await interaction.followup.send(f'```Could not find a player named {target}.```')
# end time_slash

@tree.command(name="survived", description="Shows the total time a player's current character has survived for in in-game hours.")
@app_commands.describe(target="Player name or 'all'")
async def survived_slash(interaction: discord.Interaction, target: str):
    global pz_rcon_agent, player_data_agent
    await interaction.response.defer(thinking=True)

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
        # await interaction.response.send_message("```🕒 - Top 10 Current Character by In-Game Survival Hours:\n" + "\n".join((lines)) + "```")
        await interaction.followup.send("```🕒 - Top 10 Current Character by In-Game Survival Hours:\n" + "\n".join((lines)) + "```")
    elif target.lower() in player_data_agent.get_player_data(): # A Singlar Player
        player_data = player_data_agent.get_player_data()[target.lower()]
        days = int(player_data['hours_survived']//24)
        hours = int(player_data['hours_survived']%24)
        status = "🟢" if target.lower() in pz_rcon_agent.get_online_players() else "🔴"
        # await interaction.response.send_message(f"```{status} - {target.capitalize()} has survived for {days} days and {hours} hours in-game.```")
        await interaction.followup.send(f"```{status} - {target.capitalize()} has survived for {days} days and {hours} hours in-game.```")
    else:
        # await interaction.response.send_message(f'```Could not find a player named {target}.```')
        await interaction.followup.send(f'```Could not find a player named {target}.```')
# end survived_slash

@tree.command(name="zombies", description="Shows a player's total zombie kills.")
@app_commands.describe(target="Player name or 'all'")
async def zombies_slash(interaction: discord.Interaction, target: str):
    global pz_rcon_agent, player_data_agent
    await interaction.response.defer(thinking=True)

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
        # await interaction.response.send_message("```🕒 - Top 10 Current Character by Zombie Kills:\n" + "\n".join((lines)) + "```")
        await interaction.followup.send("```🕒 - Top 10 Current Character by Zombie Kills:\n" + "\n".join((lines)) + "```")
    elif target.lower() in player_data_agent.get_player_data(): # A Singlar Player
        player_data = player_data_agent.get_player_data()[target.lower()]
        zombies = player_data['zombie_kills']
        status = "🟢" if target.lower() in pz_rcon_agent.get_online_players() else "🔴"
        # await interaction.response.send_message(f"```{status} - {target.capitalize()} has killed {zombies} zombies.```")
        await interaction.followup.send(f"```{status} - {target.capitalize()} has killed {zombies} zombies.```")
    else:
        # await interaction.response.send_message(f'```Could not find a player named {target}.```')
        await interaction.followup.send(f'```Could not find a player named {target}.```')
# end zombies_slash

# ------------------- #
#    Slash Command    #
#   Below Suspended!  #
# ------------------- #
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
# # end survivors_slash

@tree.command(name="skill", description="Show a player's skills or leaderboard for a skill")
@app_commands.describe(target="Skill name, player name, 'total' or 'all'.")
async def skill_slash(interaction: discord.Interaction, target:str): #target2:str=None
    global pz_rcon_agent, player_data_agent
    target_lower = target.lower()
    skill_emojis = read_json_file('./skill_emojis.json')
    # if target2 != None:
    #     target_lower = (target+' '+target2).lower()
    # target_lower = target.lower()
    await interaction.response.defer(thinking=True)
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
            # await interaction.response.send_message("```📊 - No skill data yet.```")
            await interaction.followup.send("```📊 - No skill data yet.```")
            return

        lines = []
        for p, total in top:
            display_name_cap = p.capitalize()
            status = "🟢" if p in [pl.lower() for pl in pz_rcon_agent.get_online_players()] else "🔴"
            lines.append(f"{status} - {display_name_cap}: {total}")

        # await interaction.response.send_message(f"```📊 - Top 10 Players by Total Skills:\n" + "\n".join(lines) + "```")
        await interaction.followup.send(f"```📊 - Top 10 Players by Total Skills:\n" + "\n".join(lines) + "```")
        return  # <<< THIS RETURN IS CRUCIAL

    # ----------------------
    # SKILL-SPECIFIC LEADERBOARD
    # ----------------------
    skill_key = read_json_file('./skill_aliases.json').get(target_lower, target.title())
    if skill_key in skill_emojis:
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
        emoji = skill_emojis.get(skill_key, '')
        lines = []
        for p, lvl in top:
            status = "🟢" if p in [pl.lower() for pl in pz_rcon_agent.get_online_players()] else "🔴"
            lines.append(f"{status} - {p}: {lvl}")

        # await interaction.response.send_message(
        #     f"```{emoji} - Top 10 Players by {SKILL_DISPLAY.get(skill_key, skill_key)}:\n" + "\n".join(lines) + "```"
        # )
        await interaction.followup.send(f"```{emoji} - Top 10 Players by {SKILL_DISPLAY.get(skill_key, skill_key)}:\n" + "\n".join(lines) + "```")
        return

    # OTHERWISE TREAT AS PLAYER NAME
    player_key = target_lower
    if player_key not in player_data_agent.get_player_data():
        # await interaction.response.send_message(f"```Could not find player or skill with name {player_key}```")
        await interaction.followup.send(f"```Could not find player or skill with name {player_key}```")
        return
        # player_skills[player_key] = DEFAULT_SKILLS.copy()

    # skills = player_skills[player_key]
    skills = player_data_agent.get_player_data()[player_key]['perks']
    display_name = target.capitalize()
    status = "🟢 Online" if player_key in [pl.lower() for pl in online_players] else "🔴 Offline"

    # Sort skills by highest first
    # sorted_skills_by_name = sorted(skills.items(), key=lambda x: x[0], reverse=False)
    # print(sorted_skills_by_name)
    sorted_skills = sorted(skills.items(), key=lambda x: x[1], reverse=True)

    lines = []
    for skill_name, lvl in sorted_skills:
        if lvl == 0:
            continue  # optional: skip 0-level skills
        emoji = skill_emojis.get(skill_name, '')
        display_name_skill = SKILL_DISPLAY.get(skill_name, skill_name)
        lines.append(f"{emoji} {display_name_skill}: {lvl}")

    # await interaction.response.send_message(f"```{status} - {display_name}'s Skills\n" + "\n".join(lines) + "```")
    await interaction.followup.send(f"```{status} - {display_name}'s Skills\n" + "\n".join(lines) + "```")

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

# Code for sync command retrieved from https://about.abstractumbra.dev/discord.py/2023/01/29/sync-command-example.html
@bot.command()
@commands.guild_only()
@commands.has_any_role("Mods", "Bot")# Only usable by moderators
async def sync(ctx: commands.Context, guilds: commands.Greedy[discord.Object], spec: Optional[Literal["~", "*", "^"]] = None) -> None:
    await ctx.defer(ephemeral=True)
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
            f"```Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}```"
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
    await ctx.send(f"```Synced the tree to {ret}/{len(guilds)}.```")
    LOGGER.info(f"Synced the tree to {ret}/{len(guilds)}.")
# end sync

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
        "• `/commands` — Show this list.",
        ephemeral=True
    )
# end commands_slash


# --------------------
# START BOT
# --------------------
if __name__ == '__main__': # This prevents the bot being ran multiple times in different threads, just a safety precaution
    bot.run(settings_discord[target_bot]['botToken'], root_logger=True)

