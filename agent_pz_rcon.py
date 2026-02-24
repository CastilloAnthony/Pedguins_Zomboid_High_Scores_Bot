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
    # end __init__

    def poll_pz_server(self) -> None:
        """Polls PZ server for a list of currently online players
        """
        response = None
        try:
            with MCRcon(self.__settings['RCON_HOST'], self.__settings['RCON_PASSWORD'], port=self.__settings['RCON_PORT']) as rcon:
                if not self.__server_status:
                    self.__server_status = True
                response = rcon.command("players").splitlines()# or rcon.command("who").splitlines()
        except Exception:
            if self.__server_status:
                self.__server_status = True
            error = traceback.format_exc()
            lines = error.split('\n')
            LOGGER.info('Can\'t reach Project Zomboid Server: '+str(lines[-2]))
            return
        for player in response[1:]:
            self.__online_players.add(player[1:])
    # end poll_pz_server

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