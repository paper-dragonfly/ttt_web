from types import NoneType
import psycopg2
from configparser import ConfigParser #to do with accesing .ini files

    
# Get db connection data from config.ini 
def config(db_name:str='postgresql', config_file:str='ttt_web/config/config.ini') -> dict:
    parser = ConfigParser()
    parser.read(config_file)
    db_params = {}
    if parser.has_section(db_name):
        item_tups = parser.items(db_name)
        for tup in item_tups:
            db_params[tup[0]] = tup[1]
    else:
        raise Exception(f"Section {db_name} not found in file {config_file}")
    return db_params 

#connect to db
def db_connect(db:str) :
    conn = None
    params = config(db)
    conn = psycopg2.connect(**params)
    cur = conn.cursor()
    return conn,cur

# create game_db if not exists
def create_game_database()-> bool:
    conn,cur = db_connect('initialize')
    cur.execute("SELECT * FROM pg_catalog.pg_database where datname = 'ttt_http_api' ")
    game_db = cur.fetchone()
    try:
        len(game_db)
        print('db already exists')
        db_created = False
    except TypeError:
        cur.execute("""CREAT DATABASE "ttt_http_api" """)
        conn.commit()
        db_created = True
    finally:
        cur.close()
        conn.close()
        return db_created

# create test_db if not exists
def create_test_database(db)-> bool:
    conn,cur=db_connect('initialize')
    cur.execute("SELECT * FROM pg_catalog.pg_database where datname = 'ttt_http_api_test' ")
    game_db = cur.fetchone()
    try:
        len(game_db)
        print('test db already exists')
        db_created = False
    except TypeError:
        cur.execute("""CREAT DATABASE "ttt_http_api_test" """)
        conn.commit()
        db_created = True
    finally:
        cur.close()
        conn.close()
        return db_created

# Create table (if unexistant) in postgres db to store info of saved games 
def create_game_log(db):
    sql_create = """
    CREATE TABLE IF NOT EXISTS game_log(
        game_id Serial PRIMARY KEY,
        game_name VARCHAR(50) NOT NULL,
        board_size INTEGER NOT NULL,
        player1 VARCHAR(25),
        player2 VARCHAR(25),
        winner VARCHAR(25))"""

    conn,cur = db_connect(f'{db}')
    conn = None
    params = config(db)
    conn = psycopg2.connect(**params)
    cur = conn.cursor()
    cur.execute(sql_create) 
    conn.commit() 
    cur.close()
    conn.close()

# create log db
def create_move_log(db):
    sql_create_log = """
    CREATE TABLE IF NOT EXISTS move_log(
        move_id SERIAL PRIMARY KEY,
        game_id INTEGER NOT NULL,
        player_symbol VARCHAR(1)
        move_coordinate JSONB
        move_timestamp TIMESTAMP)
        """
    conn = None
    params = config(db)
    conn = psycopg2.connect(**params)
    cur = conn.cursor()
    cur.execute(sql_create_log) 
    conn.commit() 
    conn.close()

if __name__ == "__main__":
    create_game_database()
    create_test_database()
    create_game_log('postgresql')
    create_move_log('postgresql')
    create_game_log('testing')
    create_move_log('testing') 
