import copy
import json 
from datetime import datetime
import re
from typing import Dict, List, Tuple, Union
import psycopg2
import yaml
import pdb 

INTRO_TEXT = """
\nWelcome to Tick_Tack_Toe!\n
What you can do:

/new: create a new game ->
curl -d '{"board_size":"3","player1":"sun","player2":"moon","game_name":"star"}' -H "Content-Type: application/json" -X POST http://localhost:5001/new

/move: make a move -> 
curl -d '{"game_id":1, "move":"A1"}' -H "Content-Type: application/json" -X POST http://localhost:5001/move

/games: view game(s), GET: lists all games, POST: search for games by game_name, can search by full or partial name -> 
GET:  curl http://localhost:5001/games
POST: curl -d '{"game_name": "game"} -H "Content-Type: application/json" -X POST http://localhost:5001/games

/users: displays all users ->
curl http://localhost:5001/games

/userstats: shows user statistics (User_name, total_games, %wins, rank) | GET: displays leader board with all users | POST: search stats for single user ->
GET:  curl http://localhost:5001/games
POST: curl -d '{"user_name":"kaja"}' -H "Content-Type: application/json" -X POST http://localhost:5001/new

/viewgame: displays game board for selected game ->
curl -d '{"game_id":5}' -H "Content-Type: application/json" -X POST http://localhost:5001/new """

EMPTY_3X3_BOARD = [['_','_','_'],
                   ['_','_','_'],
                   ['_','_','_']]

EMPTY_4X4_BOARD = [['_','_','_','_'],
                    ['_','_','_','_'],
                    ['_','_','_','_'],
                    ['_','_','_','_']]


# Get db connection data from config.yaml

def config(config_purpose:str,config_file:str='ttt_web/config/config.yaml') -> dict:
    with open(f'{config_file}', 'r') as f:
        config_dict = yaml.safe_load(f)
    db_params = config_dict[config_purpose]
    return db_params

def db_connect(db:str, autocommit=False):
    params = config(db)
    conn = psycopg2.connect(**params)
    conn.autocommit = autocommit
    cur = conn.cursor()
    return conn,cur
    
def log_new_game(POST_info:dict,db)->int:
    try: 
        conn, cur = db_connect(db)
        board_size = POST_info['board_size']
        player1 = POST_info['player1'].lower()
        player2 = POST_info['player2'].lower()
        game_name = POST_info['game_name']

    #TODO: UPGRADE ensure game names are unique (?) - 
    # currently multiple games can have same name, returned game_id will be lowest ID
    #added MAX -> gets most recent. Doesn't prove new entry was successful
        sql_add_new_game = """INSERT INTO game_log("game_name","board_size","player1","player2")
                    VALUES(%s,%s,%s,%s)"""
        str_subs_add_new_game = (game_name,board_size,player1,player2)
        cur.execute(sql_add_new_game,str_subs_add_new_game)
        conn.commit() 
        cur.execute("SELECT MAX(game_id) FROM game_log WHERE game_name = %s",(game_name,))
        game_id:int = cur.fetchone()[0]
    finally:
        cur.close()
        conn.close()
    return game_id

def check_convertable(move:str)->bool:
    move=move.upper()
    if move[0] in ['A','B','C','D'] and int(move[1]) in [0,1,2,3] and len(move)==2:
        return True
    else:
        return False
 
def convert(move:str) -> list:
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
    return [r,c]

def check_valid(game_id:int, coordinates:list, cur:psycopg2.extensions.cursor)-> tuple:
    # is move in board? 
    cur.execute("SELECT board_size FROM game_log WHERE game_id = %s",(game_id,))
    size = cur.fetchone()[0]
    if not 0<=coordinates[0]<size and not 0<=coordinates[1]<size:
        return (False,"Invalid Move, not in board range")
    # is position already taken? 
    cur.execute("SELECT move_coordinate FROM move_log WHERE game_id = %s",(game_id,))
    all_moves:List[tuple] = cur.fetchall()
    for i in range(len(all_moves)):
        if coordinates == all_moves[i][0]:
            return (False, "Spot already occupied")
    # move is valid
    return (True, "move valid")

def update_move_log(game_id:int, coordinates:list, conn:psycopg2.extensions.connection, cur:psycopg2.extensions.cursor)->str:
    #who's move is it, x/o?
    sql = "SELECT COUNT(*) FROM move_log WHERE game_id = %s AND player_symbol = %s"
    cur.execute(sql,(game_id,"x"))
    x_count= cur.fetchone()[0]
    cur.execute(sql,(game_id,"o"))
    o_count = cur.fetchone()[0]
    player_symbol = "x"
    if x_count>o_count:
        player_symbol = "o" 
    #insert move into db
    sql = "INSERT INTO move_log(game_id,player_symbol,move_coordinate) VALUES(%s,%s,%s)"
    cur.execute(sql,(game_id, player_symbol, json.dumps(coordinates)))
    conn.commit()
    return (player_symbol)


