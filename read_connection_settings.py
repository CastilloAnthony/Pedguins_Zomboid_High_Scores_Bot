import json
from pathlib import Path

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
            "LOG_DIR" : "/path/to/logs/",
            }, file, indent=4)
        print('Created new settings_connection.json file, please fill out missing passwords and/or incorrect and/or missing data.')
    else:
        with open(file_path, 'r') as file:
            return json.load(file)
# end read_connection_settings