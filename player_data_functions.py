import time
import json
from datetime import datetime
from pathlib import Path
import traceback
import logging
# from uuid import uuid4
LOGGER: logging.Logger = logging.getLogger("bot")
import copy

# Old Style
# DEFAULT_SKILLS = {
#     "Fitness": 0,
#     "Strength": 0,
#     "Cooking": 0,
#     "Blunt": 0,
#     "Axe": 0,
#     "Lightfoot": 0,
#     "Nimble": 0,
#     "Sprinting": 0,
#     "Sneak": 0,
#     "Woodwork": 0,
#     "Aiming": 0,
#     "Reloading": 0,
#     "Farming": 0,
#     "Fishing": 0,
#     "Trapping": 0,
#     "PlantScavenging": 0,
#     "Doctor": 0,
#     "Electricity": 0,
#     "Blacksmith": 0,
#     "MetalWelding": 0,
#     "Mechanics": 0,
#     "Spear": 0,
#     "Maintenance": 0,
#     "SmallBlade": 0,
#     "LongBlade": 0,
#     "SmallBlunt": 0,
#     "Tailoring": 0,
#     "Tracking": 0,
#     "Husbandry": 0,
#     "FlintKnapping": 0,
#     "Masonry": 0,
#     "Pottery": 0,
#     "Carving": 0,
#     "Butchering": 0,
#     "Glassmaking": 0,
#     "Art": 0,
#     "Cleaning": 0,
#     "Dancing": 0,
#     "Meditation": 0,
#     "Music": 0,
# }

DEFAULT_SKILLS = {
    "Axe": 0,
    "Long Blunt": 0,
    "Short Blunt": 0,
    "Long Blade": 0,
    "Short Blade": 0,
    "Spear": 0,
    "Maintenance": 0,
    "Aiming": 0,
    "Reloading": 0,
    "Carpentry": 0,
    "Carving": 0,
    "Cooking": 0,
    "Electrical": 0,
    "First Aid": 0,
    "Glassmaking": 0,
    "Knapping": 0,
    "Masonry": 0,
    "Blacksmithing": 0,
    "Mechanics": 0,
    "Pottery": 0,
    "Tailoring": 0,
    "Welding": 0,
    "Fishing": 0,
    "Foraging": 0,
    "Tracking": 0,
    "Trapping": 0,
    "Fitness": 0,
    "Strength": 0,
    "Agility": 0,
    "Lightfooted": 0,
    "Nimble": 0,
    "Running": 0,
    "Sneaking": 0,
    "Agriculture": 0,
    "Animal Care": 0,
    "Butchering": 0,
    "Art": 0,
    "Cleaning": 0,
    "Dancing": 0,
    "Meditation": 0,
    "Music": 0
}

def get_default_skills() -> dict:
    return copy.deepcopy(DEFAULT_SKILLS)
# end get_default_skills

def read_json_file(file_path:str) -> dict:
    try:
        if not Path(file_path).is_file():
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump({
                }, file, indent=4)
            # LOGGER.info(f'Created new {file_path} file.')
            return {}
        else:
            with open(file_path, 'r', encoding='utf-8') as file:
                # LOGGER.info(f'Loaded {file_path} file.')
                return json.load(file)
    except:
        error = traceback.format_exc()
        lines = error.split('\n')
        print(error)
        LOGGER.warning(f'There was an error in reading {file_path}')
        LOGGER.error('Error in agent_player_data.py function poll_player_data')
        return {}
# end read_json_file

def save_json_file(json_dict:dict, file_path:str) -> None:
    with open(file_path, 'w') as file:
        json.dump(json_dict, fp=file, indent=4)
        # LOGGER.info(f'Updated {file_path}')
        return
# end save_json_file

def parse_hours_survived(text:str) -> int:
    count = 0
    for c in reversed(text):
        if c == ' ':
            break
        else:
            count -= 1
    return int(text[len(text)+count:])
# end parse_hours_survived

def parse_skills(skills:str) -> dict:
    newList = skills.split(', ')
    newDict = {}
    for i in newList:
        count = 0
        for c in i:
            if c == '=':
                newDict[i[:count]] = int(i[count+1:])
            count += 1
    return newDict
# end parse_skills

