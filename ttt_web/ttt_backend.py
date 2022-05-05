import copy
import json 
from datetime import datetime
import re
from typing import Dict, List, Tuple, Union
import psycopg2
from configparser import ConfigParser #to do with accesing .ini files
import pdb 

EXIT = 'exit'

INTRO_TEXT = """
\nWelcome to Tick_Tack_Toe!\n
    What you can do on your turn: 
    Type coordinates to place your marker
    Type 's' or 'save' to save your game
    Type 'undo' to undo the last move
    Type 'leader board' to view player stats 
    Type 'end' to cancel the game\n """ #change later

EMPTY_3X3_BOARD = [['_','_','_'],
                   ['_','_','_'],
                   ['_','_','_']]

EMPTY_4X4_BOARD = [['_','_','_','_'],
                    ['_','_','_','_'],
                    ['_','_','_','_'],
                    ['_','_','_','_']]


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

def db_connect():
    conn = None
    params = config()
    conn = psycopg2.connect(**params)
    cur = conn.cursor()
    return conn,cur
    
def log_new_game(POST_info:dict):
    conn, cur = db_connect()
    board_size = POST_info['board_size']
    player1 = POST_info['p1']
    player2 = POST_info['p2']
    game_name = POST_info['game_name']
    
    sql_add_new_game = """INSERT INTO game_log("game_name","board_size","player1","player2","status")
                VALUES(%s,%s,%s,%s,%s)"""
    str_subs_add_new_game = (game_name,board_size,player1,player2,'active')
    cur.execute(sql_add_new_game,str_subs_add_new_game)
    conn.commit() 
    cur.execute("SELECT game_id FROM game_log WHERE game_name = %s",(game_name,))
    game_id:tuple = cur.fetchone()
    cur.close()
    conn.close()
    return game_id

 
    


