import psycopg2
import yaml
from ttt_web.ttt_backend import db_connect
from ttt_web.ttt_backend import config
import pdb

# create game_db if not exists
def create_game_database(test=False)-> bool:
    db_name = "ttt_http_api"
    if test:
        db_name = "ttt_http_api_test"
    conn,cur = db_connect('initialize',True)
    cur.execute("SELECT * FROM pg_catalog.pg_database where datname = %s ",(db_name,))
    game_db = cur.fetchone()
    if isinstance(game_db, tuple):
        print('db already exists')
        db_created = False
    elif game_db is None:
        conn.autocommit = True
        cur.execute(f"""CREATE DATABASE "{db_name}" """)
        db_created = True
    cur.close()
    conn.close()
    return db_created

# Create table (if unexistant) in postgres db to store info of saved games 
def create_game_log(db):
    sql_create = """
    CREATE TABLE IF NOT EXISTS game_log(
        game_id Serial PRIMARY KEY,
        game_name VARCHAR(50),
        board_size INTEGER,
        player1 VARCHAR(25),
        player2 VARCHAR(25),
        winner VARCHAR(25))"""

    conn,cur = db_connect(db)
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
        game_id INTEGER,
        player_symbol VARCHAR(1),
        move_coordinate JSONB)
        """
    conn = None
    params = config(db)
    conn = psycopg2.connect(**params)
    cur = conn.cursor()
    cur.execute(sql_create_log) 
    conn.commit() 
    conn.close()

def create_game_db():
    create_game_database(False)
    create_game_log('play_game')
    create_move_log('play_game')

def create_test_db():
    create_game_database(True)
    create_game_log('testing')
    create_move_log('testing')

if __name__ == "__main__":
    create_game_db()
    create_test_db()
     
