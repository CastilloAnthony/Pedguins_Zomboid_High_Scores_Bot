import time
import json
from datetime import datetime
from pathlib import Path
import logging
# from uuid import uuid4
LOGGER: logging.Logger = logging.getLogger("bot")

DEFAULT_SKILLS = {
    "Fitness": 0,
    "Strength": 0,
    "Cooking": 0,
    "Blunt": 0,
    "Axe": 0,
    "Lightfoot": 0,
    "Nimble": 0,
    "Sprinting": 0,
    "Sneak": 0,
    "Woodwork": 0,
    "Aiming": 0,
    "Reloading": 0,
    "Farming": 0,
    "Fishing": 0,
    "Trapping": 0,
    "PlantScavenging": 0,
    "Doctor": 0,
    "Electricity": 0,
    "Blacksmith": 0,
    "MetalWelding": 0,
    "Mechanics": 0,
    "Spear": 0,
    "Maintenance": 0,
    "SmallBlade": 0,
    "LongBlade": 0,
    "SmallBlunt": 0,
    "Tailoring": 0,
    "Tracking": 0,
    "Husbandry": 0,
    "FlintKnapping": 0,
    "Masonry": 0,
    "Pottery": 0,
    "Carving": 0,
    "Butchering": 0,
    "Glassmaking": 0,
    "Art": 0,
    "Cleaning": 0,
    "Dancing": 0,
    "Meditation": 0,
    "Music": 0,
}

# Player_data Format:
def create_default_player_data(username:str, user_id:str = 'None') -> dict:
    return {
        'username' : username,
        'user_id' : user_id,
        'lastLogin' : time.time(),
        'totalPlayTime' : 0,
        'hoursSurvived' : 0,
        'skills' : DEFAULT_SKILLS.copy(),
    }

def read_data_file(file_path:str = './player_data.json') -> dict:
    if not Path(file_path).is_file():
        with open(file_path, 'w') as file:
            json.dump({
            }, file, indent=4)
        LOGGER.info(f'Created new {file_path} file.')
        return {}
    else:
        with open(file_path, 'r') as file:
            LOGGER.info(f'Loaded {file_path} file.')
            return json.load(file)
# end read_connection_settings

def save_data_file(player_data:dict, file_path:str = './player_data.json') -> None:
    with open(file_path, 'w') as file:
        json.dump(player_data, fp=file, indent=4)
        # LOGGER.info(f'Updated {file_path}')
        return
# end save_player_data

def log_parser(logLine:str) -> dict: # Returns a dictionary of the log message broken down into its respective parts. Three different types can be had. 
    if '(perform)' in logLine:
        logLine= logLine.replace('(perform)', '')
    elif '(stop)' in logLine:
        logLine = logLine.replace('(stop)', '')
    newList = (logLine[:23]+logLine[24:-3]).strip('[]').split('][') # Remove whitespace between timestamp and user_id, outer brackets, and split into separate keys. 
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
    elif newList[4] == 'Created Player 1':
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
    elif newList[4] == 'WriteSkillRecoveryJournal STOP':
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
    elif newList[4] == 'ReadSkillRecoveryJournal  STOP': #
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
    else: # Skills
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
# end logParser
    
def parse_hours_survived(text:str) -> int:
    count = 0
    for c in reversed(text):
        if c == ' ':
            break
        else:
            count -= 1
    return int(text[len(text)+count:])
# end parseHourseSurvived

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
# end parseSkills

def check_old_player_data() -> dict:
    files = ['./player_times.json', './seen_skills.json']
    oldData = {}
    newData = {}
    for i in files:
        if Path(i).is_file():
            with open(i, 'r') as file:
                LOGGER.info(f'Founded and loaded old player data from {i} file.')
                oldData[i] = json.load(file)
    # print(oldData)
    for i, j in oldData.items():
        for key, value in j.items():
            if key not in newData:
                newData[key] = create_default_player_data(key)
            if i == './player_times.json':
                newData[key]['totalPlayTime'] = value
            elif i == './seen_skills.json':
                newData[key]['skills'] = value
    return newData
# end check_old_player_data
