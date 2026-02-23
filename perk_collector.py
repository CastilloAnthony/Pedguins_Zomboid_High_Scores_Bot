# This file developed by Anthony Castillo (ComradeWolf)
import os
from pathlib import Path
import traceback
import paramiko
import logging
LOGGER: logging.Logger = logging.getLogger("bot")
from read_connection_settings import read_connection_settings

class PerkCollector():
    def __init__(self) -> None:
        self.__settings = read_connection_settings()
        self.__player_data = {}
        # self.poll_sftp_server_for_player_data()
        # self.update_player_data()
    # end __init__

    def poll_sftp_server_for_player_data(self) -> bool:
        """Connects to and copies player_data.json files from the sftp server host

        Returns:
            bool: Success or failure
        """
        sftp = None
        try:
            transport = paramiko.Transport((self.__settings['SFTP_HOST'], self.__settings['SFTP_PORT']))
            transport.connect(username=self.__settings['SFTP_USER'], password=self.__settings['SFTP_PASS'])
            sftp = paramiko.SFTPClient.from_transport(transport)
        except:
            error = traceback.format_exc()
            lines = error.split('\n')
            LOGGER.info('Can\'t reach Bisect Hosting '+str(lines[-2]))
            return False
        if not Path(self.__settings['LOCAL_PLAYER_DATA_PATH']).is_dir():
            Path(self.__settings['LOCAL_PLAYER_DATA_PATH']).mkdir()
        filesnames = sftp.listdir(self.__settings['SFTP_PLAYER_DATA_PATH'])
        player_data_files = [f for f in filesnames if f.endswith("_data.json")]
        if player_data_files:
            for filename in player_data_files:
                file_path = os.path.join(self.__settings['SFTP_PLAYER_DATA_PATH'], filename)
                sftp.get(remotepath=file_path, localpath=self.__settings['LOCAL_PLAYER_DATA_PATH'])
        sftp.close()
        return True
    # end poll_server

    def update_player_data(self) -> None:
        file_list = [filename for filename in Path(self.__settings['LOCAL_PLAYER_DATA_PATH']) if filename.is_file()]
        for filename in file_list:
            print(filename)
    # end update_player_data

    def get_player_data(self) -> dict:
        return self.__player_data
    # end get_player_data
# end PerkCollector

if __name__ == '__main__':
    newAgent = PerkCollector()
    print(newAgent.poll_sftp_server_for_player_data())
    print(newAgent.uppdate_player_data())
    print(newAgent.get_player_data())