def log_parser(logLine:str) -> dict: # Returns a dictionary of the log message broken down into its respective parts. Three different types can be had. 
    if '(perform)' in logLine:
        logLine= logLine.replace('(perform)', '')
    elif '(stop)' in logLine:
        logLine = logLine.replace('(stop)', '')
    newList = (logLine[:23]+logLine[24:-3]).strip('[]').split('][') # Remove whitespace between timestamp and user_id, outer brackets, and split into separate keys. 
    newList[2] = newList[2].lower()
    if newList[4] == 'Level Changed':
        return {
            'type' : 'levelUp',
            # 'uuid' : uuid4(),
            # 'timestamp' : datetime.strptime(newList[0], '%d-%m-%y %H:%M:%S.%f'),
            'timestamp' : newList[0],
            # 'timestamp' : int(time.mktime(time.strptime(newList[0], '%d-%m-%y %H:%M:%S.%f'))),
            'user_id' : newList[1],
            'username' : newList[2],
            'coordinates' : newList[3].split(','),
            'status' : newList[4],
            'skill' : newList[5],
            'level' : int(newList[6]),
            'hoursSurvived' : parse_hours_survived(newList[7]),
        }
    elif newList[4] == 'Login': # Can it output 'Created Player 2' or 3 or 4???
        return {
            'type' : 'login',
            # 'uuid' : uuid4(),
            # 'timestamp' : datetime.strptime(newList[0], '%d-%m-%y %H:%M:%S.%f'),
            'timestamp' : newList[0],
            # 'timestamp' : int(time.mktime(time.strptime(newList[0], '%d-%m-%y %H:%M:%S.%f'))),
            'user_id' : newList[1],
            'username' : newList[2],
            'coordinates' : newList[3].split(','),
            'status' : newList[4],
            'hoursSurvived' : parse_hours_survived(newList[5]),
        }
    elif newList[4] == 'Died': # Can it output 'Created Player 2' or 3 or 4???
        return {
            'type' : 'died',
            # 'uuid' : uuid4(),
            # 'timestamp' : datetime.strptime(newList[0], '%d-%m-%y %H:%M:%S.%f'),
            'timestamp' : newList[0],
            # 'timestamp' : int(time.mktime(time.strptime(newList[0], '%d-%m-%y %H:%M:%S.%f'))),
            'user_id' : newList[1],
            'username' : newList[2],
            'coordinates' : newList[3].split(','),
            'status' : newList[4],
            'hoursSurvived' : parse_hours_survived(newList[5]),
        }
    elif 'Created Player' in newList[4]: # 'Created Player 1' and/or 'Created Player n'
        return {
            'type' : 'creation',
            # 'uuid' : uuid4(),
            # 'timestamp' : datetime.strptime(newList[0], '%d-%m-%y %H:%M:%S.%f'),
            'timestamp' : newList[0],
            # 'timestamp' : int(time.mktime(time.strptime(newList[0], '%d-%m-%y %H:%M:%S.%f'))),
            'user_id' : newList[1],
            'username' : newList[2],
            'coordinates' : newList[3].split(','),
            'status' : newList[4],
            'hoursSurvived' : parse_hours_survived(newList[5]),
        }
    elif newList[4] == 'WriteSkillRecoveryJournal START':
        return {
            'type' : 'skillJournal',
            # 'uuid' : uuid4(),
            # 'timestamp' : datetime.strptime(newList[0], '%d-%m-%y %H:%M:%S.%f'),
            'timestamp' : newList[0],
            # 'timestamp' : int(time.mktime(time.strptime(newList[0], '%d-%m-%y %H:%M:%S.%f'))),
            'user_id' : newList[1],
            'username' : newList[2],
            'coordinates' : newList[3].split(','),
            'status' : newList[4],
        }
    elif newList[4] == 'WriteSkillRecoveryJournal STOP' or newList[4] == 'WriteSkillRecoveryJournal  STOP': # Why are there two different types for the same thing in the _PerksLog.txt?
        return {
            'type' : 'skillJournal',
            # 'uuid' : uuid4(),
            # 'timestamp' : datetime.strptime(newList[0], '%d-%m-%y %H:%M:%S.%f'),
            'timestamp' : newList[0],
            # 'timestamp' : int(time.mktime(time.strptime(newList[0], '%d-%m-%y %H:%M:%S.%f'))),
            'user_id' : newList[1],
            'username' : newList[2],
            'coordinates' : newList[3].split(','),
            'status' : newList[4],
        }
    elif newList[4] == 'ReadSkillRecoveryJournal START':
        return {
            'type' : 'skillJournal',
            # 'uuid' : uuid4(),
            # 'timestamp' : datetime.strptime(newList[0], '%d-%m-%y %H:%M:%S.%f'),
            'timestamp' : newList[0],
            # 'timestamp' : int(time.mktime(time.strptime(newList[0], '%d-%m-%y %H:%M:%S.%f'))),
            'user_id' : newList[1],
            'username' : newList[2],
            'coordinates' : newList[3].split(','),
            'status' : newList[4],
        }
    elif newList[4] == 'ReadSkillRecoveryJournal  STOP' or newList[4] == 'ReadSkillRecoveryJournal STOP': # Why are there two different types for the same thing in the _PerksLog.txt?
        return {
            'type' : 'skillJournal',
            # 'uuid' : uuid4(),
            # 'timestamp' : datetime.strptime(newList[0], '%d-%m-%y %H:%M:%S.%f'),
            'timestamp' : newList[0],
            # 'timestamp' : int(time.mktime(time.strptime(newList[0], '%d-%m-%y %H:%M:%S.%f'))),
            'user_id' : newList[1],
            'username' : newList[2],
            'coordinates' : newList[3].split(','),
            'status' : newList[4],
        }
    elif 'Fitness' in newList[4] and 'Strength' in newList[4]: # Skills
        return {
            'type' : 'skills',
            # 'uuid' : uuid4(),
            # 'timestamp' : datetime.strptime(newList[0], '%d-%m-%y %H:%M:%S.%f'),
            'timestamp' : newList[0],
            # 'timestamp' : int(time.mktime(time.strptime(newList[0], '%d-%m-%y %H:%M:%S.%f'))),
            'user_id' : newList[1],
            'username' : newList[2],
            'coordinates' : newList[3].split(','),
            'skills' : parse_skills(newList[4]),
            'hoursSurvived' : parse_hours_survived(newList[5]),
        }
    else:
        data = {
            'type' : 'unhandled',
            'timestamp' : newList[0],
            'allData' : newList
        }
        LOGGER.warning(f'An unhandled log message has been detected {data}')
        return data
