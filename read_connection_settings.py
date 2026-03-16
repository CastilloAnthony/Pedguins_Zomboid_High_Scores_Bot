# This file developed by Anthony Castillo (ComradeWolf)
import json
from pathlib import Path
import logging
LOGGER: logging.Logger = logging.getLogger("bot")

def read_connection_settings(file_path = './settings_connection.json') -> dict:
    if not Path(file_path).is_file():
        with open(file_path, 'w') as file:
            json.dump({
                "RCON_HOST" : "ip.add.res.s",
                "RCON_PORT" : 0,
                "RCON_PASSWORD" : "",
                "SFTP_HOST" : "website.com",
                "SFTP_PORT" : 2022,
                "SFTP_USER" : "username.ID.etc",
                "SFTP_PASS" : "",
                "SFTP_PLAYER_DATA_PATH" : "./cache/Lua/PlayerCharacterDataCollector",
                "LOCAL_PLAYER_DATA_PATH" : "./PlayerCharacterDataCollector",
                "POLLING_RATE" : 5,
                "MAX_POLLING_RATE" : 60,
            }, file, indent=4)
        LOGGER.info('Created new settings_connection.json file, please fill out missing passwords and/or incorrect and/or missing data.')
    else:
        with open(file_path, 'r') as file:
            return json.load(file)
# end read_connection_settings
{
"RCON_HOST": "127.0.0.1",
"RCON_PORT": 27015,
"RCON_PASSWORD": "test12345",
"SFTP_HOST": "127.0.0.1",
"SFTP_PORT": 22,
"SFTP_USER": "cao21745@yahoo.com",
"SFTP_PASS": "7Lb4Bz29!",
"POLLING_RATE" : 10,
"MAX_POLLING_RATE" : 60,
"SFTP_PLAYER_DATA_PATH" : "C:\\Users\\Anthony Castillo\\Zomboid\\Lua\\PlayerCharacterDataCollector",
"LOCAL_PLAYER_DATA_PATH" : "./PlayerCharacterDataCollector"
}