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
    player1 = POST_info['player1']
    player2 = POST_info['player2']
    game_name = POST_info['game_name']
    
    sql_add_new_game = """INSERT INTO game_log("game_name","board_size","player1","player2","status")
                VALUES(%s,%s,%s,%s,%s)"""
    str_subs_add_new_game = (game_name,board_size,player1,player2,'active')
    cur.execute(sql_add_new_game,str_subs_add_new_game)
    conn.commit() 
    cur.execute("SELECT game_id FROM game_log WHERE game_name = %s",(game_name,))
    game_id:int = cur.fetchone()[0]
    cur.close()
    conn.close()
    return game_id

def convert(move:str) -> tuple:
    move = move.upper()
    con_dict = {
        'A1' : [0,0],
        'A2' : [0,1],
        'A3' : [0,2],
        'A4' : [0,3],
        'B1' : [1,0],
        'B2' : [1,1],
        'B3' : [1,2],
        'B4' : [1,3],
        'C1' : [2,0],
        'C2' : [2,1],
        'C3' : [2,2],
        'C4' : [2,3],
        'D1' : [3,0],
        'D2' : [3,1],
        'D3' : [3,2],
        'D4' : [3,3],
         }
    r = con_dict[move][0]
    c = con_dict[move][1]
    return (r,c)

def check_valid(game_id:int, coordinates:tuple, cur:psycopg2.extensions.cursor):
    # is move in board? 
    cur.execute("SELECT board_size FROM game_log WHERE game_id = %s",(game_id,))
    size = cur.fetchone()[0]
    if not 0<=coordinates[0]<size and not 0<=coordinates[1]<size:
        return (False,"Invalid Move")
    # is position already taken? 
    cur.execute("SELECT move_coordinate FROM move_log WHERE game_id = %s",(game_id,))
    all_moves:List[tuple] = cur.fetchall()
    for i in range(len(all_moves)):
        if coordinates == all_moves[i][0]:
            return (False, "Spot already occupied")
    # move valid
    return (True, "move valid")


def update_move_log(game_id:int, coordinates:tuple, conn:psycopg2.extensions.connection, cur:psycopg2.extensions.cursor):
    #who's move is it, x/o?
    sql = "SELECT COUNT(*) FROM move_log WHERE game_id = %s AND player_symbol = %s"
    cur.execute(sql,(game_id,"x"))
    x_count= cur.fetchone()[0]
    cur.execute(sql,(game_id,"o"))
    o_count = cur.fetchone()[0]
    next_move = "x"
    if x_count>o_count:
        next_move = "o" 
    #insert move into db
    sql = "INSERT INTO move_log(game_id,player_symbol,move_coordinate) VALUES(%s,%s,%s)"
    cur.execute(sql,(game_id, next_move, json.dumps(coordinates)))
    conn.commit()
    return (True, "move successful")
    
def generate_leader_board(conn:psycopg2.extensions.connection, cur:psycopg2.extensions.cursor) -> dict:
    sql_get_summary_stats = """ 
    WITH 
    winner_tally AS(
        SELECT COUNT(*)::float AS ct, winner 
        FROM game_log
        GROUP BY winner),
        
    player1_tally AS(
        SELECT COUNT(*)::float as ct, player1 
        FROM game_log
        GROUP BY player1),
        
    player2_tally AS(
        SELECT COUNT(*) as ct, player2 
        FROM game_log
        GROUP BY player2),

    combo AS(
        Select
        CASE WHEN p1.player1 is NULL THEN 0 ELSE p1.ct END AS ct1,
        CASE WHEN p2.player2 is NULL THEN 0 ELSE p2.ct END AS ct2,
        CASE WHEN p2.player2 is NULL THEN p1.player1 ELSE p2.player2 END AS player  
        FROM player2_tally as p2
        FULL JOIN player1_tally as p1 ON p2.player2 = p1.player1)

    SELECT player, combo.ct1 + combo.ct2 AS "total_games", (winner_tally.ct/(combo.ct1 + combo.ct2))*100 AS percent_wins FROM combo
    FULL JOIN winner_tally ON combo.player = winner_tally.winner
    WHERE player IS NOT NULL
    ORDER BY percent_wins DESC NULLS LAST;"""

    cur.execute(sql_get_summary_stats)
    summary_stats = cur.fetchall() # player name, total games, %wins
    
    # create leader_board dict, populate with highest ranked player
    highest_ranked_player = summary_stats[0][0]
    leader_board = {
        'Player': ['Total Games', '%wins', 'Rank'],
        highest_ranked_player:[summary_stats[0][1], summary_stats[0][2], 1]}
    # fill leader_board
    for i in range(1,len(summary_stats)):
        cur_player_tup = summary_stats[i]
        #add player to leader_board dict
        leader_board[cur_player_tup[0]] = [cur_player_tup[1], cur_player_tup[2]] 
        # get info to determin if rank is same or lower than prev player
        prev_rank = leader_board[summary_stats[i-1][0]][2]
        prev_pwins = summary_stats[i-1][2]
        cur_pwins = cur_player_tup[2]
        if prev_pwins == cur_pwins: # same %wins -> same rank
            leader_board[cur_player_tup[0]].append(prev_rank)
        else: #lower %wins -> lower rank
            leader_board[cur_player_tup[0]].append(i+1)
    return leader_board 

 
    


