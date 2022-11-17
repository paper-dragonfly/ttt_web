from tkinter.tix import Select
import psycopg2
from configparser import ConfigParser #to do with accesing .ini files
import pdb
from typing import Dict, List, Tuple, Union
import copy
import sys

EMPTY_3X3_BOARD = [['_','_','_'],
                   ['_','_','_'],
                   ['_','_','_']]

EMPTY_4X4_BOARD = [['_','_','_','_'],
                    ['_','_','_','_'],
                    ['_','_','_','_'],
                    ['_','_','_','_']]

# Get db connection data from config.ini 
def config(config_file:str='ttt_web/config/config.ini', section:str='postgresql') -> dict:
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

#connect to db and make curser
def db_connect():
    conn = None
    params = config()
    conn = psycopg2.connect(**params)
    cur = conn.cursor()
    return conn,cur
conn, cur = db_connect()


    

# def display_gb(game_id:int)->List[List]:
#     conn, cur = db_connect()
#     # generate emptry board of correct size
#     cur.execute("SELECT board_size FROM game_log WHERE game_id=%s",(game_id,))
#     board_size = cur.fetchone()[0]
#     if board_size == 4:
#         gb = copy.deepcopy(EMPTY_4X4_BOARD)
#     elif board_size == 3: 
#         gb = copy.deepcopy(EMPTY_3X3_BOARD)
#     # 
#     sql = "SELECT player_symbol,move_coordinate FROM move_log WHERE game_id=%s"
#     str_subs = (game_id,)
#     cur.execute(sql, str_subs)
#     moves = cur.fetchall()
#     print(moves)
#     for i in range(len(moves)):
#         r = moves[i][1][0]
#         c = moves[i][1][1]
#         symb = moves[i][0]
#         gb[r][c] = symb
#     return gb
# # display_gb(5)

# def create_databases(conn,cur):
#     cur.execute("SELECT * FROM pg_catalog.pg_database where datname = 'ho' ")
#     game_db = cur.fetchone()
#     print(game_db)
#     # pdb.set_trace()
#     try:
#         len(game_db)
#         print('yes db') 
#     except TypeError:
#         print('no db')

# print(create_databases(conn, cur))

# print('done')

