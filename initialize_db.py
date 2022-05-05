import psycopg2
from configparser import ConfigParser #to do with accesing .ini files

# Get db connection data from config.ini 
def config(config_file:str='config/config.ini', section:str='postgresql') -> dict:
    parser = ConfigParser()
    parser.read(config_file)
    db_params = {}
    if parser.has_section(section):
        item_tups = parser.items(section)
        for tup in item_tups:
            db_params[tup[0]] = tup[1]
    else:
        raise Exception(f"Section {section} not found in file {config_file}")
    return db_params 

#### TODO: NEED TO CHANGE TABLES

# Create table (if unexistant) in postgres db to store info of saved games 
def create_saved_games_table():
    sql_create = """
    CREATE TABLE IF NOT EXISTS saved_games(
        game_id Serial PRIMARY KEY,
        game_name VARCHAR(50) NOT NULL,
        gb TEXT[3][3] NOT NULL,
        current_player VARCHAR(10), 
        move_log JSONB)"""

    conn = None
    params = config()
    conn = psycopg2.connect(**params)
    cur = conn.cursor()
    cur.execute(sql_create) 
    conn.commit() 
    conn.close()

# create log db
def create_log():
    sql_create_log = """
    CREATE TABLE IF NOT EXISTS ttt_log(
        log_id SERIAL PRIMARY KEY,
        player1 VARCHAR(50),
        player2 VARCHAR(50),
        winner VARCHAR(50),
        loser VARCHAR(50),
        stalemate BOOLEAN DEFAULT true,
        time_stamp TIMESTAMP) 
        """
    conn = None
    params = config()
    conn = psycopg2.connect(**params)
    cur = conn.cursor()
    cur.execute(sql_create_log) 
    conn.commit() 
    conn.close()

if __name__ == "__main__":
    create_saved_games_table()
    create_log()