# This file developed by Anthony Castillo (ComradeWolf)
import os
from pathlib import Path
import traceback
import paramiko
import logging
LOGGER: logging.Logger = logging.getLogger("bot")

from read_connection_settings import read_connection_settings
from player_data_functions import read_json_file, save_json_file, log_parser

class Agent_Perk_Log():
    """Connects to an sftp server, copies the *_PerkLog.txt files from the server to a local dir, parses and imports it to a variable accessible by a function
    """
    def __init__(self):
        """Imports connection settings from settings_connections.json and creates initial variable for perk_log
        """
        self.__settings = read_connection_settings()
        self.__perk_log = read_json_file('pz_perk_log.json')
        self.__new_perk_log = {}
        self.__latest_perk_log_filename = ''
        # self.poll_perk_log()
    # end __init__

    async def poll_perk_log(self) -> bool:
        """Connects to and copies *_PerkLog.json files from the sftp server host

        Returns:
            bool: Success or failure
        """
        sftp = None
        try:
            transport = paramiko.Transport((self.__settings['SFTP_HOST'], self.__settings['SFTP_PORT']))
            transport.connect(username=self.__settings['SFTP_USER'], password=self.__settings['SFTP_PASS'])
            sftp = paramiko.SFTPClient.from_transport(transport)
            if not Path(self.__settings['LOCAL_PERK_LOG_PATH']).is_dir():
                Path(self.__settings['LOCAL_PERK_LOG_PATH']).mkdir()
            filesnames = sftp.listdir(self.__settings['LOG_DIR'])
            perk_log_file = sorted([f for f in filesnames if f.endswith('_PerkLog.txt')])
            if perk_log_file:
                for filename in perk_log_file:
                    remote_file_path = self.__settings['LOG_DIR']+"/"+filename # Linux
                    # remote_file_path = os.path.join(self.__settings['LOG_DIR'], filename) # Windows
                    self.__latest_perk_log_filename = os.path.join(self.__settings['LOCAL_PERK_LOG_PATH'], filename)
                    sftp.get(remotepath=remote_file_path, localpath=self.__latest_perk_log_filename)
                self.update_perk_log()
        except:
            error = traceback.format_exc()
            lines = error.split('\n')
            print(error)
            LOGGER.error('Can\'t reach Bisect Hosting: '+str(lines[-1]))
            LOGGER.error('Error in agent_perk_log.py function poll_perk_log')
            return False
        finally:
            if sftp:
                sftp.close()
        return True
    # end poll_perk_log

    def update_perk_log(self) -> None:
        """_summary_
        """
        with open(self.__latest_perk_log_filename, 'r') as file:
            for line in file:
                if line != '':
                    parsed = log_parser(line)
                    if parsed['timestamp'] not in self.__perk_log:
                        if parsed['timestamp'] not in self.__new_perk_log:
                            self.__new_perk_log[parsed['timestamp']] = parsed
        save_json_file(json_dict=self.__perk_log, file_path='pz_perk_log.json')
    # end update_perk_log

    def truncate_log(self) -> None:
        """Deletes old *_PerkLog.txt files locally stored and removes info (WIP)

        Returns:
            dict: player data
        """
        pass
    # end truncate_log

    def update_new_perk_log(self, timestamp:str) -> bool:
        """_summary_

        Args:
            timestamp (str): _description_
        """
        if timestamp in self.__new_perk_log:
            if timestamp not in self.__perk_log:
                self.__perk_log[timestamp] = self.__new_perk_log.pop(timestamp)
                return True
            else:
                return False
        else:
            return False
    # end update_new_perk_log

    def get_full_log(self) -> dict:
        """Returns a dictionary of imported player data

        Returns:
            dict: player data
        """
        return self.__perk_log
    # end get_log

    def get_new_log(self) -> dict:
        """Returns a dictionary of imported player data

        Returns:
            dict: player data
        """
        return self.__new_perk_log
    # end get_log
# end perk_log_agent

if __name__ == '__main__': # For testing purposes
    newAgent = Agent_Perk_Log()
    newAgent.poll_perk_log()
    newAgent.update_perk_log()
    print(newAgent.get_log())