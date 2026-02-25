# This file developed by Anthony Castillo (ComradeWolf)
import traceback
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
        self.__server_status = False
        # await self.poll_pz_server()
    # end __init__

    async def poll_pz_server(self) -> None:
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

    def get_online_players(self) -> set:
        return self.__online_players
    # end get_online_players

    def get_server_status(self) -> bool:
        return self.__server_status
    # end get_server_status
# end PZRcon_agent

if __name__ == '__main__': # For testing purposes
    newAgent = Agent_PZ_RCON()
    newAgent.poll_pz_server()
    print(newAgent.get_server_status())
    print(newAgent.get_online_players())