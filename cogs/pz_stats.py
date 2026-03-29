import discord
# from discord.ext import commands, tasks
from discord import app_commands
from discord.ext import commands
import time
import logging
LOGGER: logging.Logger = logging.getLogger("bot")
import difflib
from datetime import datetime
# from class_bot import Discord_Bot
# import class_bot

from shared_functions.player_data_functions import read_json_file, get_default_skills
from agents.pz_rcon import Agent_PZ_RCON
from agents.player_data import Agent_Player_Data
from classes.bot import Discord_Bot

class Project_Zomboid_Commands(commands.Cog):
    def __init__(self, bot:Discord_Bot, pz_rcon_agent:Agent_PZ_RCON, player_data_agent:Agent_Player_Data):
        self.__bot = bot
        self.__pz_rcon_agent = pz_rcon_agent
        self.__player_data_agent = player_data_agent
    # end __init__

    @app_commands.command(name="online", description="Show currently online players.")
    async def online_slash(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        if not self.__pz_rcon_agent.get_online_players():
            await interaction.followup.send("```🟢 - No players are currently online.```")
            return
        lines = []
        for player in sorted(self.__pz_rcon_agent.get_online_players()):
            if player in self.__player_data_agent.get_player_data():
                duration = time.time() - self.__player_data_agent.get_player_data()[player]['lastLogin'] #player_sessions.get(player, now)
                h, m, s = int(duration//3600), int((duration%3600)//60), int((duration%(60*60)%60))
                lines.append(f"- {player} ({h}h {m}m {s}s)")
        await interaction.followup.send(f"```🟢 - Players Online (Session Time):\n" + "\n".join(lines) + f"\n\nTotal: {len(self.__pz_rcon_agent.get_online_players())}```")
    # end online_slash

    @app_commands.command(name="playtime", description="Show total playtime for a player.")
    @app_commands.describe(target="Player name or 'all'")
    async def playtime_slash(self, interaction: discord.Interaction, target: str = "all"):
        await interaction.response.defer(thinking=True)
        if target == "all":
            player_times = []
            all_player_data = self.__player_data_agent.get_player_data()
            for player in all_player_data:
                if all_player_data[player]['access_level'] != "admin": # Exclude admins from playtime leaderboard
                    if player in self.__pz_rcon_agent.get_online_players():
                        player_times.append((player, all_player_data[player]['totalPlayTime']+(time.time()-all_player_data[player]['lastPoll'])))
                    else:
                        player_times.append((player, all_player_data[player]['totalPlayTime']))
            player_times = sorted(player_times, key=lambda tup: tup[1], reverse=True)
            lines = []
            for p, sec in player_times[:10]: # Top 10 (arrays/lists start at 0 and this syntax goes up to, but does not include the last index)
                h, m, s = int(sec//3600), int((sec%3600)//60), int((sec%3600)%60)
                status = "🟢" if p in self.__pz_rcon_agent.get_online_players() else "🔴"
                lines.append(f"{status} - {p}: {h}h {m}m {s}s")
            await interaction.followup.send("```🕒 - Top 10 Players by Total Playtime:\n" + "\n".join((lines)) + "```")
        # elif target.lower() in self.__player_data_agent.get_player_data(): # A Singlar Player
        #     player_data = self.__player_data_agent.get_player_data()[target.lower()]
        #     h, m, s = 0, 0, 0
        #     if target.lower() in self.__pz_rcon_agent.get_online_players():
        #         player_time = player_data['totalPlayTime']+(time.time()-player_data['lastPoll'])
        #         h, m, s = int(player_time//3600), int((player_time%3600)//60), int((player_time%3600)%60)
        #     else:
        #         h, m, s = int(player_data['totalPlayTime']//3600), int((player_data['totalPlayTime']%3600)//60), int((player_data['totalPlayTime']%3600)%60)
        #     status = "🟢" if target.lower() in self.__pz_rcon_agent.get_online_players() else "🔴"
        #     await interaction.followup.send(f"```{status} - {target.capitalize()} has played for {h}h {m}m {s}s in total.```")
        elif len(difflib.get_close_matches(target, self.__player_data_agent.get_player_data().keys())) > 0: # Get closest match
            matches = difflib.get_close_matches(target, self.__player_data_agent.get_player_data().keys())
            player_data = self.__player_data_agent.get_player_data()[matches[0]]
            h, m, s = 0, 0, 0
            if target in self.__pz_rcon_agent.get_online_players():
                player_time = player_data['totalPlayTime']+(time.time()-player_data['lastPoll'])
                h, m, s = int(player_time//3600), int((player_time%3600)//60), int((player_time%3600)%60)
            else:
                h, m, s = int(player_data['totalPlayTime']//3600), int((player_data['totalPlayTime']%3600)//60), int((player_data['totalPlayTime']%3600)%60)
            status = "🟢" if matches[0] in self.__pz_rcon_agent.get_online_players() else "🔴"
            await interaction.followup.send(f"```{status} - {matches[0]} has played for {h}h {m}m {s}s in total.```")
        else:
            await interaction.followup.send(f'```Could not find a player named {target}.```')
    # end playtime_slash

    @app_commands.command(name="survived", description="Shows the total time a player's current character has survived for in in-game hours.")
    @app_commands.describe(target="Player name or 'all'")
    async def survived_slash(self, interaction: discord.Interaction, target: str = "all"):
        await interaction.response.defer(thinking=True)
        if target == "all":
            player_times = []
            all_player_data = self.__player_data_agent.get_player_data()
            for player in all_player_data:
                if all_player_data[player]['access_level'] != "admin": # Exclude admins from survival time leaderboard
                    player_times.append((all_player_data[player]['username'], all_player_data[player]['hours_survived']%24, all_player_data[player]['hours_survived']//24, all_player_data[player]['hours_survived']))
            player_times = sorted(player_times, key=lambda tup: tup[3], reverse=True)
            lines = []
            for p, hours, days, _ in player_times[:10]: # Top 10 (arrays/lists start at 0 and this syntax goes up to, but does not include the last index)
                status = "🟢" if p in self.__pz_rcon_agent.get_online_players() else "🔴"
                lines.append(f"{status} - {p}: {int(days)} days {int(hours)} hours")
            await interaction.followup.send("```🕒 - Top 10 Current Character by In-Game Survival Hours:\n" + "\n".join((lines)) + "```")
        # elif target.lower() in self.__player_data_agent.get_player_data(): # A Singlar Player
        #     player_data = self.__player_data_agent.get_player_data()[target.lower()]
        #     days = int(player_data['hours_survived']//24)
        #     hours = int(player_data['hours_survived']%24)
        #     status = "🟢" if target.lower() in self.__pz_rcon_agent.get_online_players() else "🔴"
        #     await interaction.followup.send(f"```{status} - {target.capitalize()} has survived for {days} days and {hours} hours in-game.```")
        elif len(difflib.get_close_matches(target, self.__player_data_agent.get_player_data().keys())) > 0: # Get closest match
            matches = difflib.get_close_matches(target, self.__player_data_agent.get_player_data().keys())
            player_data = self.__player_data_agent.get_player_data()[matches[0]]
            days = int(player_data['hours_survived']//24)
            hours = int(player_data['hours_survived']%24)
            status = "🟢" if matches[0] in self.__pz_rcon_agent.get_online_players() else "🔴"
            await interaction.followup.send(f"```{status} - {matches[0]} has survived for {days} days and {hours} hours in-game.```")
        else:
            await interaction.followup.send(f'```Could not find a player named {target}.```')
    # end survived_slash

    @app_commands.command(name="zombies", description="Shows a player's total zombie kills.")
    @app_commands.describe(target="Player name or 'all'")
    async def zombies_slash(self, interaction: discord.Interaction, target: str = "all"):
        await interaction.response.defer(thinking=True)
        if target == "all":
            total_zombie_kills = 0
            player_zombie_kills = []
            all_player_data = self.__player_data_agent.get_player_data()
            for player_data in all_player_data:
                if all_player_data[player_data]['access_level'] != "admin": # Exclude admins from zombie kill leaderboard
                    player_zombie_kills.append((all_player_data[player_data]['username'], all_player_data[player_data]['zombie_kills']))
                    total_zombie_kills += all_player_data[player_data]['zombie_kills']
            player_zombie_kills = sorted(player_zombie_kills, key=lambda tup: tup[1], reverse=True)
            lines = []
            for p, kills in player_zombie_kills[:10]: # Top 10 (arrays/lists start at 0 and this syntax goes up to, but does not include the last index)
                status = "🟢" if p in self.__pz_rcon_agent.get_online_players() else "🔴"
                lines.append(f"{status} - {p}: {kills} zombies")
            await interaction.followup.send(f"```🕒 - Top 10 Current Character by Zombie Kills (Total: {total_zombie_kills}):\n" + "\n".join((lines)) + "```")
        # elif target.lower() in self.__player_data_agent.get_player_data(): # A Singlar Player
        #     player_data = self.__player_data_agent.get_player_data()[target.lower()]
        #     status = "🟢" if target.lower() in self.__pz_rcon_agent.get_online_players() else "🔴"
        #     await interaction.followup.send(f"```{status} - {target.capitalize()} has killed {player_data['zombie_kills']} zombies.```")
        elif len(difflib.get_close_matches(target, self.__player_data_agent.get_player_data().keys())) > 0: # Get closest match
            matches = difflib.get_close_matches(target, self.__player_data_agent.get_player_data().keys())
            player_data = self.__player_data_agent.get_player_data(matches[0])
            status = "🟢" if matches[0] in self.__pz_rcon_agent.get_online_players() else "🔴"
            await interaction.followup.send(f"```{status} - {matches[0]} has killed {player_data['zombie_kills']} zombies.```")
        else:
            await interaction.followup.send(f'```Could not find a player named {target}.```')
    # end zombies_slash

    # # Command suspended for non-pvp server  
    # @app_commands.command(name="survivors", description="Shows a player's total survivor kills.")
    # @app_commands.describe(target="Player name or 'all'")
    # async def survivors_slash(self, interaction: discord.Interaction, target: str):
    #     await interaction.response.defer(thinking=True)
    #     if target.lower() == "all":
    #         player_times = []
    #         for player in self.__player_data_agent.get_player_data():
    #             player_data = self.__player_data_agent.get_player_data()[player]
    #             player_times.append((player_data['username'], player_data['survivor_kills']))
    #         player_times = sorted(player_times, key=lambda tup: tup[1], reverse=True)
    #         lines = []
    #         for p, kills in player_times[:10]: # Top 10 (arrays/lists start at 0 and this syntax goes up to, but does not include the last index)
    #             status = "🟢" if p in self.__pz_rcon_agent.get_online_players() else "🔴"
    #             lines.append(f"{status} - {p.capitalize()}: {kills} survivors")
    #         await interaction.folloutup.send("```🕒 - Top 10 Current Character by Survivors Kills:\n" + "\n".join((lines)) + "```")
    #     elif target.lower() in self.__player_data_agent.get_player_data(): # A Singlar Player
    #         player_data = self.__player_data_agent.get_player_data()[target.lower()]
    #         survivors = player_data['survivor_kills']
    #         status = "🟢" if target.lower() in self.__pz_rcon_agent.get_online_players() else "🔴"
    #         await interaction.followup.send(f"```{status} - {target.capitalize()} has killed {survivors} survivors.```")
    #     else:
    #         await interaction.followup.send(f'```Could not find a player named {target}.```')
    # # end survivors_slash

    @app_commands.command(name="skill", description="Show a player's skills or leaderboard for a skill")
    @app_commands.describe(target="Skill name, player name, 'total' or 'all'.")
    async def skill_slash(self, interaction: discord.Interaction, target:str = "total"): #target2:str=None
        await interaction.response.defer(thinking=True)
        skill_aliases = read_json_file('./skill_aliases.json')
        skill_emojis = read_json_file('./skill_emojis.json')
        lines = []
        if target == 'all' or target == 'total': # All Players
            combined = []
            all_player_data = self.__player_data_agent.get_player_data()
            for player_data in all_player_data:
                if all_player_data[player_data]['access_level'] != "admin": # Exclude admins from total skill leaderboard
                    combined.append((all_player_data[player_data]['username'], sum(all_player_data[player_data]['perks'].values()),))
            top = sorted(combined, key=lambda x: x[1], reverse=True)[:10]
            for player in top:
                status = "🟢" if target in [pl for pl in self.__pz_rcon_agent.get_online_players()] else "🔴"
                lines.append(f'{status} - {player[0]}: {player[1]}')
            await interaction.followup.send(f"```📊 - Top 10 Players by Total Skills:\n" + "\n".join(lines) + "```")
        # elif target_lower in self.__player_data_agent.get_player_data(): # Player specific
        #     player_data = self.__player_data_agent.get_player_data()[target_lower]
        #     skills = []
        #     for perk in sorted(player_data['perks']):
        #         if player_data['perks'][perk] > 0:
        #             skills.append((perk, player_data['perks'][perk]))
        #     skills = sorted(skills, key=lambda x: x[1], reverse=True)
        #     for tuple in skills:
        #         emoji = skill_emojis.get(tuple[0], '')
        #         lines.append(f'{emoji} {tuple[0]}: {tuple[1]}')
        #     status = "🟢" if target_lower in [pl.lower() for pl in self.__pz_rcon_agent.get_online_players()] else "🔴"
        #     await interaction.followup.send(f"```{status} - {player_data['username']}'s Skills (Total: {sum(tuple[1] for tuple in skills)})\n" + "\n".join(lines) + "```")
        elif target in skill_aliases: # Skill alias specific
            skill_alias = skill_aliases[target]
            emoji = skill_emojis.get(skill_alias, '')
            combined = []
            all_player_data = self.__player_data_agent.get_player_data()
            for player_data in all_player_data:
                combined.append((all_player_data[player_data]['username'], all_player_data[player_data]['perks'][skill_alias],))
            combined = sorted(combined, key=lambda x: x[1], reverse=True)[:10]
            for tuple in combined:
                status = "🟢" if tuple[0] in [player for player in self.__pz_rcon_agent.get_online_players()] else "🔴"
                lines.append(f'{status} - {tuple[0]}: {tuple[1]}')
            await interaction.followup.send(f"```{emoji} - Top 10 Players by {skill_alias}:\n" + "\n".join(lines) + "```")
        # elif target.capitalize() in get_default_skills(): # Skill specific
        #     target_capitalize = target.capitalize()
        #     emoji = skill_emojis.get(target_capitalize, '')
        #     combined = []
        #     all_player_data = self.__player_data_agent.get_player_data()
        #     for player_data in all_player_data:
        #         combined.append((player_data, all_player_data[player_data]['perks'][target_capitalize],))
        #     combined = sorted(combined, key=lambda x: x[1], reverse=True)[:10]
        #     for tuple in combined:
        #         status = "🟢" if tuple[0].lower() in [player.lower() for player in self.__pz_rcon_agent.get_online_players()] else "🔴"
        #         lines.append(f'{status} - {tuple[0]}: {tuple[1]}')
        #     await interaction.followup.send(f"```{emoji} - Top 10 Players by {target_capitalize}:\n" + "\n".join(lines) + "```")
        elif len(difflib.get_close_matches(target, self.__player_data_agent.get_player_data().keys())) > 0: # Get closest match of players
            matches = difflib.get_close_matches(target, self.__player_data_agent.get_player_data().keys())
            player_data = self.__player_data_agent.get_player_data()[matches[0]]
            skills = []
            for perk in sorted(player_data['perks']):
                if player_data['perks'][perk] > 0:
                    skills.append((perk, player_data['perks'][perk]))
            skills = sorted(skills, key=lambda x: x[1], reverse=True)
            for tuple in skills:
                emoji = skill_emojis.get(tuple[0], '')
                lines.append(f'{emoji} {tuple[0]}: {tuple[1]}')
            status = "🟢" if matches[0] in [pl for pl in self.__pz_rcon_agent.get_online_players()] else "🔴"
            await interaction.followup.send(f"```{status} - {player_data['username']}'s Skills (Total: {sum(tuple[1] for tuple in skills)})\n" + "\n".join(lines) + "```")
        elif len(difflib.get_close_matches(target, get_default_skills().keys())) > 0: # Get closest match of skills
            matches = difflib.get_close_matches(target, get_default_skills().keys())
            emoji = skill_emojis.get(matches[0], '')
            combined = []
            all_player_data = self.__player_data_agent.get_player_data()
            for player_data in all_player_data:
                if all_player_data[player_data]['access_level'] != "admin": # Exclude admins from individual skill leaderboards
                    combined.append((player_data, all_player_data[player_data]['perks'][matches[0]],))
            combined = sorted(combined, key=lambda x: x[1], reverse=True)[:10]
            for tuple in combined:
                status = "🟢" if tuple[0] in [player for player in self.__pz_rcon_agent.get_online_players()] else "🔴"
                lines.append(f'{status} - {tuple[0]}: {tuple[1]}')
            await interaction.followup.send(f"```{emoji} - Top 10 Players by {matches[0]}:\n" + "\n".join(lines) + "```")
        else:
            await interaction.followup.send(f"```Could not find player or skill with name {target}```")
    # end skill_slash

    @app_commands.command(name="traits", description="Show a player's traits or a list of players for a trait")
    @app_commands.describe(target="Trait name, player name or 'top'.")
    async def traits_slash(self, interaction: discord.Interaction, target:str = "top"): #target2:str=None
        await interaction.response.defer(thinking=True)
        await interaction.followup.send(f"```This command is currently unavailable.```")
    # end traits_slash

    @app_commands.command(name="world", description="Show world information")
    @app_commands.describe(target="UNDEFINED.")
    async def world_slash(self, interaction: discord.Interaction, target:str = ""): #target2:str=None
        await interaction.response.defer(thinking=True)
        await interaction.followup.send(f"```This command is currently unavailable.```")
    # end traits_slash

    # # Disabled until a discord-to-pz-username connection can be made
    # @app_commands.command(name="map", description="Show a player's last known location on b42map.com")
    # @app_commands.describe(target="A player name.")
    # async def map_slash(self, interaction: discord.Interaction, target:str): #target2:str=None
    #     await interaction.response.defer(thinking=True)
    #     target_lower = target.lower()
    #     if target_lower in self.__player_data_agent.get_player_data():
    #         url = 'https://b42map.com/?'
    #         player_data = self.__player_data_agent.get_player_data()[target_lower]
    #         url += str(round(player_data['coord_x']))+'x'+str(round(player_data['coord_y']))
    #         await interaction.followup.send(f'`{player_data['username']}\'s last known location is `{url}')
    #     else:
    #         await interaction.followup.send(f'```Could not find a player with the name of {target}```')
    # # end map

    # Discord Admin Only Command
    @app_commands.command(name="position", description="Administrators only; Displays a player's map position.")
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(player="Name of a player (i.e., Pedguin)")
    async def position_slash(self, interaction: discord.Interaction, player:str) -> None:
        await interaction.response.defer(thinking=True, ephemeral=True)
        LOGGER.info(f'Position retrieval attempted by {interaction.user.name} with user id {interaction.user.id} and target "{player}"')
        if len(difflib.get_close_matches(player, self.__player_data_agent.get_player_data().keys())) > 0: # Get closest match of players
            players = self.__player_data_agent.get_player_data()
            matches = difflib.get_close_matches(player, players.keys())
            url = 'https://b42map.com/?'+str(round(players[matches[0]]['coords']['x']))+'x'+str(round(players[matches[0]]['coords']['y']))
            await interaction.followup.send(f'```{matches[0]}\'s last known position:``` {url}')
        else:
            await interaction.followup.send(f'```Could not find player named {player}```')
    # end position_slash

    @app_commands.command(name="lastlog", description="Show a player's last login time")
    @app_commands.describe(player="Player name'.")
    async def lastlog_slash(self, interaction: discord.Interaction, player:str): #target2:str=None
        await interaction.response.defer(thinking=True)
        if len(difflib.get_close_matches(player, self.__player_data_agent.get_player_data().keys())) > 0:
            matches = difflib.get_close_matches(player, self.__player_data_agent.get_player_data().keys())
            player_data = self.__player_data_agent.get_player_data()[matches[0]]
            status = "🟢" if matches[0] in [pl for pl in self.__pz_rcon_agent.get_online_players()] else "🔴"
            await interaction.followup.send(f'```{status} - {player_data['username']}\'s last login: {datetime.fromtimestamp(round(player_data['lastLogin'])).strftime("%B %d, %Y %H:%M:%S")}```')
        else:
            await interaction.followup.send(f'```Could not find player named {player}```')
    # end lastlog_slash

    @app_commands.command(name="commands", description="Show all available commands")
    async def commands_slash(self, interaction: discord.Interaction):    
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
            "• `/lastlog player` — Show a player's last log in time.\n"
            "• `/commands` — Show this list.",
            ephemeral=True
        )
    # end commands_slash

    # Discord Admin Only Command
    @app_commands.command(name="admincommands", description="Administrators only; Show all available admin commands")
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def adminCommands_slash(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            "📜 **Available Admin Commands:**\n"
            "• `/position [player]` — Show the current position of a player.\n"
            "• `/sync` — Syncs all discord commands.\n"
            "• `/reload [cog_name]` — Reloads a specific cog (i.e., \"core\" or \"pz_stats\").\n"
            "• `/close` — Manually stops the bot. (WARNING: Avoid using unless owner).\n"
            "• `/adminCommands` — Show this list.",
            ephemeral=True
        )
    # end adminCommands_slash
# end Project_Zomboid_Commands

async def setup(bot:Discord_Bot):
    await bot.add_cog(Project_Zomboid_Commands(bot, bot.get_pz_rcon_agent(), bot.get_player_data_agent()))