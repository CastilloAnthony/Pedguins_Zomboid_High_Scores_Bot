# This file developed by Anthony Castillo (ComradeWolf)
import traceback
import time
from mcrcon import MCRcon
import logging
LOGGER: logging.Logger = logging.getLogger("bot")

from read_connection_settings import read_connection_settings

class Agent_PZ_RCON():
    """Retrives and maintains a list of currently online players and the server status
    """
    def __init__(self):
        """Imports connection settings from settings_connections.json
        """
        self.__settings = read_connection_settings()
        self.__online_players = set()
        self.__running = True
        self.__server_status = False
        self.__online_players_msgs = []
        self.__first_check = False
        # await self.poll_pz_server()
    # end __init__

    def poll_pz_server(self) -> None:
        """Polls PZ server for a list of currently online players
        """
        try:
            with MCRcon(self.__settings['RCON_HOST'], self.__settings['RCON_PASSWORD'], port=self.__settings['RCON_PORT']) as rcon:
                if not self.__server_status:
                    self.__server_status = True
                response = rcon.command("players").splitlines() or rcon.command("who").splitlines() # Linux servers use the who command
                if len(response) > 0: # If len(response) is 0 then there was an issue getting a response from the PZ server and we therefore do not want to update online_players
                    new_list = set()
                    for player in response[1:]:
                        new_list.add(player[1:].lower())
                    if new_list != self.__online_players:
                        self.__online_players = new_list
                        # self.generate_player_connection_msgs(new_list)
                    if not self.__first_check:
                        self.__first_check = True
        except Exception:
            if self.__server_status:
                self.__server_status = False
            self.__online_players = set()
            error = traceback.format_exc()
            lines = error.split('\n')
            print(error)
            LOGGER.error('Can\'t reach Project Zomboid Server: '+str(lines[-1]))
            LOGGER.error('Error in agent_pz_rcon.py function poll_pz_server')
            return
    # end poll_pz_server

    async def say_to_pz_server(self, message:str) -> None:
        # print(message)
        try:
            with MCRcon(self.__settings['RCON_HOST'], self.__settings['RCON_PASSWORD'], port=self.__settings['RCON_PORT']) as rcon:
                if not self.__server_status:
                    self.__server_status = True
                response = rcon.command(f'servermsg "{message}"').splitlines()
                print(response)
        except:
            if self.__server_status:
                self.__server_status = False
            error = traceback.format_exc()
            lines = error.split('\n')
            print(error)
            LOGGER.error('Can\'t reach Project Zomboid Server: '+str(lines[-1]))
            LOGGER.error('Error in agent_pz_rcon.py function say_to_pz_server')
            return
    # end say_to_pz_server

    # def generate_player_connection_msgs(self, new_players:list) -> None:       
    #     # await pz_rcon_agent.poll_pz_server()
    #     # await update_status()
    #     # await player_data_agent.poll_player_data()
    #     # await pz_perk_log_agent.poll_perk_log()
    #     current_players = .get_online_players()

    #     # --- Handle joins ---
    #     for player in self.__online_players - new_players:
    #         if self.__curr_activity != '':
    #             if player in player_data_agent.get_player_data():
    #                 player_data_agent.update_player_last_login(player, time.time())
    #                 await channel.send(f"```🟢 - {player.capitalize()} has joined the server!```")

    #     # --- Handle leaves ---
    #     for player in online_players - current_players:
    #         duration = time.time() - player_data_agent.get_player_data()[player]['lastLogin']
    #         h, m, s = int(duration//3600), int((duration%3600)//60), int((duration%3600)%60)
    #         if channel:
    #             await channel.send(f"```🔴 - {player.capitalize()} has left the server.\nSession: {h}h {m}m {s}s```")

    #     # --- Increment survival and total time for current online players ---
    #     for player in current_players & online_players:
    #         if player in player_data_agent.get_player_data():
    #             player_data_agent.update_player_total_play_time(player)

    #     online_players.clear()
    #     online_players.update(current_players)
    # # end generate_player_connection_msgs

    def get_online_players(self) -> set:
        return self.__online_players
    # end get_online_players

    def get_server_status(self) -> bool:
        return self.__server_status
    # end get_server_status

    def get_online_players_msgs(self) -> list[str]:
        return self.__online_players_msgs 
    # end get_online_players_msgs

    def get_curr_activity(self) -> str:
        return self.__curr_activity
    # end get_curr_activity

    def get_first_check(self) -> bool:
        return self.__first_check
    # end get_first_check

    def toggle_running(self) -> None:
        if self.__running:
            self.__running = False
        else:
            self.__running = True
    # end toggle_running

    def run_agent(self) -> None:
        last_poll = 0 # We want this to retrieve player count immediately
        while self.__running:
            if time.time() - last_poll > self.__settings['POLLING_RATE']:
                self.poll_pz_server()
                last_poll = time.time()
        # end while
    # end run_agent
# end PZRcon_agent

if __name__ == '__main__': # For testing purposes
    newAgent = Agent_PZ_RCON()
    newAgent.run_agent()
    # newAgent.poll_pz_server()
    # print(newAgent.get_server_status())
    # print(newAgent.get_online_players())