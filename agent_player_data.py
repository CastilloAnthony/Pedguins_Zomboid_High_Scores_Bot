# This file developed by Anthony Castillo (ComradeWolf)
import os
from pathlib import Path
import traceback
import paramiko
import logging
LOGGER: logging.Logger = logging.getLogger("bot")

from read_connection_settings import read_connection_settings
from player_data_functions import read_json_file, save_json_file

class Agent_Player_Data():
    """Connects to an sftp server, copies json files from the server to a local dir, iterates over those files to import them to a variable accessible by a function
    """
    def __init__(self) -> None:
        """Imports connection settings from settings_connections.json and creates initial variable for player_data
        """
        self.__settings = read_connection_settings()
        self.__player_data = read_json_file(file_path='./player_data.json') # Reads player_data.json
        self.poll_player_data()
    # end __init__

    def poll_player_data(self) -> bool:
        """Connects to and copies player_data.json files from the sftp server host

        Returns:
            bool: Success or failure
        """
        sftp = None
        try:
            transport = paramiko.Transport((self.__settings['SFTP_HOST'], self.__settings['SFTP_PORT']))
            transport.connect(username=self.__settings['SFTP_USER'], password=self.__settings['SFTP_PASS'])
            sftp = paramiko.SFTPClient.from_transport(transport)
            if not Path(self.__settings['LOCAL_PLAYER_DATA_PATH']).is_dir():
                Path(self.__settings['LOCAL_PLAYER_DATA_PATH']).mkdir()
            filesnames = sftp.listdir(self.__settings['SFTP_PLAYER_DATA_PATH'])
            player_data_files = [f for f in filesnames if f.endswith("_data.json")]
            if player_data_files:
                for filename in player_data_files:
                    remote_file_path = os.path.join(self.__settings['SFTP_PLAYER_DATA_PATH'], filename)
                    local_file_path = os.path.join(self.__settings['LOCAL_PLAYER_DATA_PATH'], filename)
                    sftp.get(remotepath=remote_file_path, localpath=local_file_path)
            sftp.close()
        except:
            error = traceback.format_exc()
            lines = error.split('\n')
            LOGGER.info('Can\'t reach Bisect Hosting: '+str(lines[-2]))
            return False
        self.update_player_data()
        return True
    # end poll_server

    def update_player_data(self) -> None:
        """Imports json files from a specific directory into a local variable and saves an updated player_data.json
        """
        for (dir_path, dir_names, filenames) in os.walk(self.__settings['LOCAL_PLAYER_DATA_PATH']):
            for filename in filenames:
                local_file_path = os.path.join(dir_path, filename)
                player_data = read_json_file(local_file_path)
                if player_data['username'].lower() in self.__player_data:
                    player_data['totalPlayTime'] = self.__player_data[player_data['username'].lower()]['totalPlayTime']
                    self.__player_data[player_data['username'].lower()] = player_data
                else:
                    self.__player_data[player_data['username'].lower()] = player_data 
        save_json_file(json_dict=self.__player_data, file_path='./player_data.json')
    # end update_player_data

    def get_player_data(self) -> dict:
        """Returns a dictionary of imported player data

        Returns:
            dict: player data
        """
        return self.__player_data
    # end get_player_data
# end PerkCollector

if __name__ == '__main__': # For testing purposes
    newAgent = Agent_Player_Data()
    newAgent.poll_player_data()
    newAgent.update_player_data()
    print(newAgent.get_player_data())