def check_win(conn, cur, game_id:int, player_symbol:str) -> Tuple[bool,str]:
    # get all moves for player that just played 
    sql = """SELECT move_coordinate FROM move_log 
                WHERE game_id=%s AND player_symbol=%s"""
    str_subs = (game_id, player_symbol)
    cur.execute(sql,str_subs)
    player_moves_tups = cur.fetchall()
    player_moves = []
    for i in range(len(player_moves_tups)):
        player_moves.append(player_moves_tups[i][0]) #[[0,0],[1,2],[0,2]]
    # find how many peices player has in each row/col
    cur.execute("SELECT board_size FROM game_log WHERE game_id=%s",(game_id,))
    board_size = cur.fetchone()[0]
    row_dict = {}
    col_dict = {}
    for i in range(board_size):
        row_dict[i] = 0    #eg {0:0, 1:0, 2:0}
        col_dict[i] = 0
    for i in range(len(player_moves)):
        row_dict[player_moves[i][0]] += 1
        col_dict[player_moves[i][1]] += 1
    #check horizontal
    for key in row_dict:
        if row_dict[key] == board_size:
            return (True,'horizontal') 
    # check vert
    for key in col_dict:
        if col_dict[key] == board_size:
            return (True,'vertical')
    # check di
        # determine what set of coordinates are needed for a diagonal win
        di_win1 = set()
        di_win2 = set()
        rev = board_size - 1
        for i in range(board_size):
            di_win1.add(f"{i},{i}")
            di_win2.add(f"{rev-i},{i}")
        # turn player_moves:List[List] -> set[str]
        player_moves_str:set = set()
        for coordinate in player_moves:
            player_moves_str.add(f"{coordinate[0]},{coordinate[1]}")
        # does player have coordinates for di win? 
        if di_win1.issubset(player_moves_str) or di_win2.issubset(player_moves_str):
            return (True,'diagonal')
    else:
        return (False, 'no_win')

def check_stale_mate(cur,game_id:int)->bool:
    cur.execute("SELECT COUNT(*) FROM move_log WHERE game_id=%s",(game_id,))
    total_moves = cur.fetchone()[0]
    cur.execute("SELECT board_size FROM game_log WHERE game_id=%s",(game_id,))
    board_size = cur.fetchone()[0]
    if total_moves == board_size**2:
        return True
    else:
        return False
    
def update_game_log(conn, cur, game_id:int, player_symbol:str, win:bool=True):
    # get winning player's name
    cur.execute("SELECT player1,player2 FROM game_log WHERE game_id =%s",(game_id,))
    players = cur.fetchall()
    player = players[0][0] #player1
    if player_symbol == 'o':
        player = players[0][1] #player2
    if not win:
        player = 'stalemate'
    #update winner section of game_log
    sql ="UPDATE game_log SET winner = %s WHERE game_id=%s"
    str_subs = (player, game_id)
    cur.execute(sql,str_subs) 
    conn.commit()
    return True

def display_gb(cur, game_id:int)->List[List]:
    # generate emptry board of correct size
    cur.execute("SELECT board_size FROM game_log WHERE game_id=%s",(game_id,))
    board_size = cur.fetchone()[0]
    if board_size == 4:
        gb = copy.deepcopy(EMPTY_4X4_BOARD)
    elif board_size == 3: 
        gb = copy.deepcopy(EMPTY_3X3_BOARD)
    # get moves
    sql = "SELECT player_symbol,move_coordinate FROM move_log WHERE game_id=%s"
    str_subs = (game_id,)
    cur.execute(sql, str_subs)
    moves = cur.fetchall()
    # generate gb
    for i in range(len(moves)):
        r = moves[i][1][0]
        c = moves[i][1][1]
        symb = moves[i][0]
        gb[r][c] = symb
    return gb


def display_users(cur)->List[str]:
    # Get all distinct users
    # is there a more efficient way to do this? 
    cur.execute("SELECT DISTINCT player1 FROM game_log")
    all_p1:List[Tuple] = cur.fetchall()
    cur.execute("SELECT DISTINCT player2 FROM game_log")
    all_p2:List[Tuple] = cur.fetchall() 
    users = []
    for i in range(len(all_p1)):
        user = all_p1[i][0]
        if user not in users:
            users.append(user)
    for i in range(len(all_p2)):
        user = all_p2[i][0]
        if user not in users:
            users.append(user)
    # arrange list alphabetically, ignor case
    users_alphasort = sorted(users, key=str.casefold)
    return users_alphasort
    
    
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




 
    


