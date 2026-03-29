# This file developed by Peter Mann (Pedguin) and includes modifications made by Anthony Castillo (ComradeWolf)
# Last Update: 2026-24-02
# Code for sync command retrieved from https://about.abstractumbra.dev/discord.py/2023/01/29/sync-command-example.html

# Native Modules
import time
from typing import Literal, Optional
import logging
from threading import Thread
import asyncio
import traceback

# Publicly Available Modules
import discord
from discord.ext import commands, tasks
# from discord import app_commands 

# Custom Modules
from shared_functions.read_discord_settings import read_discord_settings
# from shared_functions.read_connection_settings import read_connection_settings
from agents.player_data import Agent_Player_Data
# from agent_perk_log import Agent_Perk_Log
from agents.pz_rcon import Agent_PZ_RCON
# from player_data_functions import read_json_file
# from cogs.core import Core_Commands
# from cogs.pz_stats import Project_Zomboid_Commands

# Variable Initializations
LOGGER: logging.Logger = logging.getLogger("bot")
logging.getLogger('paramiko').setLevel(logging.WARNING) # Surpresses logging info messages about connecting and closing SFTP

class Discord_Bot(commands.Bot):
    def __init__(self):
        self.__intents = discord.Intents.default()
        self.__intents.message_content = True
        super().__init__(command_prefix='!', intents=self.__intents)
        self.__settings_discord = read_discord_settings()
        # self.__settings_connection = read_connection_settings()
        self.__target_bot = 'pedguinBot'
        self.__curr_activity = ''
        self.__server_online = False
        self.__threads = []
        self.__pz_rcon_agent = Agent_PZ_RCON()
        self.__player_data_agent = Agent_Player_Data()
        self.__online_players = set()
    # end __init__

    async def announce_server_status(self, online: bool = False):
        channel = self.get_channel(self.__settings_discord[self.__target_bot]['ANNOUNCE_CHANNEL_ID'])
        if not channel or not isinstance(channel, discord.abc.Messageable):
            return
        msg = "🟢 - Project Zomboid server is now ONLINE" if online else "🔴 - Project Zomboid server is OFFLINE"
        await channel.send(f"# {msg}")
    # end announce_server_status

    async def update_status(self):
        # global pz_rcon_agent, curr_activity #, online_players, server_online
        try:
            if self.__pz_rcon_agent.get_first_check():
                if self.__pz_rcon_agent.get_server_status():
                    activity_name = ""
                    if len(self.__pz_rcon_agent.get_online_players())==0:
                        activity_name = "🟢 Server Online"
                    else:
                        activity_name = f"🟢 {len(self.__pz_rcon_agent.get_online_players())} Survivors Online"
                    if 'Online' not in self.__curr_activity:
                        await self.announce_server_status(True)
                    if self.__curr_activity != activity_name:
                        await self.change_presence(status=discord.Status.online, activity=discord.Game(name=activity_name))
                        self.__curr_activity = activity_name
                        LOGGER.info(f'Changed discord status to {activity_name}')
                else:
                    activity_name = "🔴 Server Offline"
                    if activity_name != self.__curr_activity:
                        await self.change_presence(status=discord.Status.dnd, activity=discord.Game(name=activity_name))
                        self.__curr_activity = activity_name
                        LOGGER.info(f'Changed discord status to 🔴 Server Offline')
                        await self.announce_server_status(False)
            else:
                activity_name = "🔴 Server Offline"
                if activity_name != self.__curr_activity:
                    await self.change_presence(status=discord.Status.dnd, activity=discord.Game(name=activity_name))
                    self.__curr_activity = activity_name
                    LOGGER.info(f'Changed discord status to 🔴 Server Offline')
                    await self.announce_server_status(False)
        except Exception:
            LOGGER.error(f'There was an error in updating the bot\'s status: check the update_status funciton in the Discord_Bot class')
            LOGGER.error(f'Variable server_online is in state {self.__server_online} and curr_activity is set to {self.__curr_activity}')
    # end update_status

    async def check_level_ups(self):
        messages = self.__player_data_agent.get_level_ups_msgs()
        if len(messages) > 0:
            channel = self.get_channel(self.__settings_discord[self.__target_bot]['LEVELUP_CHANNEL_ID'])
            for msg in messages:
                if channel and isinstance(channel, discord.abc.Messageable):
                    await channel.send(msg)
    # end check_level_ups

    async def check_deaths(self):
        messages = self.__player_data_agent.get_deaths_msgs()
        if len(messages) > 0:
            death_channel = self.get_channel(self.__settings_discord[self.__target_bot]['ANNOUNCE_CHANNEL_ID'])
            for message in messages:
                if death_channel and isinstance(death_channel, discord.abc.Messageable):
                    await death_channel.send(message)
    # end check_deaths

    async def on_ready(self):
        LOGGER.info(f"{self.user} has connected to Discord!")
        self.poll_players.start()
        self.add_command(sync)
        LOGGER.info("Successfully finished startup")
    # end on_ready

    @tasks.loop(seconds=10)#self.__settings_connection['POLLING_RATE'])
    async def poll_players(self):
        channel = self.get_channel(self.__settings_discord[self.__target_bot]['ANNOUNCE_CHANNEL_ID'])
        
        if self.__pz_rcon_agent.get_first_check():
            current_players = self.__pz_rcon_agent.get_online_players()

            # --- Handle joins ---
            for player in current_players - self.__online_players:
                if channel and self.__curr_activity != '' and isinstance(channel, discord.abc.Messageable):
                    if player in self.__player_data_agent.get_player_data():
                        self.__player_data_agent.update_player_last_login(player, time.time())
                        await channel.send(f"```🟢 - {player} has joined the server!```")

            # --- Handle leaves ---
            for player in self.__online_players - current_players:
                duration = time.time() - self.__player_data_agent.get_player_data()[player]['lastLogin']
                h, m, s = int(duration//3600), int((duration%3600)//60), int((duration%3600)%60)
                if channel and isinstance(channel, discord.abc.Messageable):
                    await channel.send(f"```🔴 - {player} has left the server.\nSession: {h}h {m}m {s}s```")

            # --- Increment survival and total time for current online players ---
            for player in current_players & self.__online_players:
                if player in self.__player_data_agent.get_player_data():
                    self.__player_data_agent.update_player_total_play_time(player)

            self.__online_players.clear()
            self.__online_players.update(current_players)
            await self.check_level_ups()
            await self.check_deaths()
        await self.update_status()
    # end poll_players

    async def reload_cog(self, cog:str):
        try:
            await self.reload_extension(name='cogs.'+cog)
            LOGGER.info(f'The cog "{cog}" has been reloaded.')
            return True
        except Exception:
            error = traceback.format_exc()
            lines = error.split('\n')
            print(error)
            # LOGGER.error('Can\'t reach Bisect Hosting: '+str(lines[-1]))
            LOGGER.error(f'Could not reload "{cog}": '+str(lines[-1]))
            LOGGER.error('Error in class_bot function reload_cog')
            return False
    # end reload_module

    def get_player_data_agent(self):
        return self.__player_data_agent
    # end get_player_data_agent

    def get_pz_rcon_agent(self):
        return self.__pz_rcon_agent
    # end get_pz_rcon_agent

    def get_extensions(self):
        return self.extensions
    # end get_extensions

    # WIP: Produces errors when attempting to start the bot
    # async def restart_bot(self):
    #     await self.stop_bot()
    #     self.start_bot()
    # # end reload

    async def stop_bot(self):
        self.__player_data_agent.toggle_running()
        self.__pz_rcon_agent.toggle_running()
        for thread in self.__threads:
            LOGGER.info(f'Attempting to join thread {thread.getName()}.')
            thread.join()
            LOGGER.info(f'Thread {thread.getName()} has been joined.')
        self.__threads = []
        await self.close()
        LOGGER.info(f'Bot has been stopped.')
    # end stop_bot    

    def start_bot(self):
        # self.add_cog(Core_Commands(self))
        # self.add_cog(Project_Zomboid_Commands(self, self.__pz_rcon_agent, self.__player_data_agent))
        asyncio.run(self.load_extension('cogs.core'))
        asyncio.run(self.load_extension('cogs.pz_stats'))
        self.__threads.append(Thread(target=self.__pz_rcon_agent.run_agent, name="pz_rcon_agent"))
        self.__threads[-1].start()
        self.__threads.append(Thread(target=self.__player_data_agent.run_agent, name="player_data_agent"))
        self.__threads[-1].start()
        self.run(self.__settings_discord[self.__target_bot]['botToken'], root_logger=True)
        LOGGER.info(f'Bot has been closed')
        # asyncio.run(self.start(self.__settings_discord[self.__target_bot]['botToken']))
    # end start_bot
# end Discord_Bot

@commands.command()
@commands.guild_only()
@commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True))
async def sync(ctx: commands.Context, guilds: commands.Greedy[discord.Object], spec: Optional[Literal["~", "*", "^"]] = None) -> None:
    LOGGER.info(f'Attempting to sync commands... Please wait...')
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
# end sync