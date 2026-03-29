import json
from datetime import datetime
from pathlib import Path
import traceback
import logging
import shutil
import datetime
# from uuid import uuid4
LOGGER: logging.Logger = logging.getLogger("bot")
import copy

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
        errorous_dir = './errorous_jsons_data/'
        datestamp_json = str(datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))+'.json'
        LOGGER.error(f'There was an error in reading {file_path} saving copy to '+errorous_dir+datestamp_json)
        LOGGER.error('Error in player_data_functions.py function read_json_file')
        if not Path(errorous_dir).is_dir(): # Creates the Errorous Jsons directory ('./errorousJsons/')
            Path(errorous_dir).mkdir()
        shutil.copy(file_path, errorous_dir+datestamp_json)
        with open(errorous_dir+'0000_journal.log', 'a') as file:
            file.write(datestamp_json+'\t\t'+file_path+'\n')
        return {}
# end read_json_file

def save_json_file(json_dict:dict, file_path:str) -> None:
    with open(file_path, 'w') as file:
        json.dump(json_dict, fp=file, indent=4)
        # LOGGER.info(f'Updated {file_path}')
        return
# end save_json_file
