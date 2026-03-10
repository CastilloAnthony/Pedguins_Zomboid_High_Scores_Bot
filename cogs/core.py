from typing import Literal, Optional
import discord
from discord.ext import commands#, tasks
from discord import app_commands 
# import time
import logging
LOGGER: logging.Logger = logging.getLogger("bot")

# from class_bot import Discord_Bot
# import class_bot

from player_data_functions import read_json_file
from agents.pz_rcon import Agent_PZ_RCON
from agents.player_data import Agent_Player_Data

class Core_Commands(discord.ext.commands.Cog):
    def __init__(self, bot:discord.commands.Bot):
        self.__bot = bot
    # end __init__

    # Code for sync command retrieved from https://about.abstractumbra.dev/discord.py/2023/01/29/sync-command-example.html
    @app_commands.command(name="sync", description="Administrators only; Manually syncs all commands.")
    @app_commands.describe(spec="[~, *, ^]: ~ Syncs all guild commands for the current guild, * syncs all global commands to the current guild, ^ removes all commands from the current guild.")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def sync_slash(self, interaction: discord.Interaction, spec: Optional[Literal["~", "*", "^"]] = None) -> None:
        await interaction.response.defer(thinking=True, ephemeral=True)
        LOGGER.info(f'Attempting to sync commands... Please wait...')
        if spec == "~":
            synced = await self.__bot.tree.sync(guild=interaction.guild)
        elif spec == "*":
            self.__bot.tree.copy_global_to(guild=interaction.guild)
            synced = await self.__bot.tree.sync(guild=interaction.guild)
        elif spec == "^":
            await interaction.followup.send(f'This parameter has been omitted')
            return
            # self.tree.clear_commands(guild=interaction.guild)
            # await self.tree.sync(guild=interaction.guild)
            # synced = []
        else:
            synced = await self.__bot.tree.sync()
        await interaction.followup.send(f"```Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}```", ephemeral=True)
        LOGGER.info(f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}")
    # end sync

    @app_commands.command(name="reload", description="Administrators only; Manually reloads a cog.")
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(cog="core or pz_stats")
    async def reload_slash(self, interaction: discord.Interaction, cog:str) -> None:
        await interaction.response.defer(thinking=True, ephemeral=True)
        LOGGER.info(f'Cog reload attempt by {interaction.user.name} with user id {interaction.user.id} and target "{cog}"')
        if await self.__bot.reload_cog(cog):
            await interaction.followup.send(f'Cog "{cog}" was reloaded')
        else:
            extensions = []
            for extension in self.__bot.get_extensions().keys():
                if 'cogs.' in extension:
                    extensions.append(extension[5:]) # Remove 'cogs.' from the name of the extension
                else:
                    extensions.append(extension)
            await interaction.followup.send(f'Cog "{cog}" could not be reloaded. List of extensions: {', '.join(extensions)}')
    # end close_slash

    @app_commands.command(name="close", description="Administrators only; Manually stops the bot.")
    @app_commands.default_permissions(administrator=True)
    @app_commands.checks.has_permissions(administrator=True)
    async def close_slash(self, interaction: discord.Interaction,) -> None:
        await interaction.response.defer(thinking=True, ephemeral=True)
        await interaction.followup.send(f'Closing bot...')
        LOGGER.info(f'Bot was closed by {interaction.user.name} with user id {interaction.user.id}')
        await self.__bot.stop_bot()
    # end close_slash

    # WIP: Function produces errors when attempting to restart the bot
    # @app_commands.command(name="restart", description="Administrators only; Manually restarts the bot.")
    # @app_commands.default_permissions(administrator=True)
    # @app_commands.checks.has_permissions(administrator=True)
    # async def restart_slash(self, interaction: discord.Interaction,) -> None:
    #     await interaction.response.defer(thinking=True, ephemeral=True)
    #     await interaction.followup.send(f'Restarting the bot...')
    #     LOGGER.info(f'Bot was restarted by {interaction.user.name} with user id {interaction.user.id}')
    #     await self.__bot.restart_bot()
    # # end close_slash
# end Core_Commands

async def setup(bot:commands.Bot):
    await bot.add_cog(Core_Commands(bot))