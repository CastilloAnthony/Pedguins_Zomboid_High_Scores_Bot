# Developed by Anthony Castillo (ComradeWolf) for Peter Mann (Pedguin)
# Last Update: 04/05/2026 (DD/MM/YYYY)

import os
from pathlib import Path
import sqlite3

class Agent_Database():
    def __init__(self):
        self.__database_path = "./data"
        self.setup_databases()
    # end __init__
    
    def connect_to_player_data(self) -> sqlite3.Connection:
        return sqlite3.connect(os.path.join(self.__database_path, "player_data.db"))
    # end 

    def connect_to_world_states(self) -> sqlite3.Connection:
        return sqlite3.connect(os.path.join(self.__database_path, "world_state.db"))
    # end

    def setup_databases(self) -> None:
        if not Path(self.__database_path).is_dir(): # Create local player data directory if it doesn't exist
            Path(self.__database_path).mkdir()

        connection = self.connect_to_player_data()
        res = connection.cursor().execute("SELECt name FROM sqlite_master")
        tables = []
        notNone = True
        while notNone:
            temp = res.fetchone()
            if temp != None:
                tables.append(temp[0])
            else:
                notNone = False
        if "player_data" not in tables:
            connection.cursor().execute("CREATE TABLE player_data (username VARCHAR PRIMARY KEY, steam_id INTEGER, server_user_id INTEGER, ping INTEGER, displa_name VARCHAR, character_name VARCHAR, access_level VARCHAR, role VARCHAR, faction VARCHAR, is_alive INTEGER, profession VARCHAR, time_survived_float REAL, time_survived_string VARCHAR, zombie_kills INTEGER, survivor_kills INTEGER)")
        if "coords" not in tables:
            connection.cursor().execute("CREATE TABLE coords (username VARCHAR PRIMARY KEY, x REAL, y REAL, z REAL)")
        if "nutrition" not in tables:
            connection.cursor().execute("CREATE TABLE nutrition (username VARCHAR PRIMARY KEY, weight INT, calories REAL, carbohydrates REAL, proteins REAL, lipids REAL)")
        if "perks" not in tables:
            connection.cursor().execute("CREATE TABLE perks (username VARCHAR PRIMARY KEY, axe INT)")
        if "traits" not in tables:
            connection.cursor().execute("CREATE TABLE traits (username VARCHAR PRIMARY KEY, trait VARCHAR(100))")
        if "timestamps" not in tables:
            connection.cursor().execute("CREATE TABLE timestamps (username VARCHAR PRIMARY KEY, timestamp REAL)")
        if "deaths" not in tables:
            connection.cursor().execute("CREATE TABLE deaths (username VARCHAR PRIMARY KEY, timestamp REAL, death BLOB)")
        connection.commit()
        connection.close()
    # end setup_databases

    def check_if_username_exists(self, table:str, username:str) -> bool:
        connection = self.connect_to_player_data()
        res = connection.cursor().execute(f"SELECT username FROM {table} WHERE username=\"{username}\"")
        if res.fetchone():
            connection.close()
            return True
        else:
            connection.close()
            return False
    # end 

    def insert_into(self, table:str, *args:str, **kwargs) -> bool:
        newKwargs = []
        for arg in args:
            if arg in kwargs:
                if isinstance(kwargs[arg], str):
                    newKwargs.append(f"\"{str(kwargs[arg])}\"")
                else:
                    newKwargs.append(str(kwargs[arg]))
        connection = self.connect_to_player_data()
        # kwargs and args needs to be sync'd up somehow, perhaps converting kwargs into a list would be ideal
        if self.check_if_username_exists(table, kwargs["username"]):
            updates = []
            for index, arg in enumerate(args):
                updates.append(f"{arg} = {newKwargs[index]}")
            input = f"UPDATE {table} SET {", ".join(updates)} WHERE username = \"{kwargs["username"]}\";"
            # print(input)
            res = connection.cursor().execute(input)
        else:
            input = f"INSERT INTO {table} ({", ".join(args)}) VALUES ({", ".join(newKwargs)});"
            # print(input)
            res = connection.cursor().execute(input)
        connection.commit()
        connection.close()
        return True
    # end

    def get_all_usernames(self, table:str) -> list[str]:
        connection = self.connect_to_player_data()
        res = connection.cursor().execute(f"SELECT username FROM {table}")
        result = res.fetchall()
        connection.close()
        players = []
        for player in result:
            players.append(player[0])
        return players
    # end

    def get_from(self, table:str, username:str, *args:str) -> dict: # WIP
        resulting_dict = {}
        connection = self.connect_to_player_data()
        # print(args)
        if args:
            res = connection.cursor().execute(f"SELECT {", ".join(args)} FROM {table}")
            result = res.fetchall()
            for index, arg in enumerate(args):
                resulting_dict[arg] = result[0][index]
            if 'username' not in resulting_dict:
                resulting_dict['username'] = username
        else:
            res = connection.cursor().execute(f"SELECT name FROM pragma_table_info('{table}');")
            column_names = []
            result = res.fetchall()
            for i in result:
                column_names.append(i[0])
            # print(column_names)
            res = connection.cursor().execute(f"SELECT * FROM {table} WHERE username = \"{username}\"")
            result = res.fetchall()
            for i in result:
                for index, name in enumerate(column_names):
                    resulting_dict[name] = i[index]
        return resulting_dict
    # end get_from

    def get_players_with(self, table:str, column_name:str, value) -> list[str]:
        # Returns list of players where the given column_name is equal to the requested value
        return ['']
    # end
# end Agent_Database

if __name__ == "__main__":
    newDB = Agent_Database()
    newDB.setup_databases()
    # print(newDB.check_if_username_exists(table="coords", username="ComradeWolf"))
    newDB.insert_into("coords", "username", "x", "y", "z", username="ComradeWolf", x=7, y=66, z=1)
    newDB.insert_into("coords", "username", "x", "y", "z", username="Pedguin", x=7, y=66, z=1)
    newDB.insert_into("coords", "username", "x", "y", "z", username="Osie", x=7, y=66, z=1)
    newDB.insert_into("coords", "username", "x", "y", "z", username="Hestefyr", x=7, y=66, z=1)
    newDB.insert_into("coords", "username", "x", "y", "z", username="Dawn", x=7, y=66, z=1)
    newDB.insert_into("coords", "username", "x", "y", "z", username="Cyol", x=7, y=66, z=1)
    print(newDB.get_all_usernames("coords"))
    print(newDB.get_from("coords", "Cyol"))

    # newDB.get_from("coords", )