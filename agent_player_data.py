# This file developed by Anthony Castillo (ComradeWolf)
import os
import time
from pathlib import Path
import copy
import traceback
import paramiko
import logging
LOGGER: logging.Logger = logging.getLogger("bot")

from read_connection_settings import read_connection_settings
from player_data_functions import read_json_file, save_json_file, get_default_skills#, merge_duplicate_players

class Agent_Player_Data():
    """Connects to an sftp server, copies json files from the server to a local dir, iterates over those files to import them to a variable accessible by a function
    """
    def __init__(self) -> None:
        """Imports connection settings from settings_connections.json and creates initial variable for player_data
        """
        self.__settings = read_connection_settings()
        self.__player_data = read_json_file(file_path='./player_data.json') # Reads player_data.json
        self.__level_ups = []
        self.__deaths = []
        self.merge_dupes()
        self.repair_player_data()
        # await self.poll_player_data()
    # end __init__

    async def poll_player_data(self) -> bool:
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
                    remote_file_path = self.__settings['SFTP_PLAYER_DATA_PATH']+"/"+filename # Linux
                    # remote_file_path =os.path.join(self.__settings['SFTP_PLAYER_DATA_PATH'], filename) # Windows
                    local_file_path = os.path.join(self.__settings['LOCAL_PLAYER_DATA_PATH'], filename)
                    sftp.get(remotepath=remote_file_path, localpath=local_file_path)
                if sftp:
                    sftp.close()
                    transport.close()
                await self.update_player_data()
        except:
            error = traceback.format_exc()
            lines = error.split('\n')
            print(error)
            LOGGER.error('Can\'t reach Bisect Hosting: '+str(lines[-1]))
            LOGGER.error('Error in agent_player_data.py function poll_player_data')
            return False
        finally:
            if sftp:
                sftp.close()
                transport.close()
        return True
    # end poll_server

    async def update_player_data(self) -> None:
        """Imports json files from a specific directory into a local variable and saves an updated player_data.json
        """
        for (dir_path, dir_names, filenames) in os.walk(self.__settings['LOCAL_PLAYER_DATA_PATH']):
            for filename in filenames:
                local_file_path = os.path.join(dir_path, filename)
                player_data = read_json_file(local_file_path)
                if not player_data['username'].isnumeric():
                    if player_data['username'].lower() in self.__player_data:
                        if 'totalPlayTime' in self.__player_data[player_data['username'].lower()]:
                            player_data['totalPlayTime'] = self.__player_data[player_data['username'].lower()]['totalPlayTime']
                        else:
                            player_data['totalPlayTime'] = 0

                        if 'lastLogin' in self.__player_data[player_data['username'].lower()]:
                            player_data['lastLogin'] = self.__player_data[player_data['username'].lower()]['lastLogin']
                        else:
                            player_data['lastLogin'] = time.time()

                        if 'lastPoll' in self.__player_data[player_data['username'].lower()]:
                            player_data['lastPoll'] = self.__player_data[player_data['username'].lower()]['lastPoll']
                        else:
                            player_data['lastPoll'] = time.time()

                        if player_data['is_alive'] == self.__player_data[player_data['username'].lower()]['is_alive']: # Ensures that player is still alive and not a new character
                            for perk in player_data['perks']:
                                if player_data['perks'][perk] == self.__player_data[player_data['username'].lower()]['perks'][perk]+1: # Level Up Detection
                                    self.__level_ups.append((
                                        player_data['username'], # Username
                                        perk, # Name of Perk
                                        player_data['perks'][perk], # New level of perk
                                        self.__player_data[player_data['username'].lower()]['perks'][perk] # Player's previous perk level
                                        ))

                        if player_data['is_alive'] != self.__player_data[player_data['username'].lower()]['is_alive'] and player_data['is_alive'] != True: # Check for deaths, Exclue new character
                            perks_exclude_fitness_strength = {perk: level for perk, level in player_data['perks'].items() if perk not in ['Fitness', 'Strength']}
                            self.__deaths.append((
                                player_data['username'], 
                                player_data['hours_survived'], 
                                player_data['zombie_kills'], 
                                sum(player_data['perks'].values()), 
                                max(perks_exclude_fitness_strength,key=perks_exclude_fitness_strength.get), 
                                player_data['perks'][max(perks_exclude_fitness_strength,key=perks_exclude_fitness_strength.get)],
                                ))

                        self.__player_data[player_data['username'].lower()] = player_data
                    else:
                        player_data['totalPlayTime'] = 0
                        player_data['lastLogin'] = time.time()
                        player_data['lastPoll'] = time.time()
                        self.__player_data[player_data['username'].lower()] = player_data 

        save_json_file(json_dict=self.__player_data, file_path='./player_data.json')
    # end update_player_data

    def repair_player_data(self) -> None:
        """Call AFTER merging dupes. Sets default values for missing data keys
        """
        numeric_players = []
        for player in self.__player_data:
            if not player.isnumeric():
                player_data = self.__player_data[player]
                if 'username' not in player_data:
                    player_data['username'] = player

                if 'display_name' not in player_data:
                    player_data['display_name'] = player

                if 'character_name' not in player_data:
                    player_data['character_name'] = player

                if 'user_id' not in player_data:
                    player_data['user_id'] = 0

                if 'coord_x' not in player_data:
                    player_data['coord_x'] = 0
                if 'coord_y' not in player_data:
                    player_data['coord_y'] = 0
                if 'coord_z' not in player_data:
                    player_data['coord_z'] = 0

                if 'hours_survived' not in player_data and 'hoursSurvived' in player_data:
                    player_data['hours_survived'] = player_data['hoursSurvived']
                    player_data.pop('hoursSurvived')
                elif 'hours_survived' not in player_data:
                    player_data['hours_survived'] = 0.0

                if 'totalPlayTime' not in player_data:
                    player_data['totalPlayTime'] = 0.0

                if 'perks' not in player_data and 'skills' in player_data:
                    player_data['perks'] = get_default_skills()
                    player_data.pop('skills')
                elif 'perks' not in player_data:
                    player_data['perks'] = get_default_skills()

                if 'zombie_kills' not in player_data:
                    player_data['zombie_kills'] = 0

                if 'survivor_kills' not in player_data:
                    player_data['survivor_kills'] = 0

                if 'is_alive' not in player_data:
                    player_data['is_alive'] = True

                old_skills = [
                    'Husbandry', 'Farming', 'Blacksmith', 'Woodwork', 
                    'Electricity', 'Doctor', 'PlantScavenging', 'FlintKnapping', 
                    'Lightfoot', 'LongBlade', 'Blunt', 'Sprinting', 
                    'SmallBlade', 'SmallBlunt', 'Sneak', 'MetalWelding', 
                    ]
                if 'perks' in player_data:
                    recreate = False
                    for perk in player_data['perks']:
                        if perk in old_skills:
                            recreate = True
                    if recreate:
                        player_data.pop('perks')
                        player_data['perks'] = get_default_skills()

                self.__player_data[player] = player_data
            else:
                numeric_players.append(player)
        for player in numeric_players:
            LOGGER.info(f'Removed {self.__player_data.pop(player)} from player_data.jon')
        save_json_file(json_dict=self.__player_data, file_path='./player_data.json')
    # end repair_player_data

    def merge_dupes(self) -> None:
        # all_player_data = read_json_file(file_path='./player_data.json')
        drop_players = []
        for player in self.__player_data:
            if player != player.lower() and player.lower() in self.__player_data:
                player_data_a = self.__player_data[player.lower()] # Lower-cased player entry
                player_data_b = self.__player_data[player] # Non lower-cased player entry
                # if player.lower() == 'pedguin': print(player_data_a, '\n\n', player_data_b, '\n\n')
                for key in player_data_b.keys():
                    # if player.lower() == 'pedguin': print(player, isinstance(player_data_a[key], int), isinstance(player_data_a[key], float))
                    if isinstance(player_data_a[key], int) or isinstance(player_data_a[key], float):
                        if player_data_a[key] < player_data_b[key]:
                            player_data_a[key] = player_data_b[key]
                    else:
                        player_data_a[key] = player_data_b[key]
                # if player.lower() == 'pedguin': print(self.__player_data[player], '\n\n', player_data_a, '\n\n', player_data_b, '\n\n')

                self.__player_data[player.lower()] = player_data_a
                # if player.lower() == 'pedguin': print(self.__player_data[player.lower()])
                drop_players.append(player)
        if len(drop_players) > 0:
            for player in drop_players:
                self.__player_data.pop(player)
        save_json_file(json_dict=self.__player_data, file_path='./player_data.json')
    # end merge_dupes

    def update_player_total_play_time(self, username:str) -> bool:
        if username in self.__player_data:
            self.__player_data[username]['totalPlayTime'] += (time.time() - self.__player_data[username]['lastPoll'])
            self.__player_data[username]['lastPoll'] = time.time()
            save_json_file(json_dict=self.__player_data, file_path='./player_data.json')
            return True
        else:
            return False
    # end add_player_time_played

    def update_player_last_login(self, username:str, lastLogin:float) -> bool:
        if username in self.__player_data:
            self.__player_data[username]['lastLogin'] = lastLogin
            save_json_file(json_dict=self.__player_data, file_path='./player_data.json')
            return True
        else:
            return False
    # end add_player_login_time

    # def update_player_last_poll(self, username:str, lastPoll:float) -> bool:
    #     if username in self.__player_data:
    #         self.__player_data[username]['lastPoll'] = lastPoll
    #         save_json_file(json_dict=self.__player_data, file_path='./player_data.json')
    #         return True
    #     else:
    #         return False
    # # end add_player_login_time

    def get_player_data(self, username:str = None) -> dict:
        """Returns a dictionary of either all player data or just one player's data

        Returns:
            dict: player data
        """
        if username != None:
            if username in self.__player_data:
                return self.__player_data[username]
        else:
            return self.__player_data
    # end get_player_data

    def get_level_ups(self) -> list[tuple[str, str, int, int]]:
        curr_val = copy.deepcopy(self.__level_ups)
        self.__level_ups = []
        return curr_val
    # end get_level_ups

    def get_deaths(self) -> list[tuple[str, float, int, int, str, int]]:
        curr_val = copy.deepcopy(self.__deaths)
        self.__deaths = []
        return curr_val
# end PerkCollector

if __name__ == '__main__': # For testing purposes
    newAgent = Agent_Player_Data()
    newAgent.poll_player_data()
    newAgent.update_player_data()
    print(newAgent.get_player_data())