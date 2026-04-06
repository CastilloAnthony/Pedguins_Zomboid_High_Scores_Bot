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

    def connect_to_player_deaths(self) -> sqlite3.Connection:
        return sqlite3.connect(os.path.join(self.__database_path, "player_deaths.db"))
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

    def insert_into(self, table:str, *args:str, **kwargs) -> bool:
        connection = self.connect_to_player_data()
        # kwargs and args needs to be sync'd up somehow, perhaps converting kwargs into a list would be ideal
        res = connection.cursor().execute(f"INSERT INTO {table} ({", ".join(args)}) VALUES {", ".join(kwargs.values())}")
        return True
    # end

    def get_from(self, table:str, *args:str) -> dict:
        connection = self.connect_to_player_data()
        res = connection.cursor().execute(f"SELECT {", ".join(args)} FROM {table}")
        print(res.fetchall())
        return {}
    # end get_from
# end Agent_Database

if __name__ == "__main__":
    newDB = Agent_Database()
    newDB.setup_databases()
    newDB.get_from("player_data", )