# end logParser



### DEPREICATED FUNCTIONS BELOW


# # Player_data Format:
# def create_default_player_data(username:str, user_id:str = 'None') -> dict:
#     return {
#         'username' : username.lower(),
#         'user_id' : user_id,
#         'lastLogin' : time.time(),
#         'characterLastLogin' : time.time(),
#         'lastPoll' : time.time(),
#         'totalPlayTime' : 0,
#         'hoursSurvived' : 0,
#         'skills' : DEFAULT_SKILLS.copy(),
#     }
# # end create_default_player_data

# def truncate_logs() -> None:
#     pass
# # end truncate_logs

# def check_old_player_data() -> dict:
#     files = ['./player_times.json', './seen_skills.json']
#     oldData = {}
#     newData = {}
#     for i in files:
#         if Path(i).is_file():
#             with open(i, 'r') as file:
#                 LOGGER.info(f'Founded and loaded old player data from {i} file.')
#                 oldData[i] = json.load(file)
#     # print(oldData)
#     for i, j in oldData.items():
#         for key, value in j.items():
#             if key not in newData:
#                 newData[key] = create_default_player_data(key)
#             if i == './player_times.json':
#                 newData[key]['totalPlayTime'] = value
#             elif i == './seen_skills.json':
#                 newData[key]['skills'] = value
#     return newData
# # end check_old_player_data

# def merge_duplicate_players() -> None: # Merge entries of players whose names appear twice in different cases i.e. "Pedguin" and "pedguin"
#     LOGGER.info(f'Searching for and merging duplicates in player_data.json')
#     old_player_data = read_json_file('./player_data.json')
#     new_player_data = {}
#     unhandled_player_data = {}
#     new_player = ''
#     for player in old_player_data:

#         # Removing Anomalies
#         if player == old_player_data[player]['user_id']: # 76561198009712979
#             continue
#         if player == '76561198009712979': # This one is getting very frustrating... I can't seem to drop the "player"
#             # print(player)
#             continue
#         if '\"' in player:
#             new_player = player.replace('\"', '').lower()
#         else:
#             new_player = player.lower()

#         # Migrating Data
#         if new_player not in new_player_data:
#             new_player_data[new_player] = old_player_data[player]
#             if 'username' not in new_player_data[new_player]:
#                 new_player_data[new_player]['username'] = new_player
#             if 'totalPlayTime' not in new_player_data[new_player]:
#                 new_player_data[new_player]['totalPlayTime'] = 0
#             if 'characterLastLogin' not in new_player_data[new_player]:
#                 new_player_data[new_player]['characterLastLogin'] = time.time()
#             if 'lastPoll' not in new_player_data[new_player]:
#                 new_player_data[new_player]['lastPoll'] = time.time()
        
#         # Merging Data
#         elif new_player in new_player_data:
#             if 'totalPlayTime' in old_player_data[player]:
#                 new_player_data[new_player]['totalPlayTime'] += old_player_data[player]['totalPlayTime']
#             if new_player_data[new_player]['hoursSurvived'] == 0 and old_player_data[player]['hoursSurvived'] != 0:
#                 new_player_data[new_player]['hoursSurvived'] = old_player_data[player]['hoursSurvived']
#             if new_player_data[new_player]['user_id'] == 'None':
#                 new_player_data[new_player]['user_id'] = old_player_data[player]['user_id']

#         # Storing Other Anomalies
#         else:
#             LOGGER.warning(f'Unhandled player data! Sending to unhandled_player_data.json')
#             unhandled_player_data = read_json_file(file_path='./unhandled_player_data.json')
#             unhandled_player_data[player] = old_player_data[player]
#             save_json_file(json_dict=unhandled_player_data, file_path='unhandled_player_data.json')
#     save_json_file(json_dict=new_player_data, file_path='./player_data.json')
#     LOGGER.info(f'Saved and unloaded player_data.json')
# # end merge_duplicate_players