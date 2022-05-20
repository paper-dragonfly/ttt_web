import requests
import copy
import json
import pdb
from typing import Dict, List, Tuple, Union
from ttt_web.ttt_app import create_app

INTRO_TEXT = """
Welcome to Tick Tack Toe

What you can do:
* create a new game with a name, player user names and selected board size (3x3 or 4x4)
* Continue a saved game
* Make moves on your turn using coordinates eg. A2
* Type "userstats" on your turn to access user statistics - view the leader board or view the stats for a particular player
* Type 'exit' to quit the game - your game will automatically be saved

ENJOY!
"""

def create_new_game()-> dict:
    game_name = input("Game Name: ")
    board_size = input("Select board size: A. 3x3 B. 4x4 \n>")
    if board_size.upper() == 'B' or board_size[0] == '4':
        board_size = 4
    else:
        board_size = 3
    player1 = input("Player1 Username: ")
    player2 = input("Player2 Username: ")
    data = {"game_name":game_name, "board_size":board_size,"player1":player1, "player2":player2}
    flask_game_created = requests.post("http://localhost:5001/new", json=data).json() # {"message":"...","game_id":#}
    # success
    if flask_game_created['message'] == 'game successfully created':
        game_id = flask_game_created["game_id"]
        return {"game_id":game_id, "player1":player1, "player2":player2}
    else:
        print(flask_game_created['message'])
        return {"game_id":0, "player1":player1, "player2":player2}

# VISUAL | Adds row and colum labels - asethetic only
def add_axis_title(gb:List[List]) -> List[List]:
    gb_copy = copy.deepcopy(gb) 
    board_size = len(gb)
    col_head = [" "]
    for i in range(board_size):
        col_head.append(str(i+1))
    gb_copy.insert(0,col_head)

    alphabet = ["A","B","C","D"]
    row_head = [""]
    for i in range(board_size): 
        row_head.append(alphabet[i])
    for i in range(1,(board_size+1)):
        gb_copy[i].insert(0,f'{row_head[i]}')
    return gb_copy

# VISUAL | prints out board nicely
def print_beautiful_board(gb_copy:List[List]) -> str:
    print('\n')
    size = len(gb_copy)
    board_string = str()
    for r in range(size):
        for c in range(size):
            board_string += f"{gb_copy[r][c]}  "
        board_string += "\n"
    print(board_string)
    return board_string

def display_board(game_id:int)->str:
    flask_viewgame = requests.post("http://localhost:5001/viewgame", json={'game_id':game_id})
    gb = flask_viewgame.json()['message']
    print_beautiful_board(add_axis_title(gb))

def load_game()->dict:
    name_search = input("search for a game or press enter to list all games: ")
    if name_search == "": # all
        flask_games = requests.get("http://localhost:5001/games").json()
        for key in flask_games['message']:
            print(key+" : " + str(flask_games['message'][key]))
        # print(flask_games["message"]) #dict of all games
        # TODO: what if they don't put in correct input? 
        game_id = int(input("Select the game_id for the game you want to continue: "))    
    else: # subset
        flask_games = requests.post("http://localhost:5001/games", json={'name':name_search}).json()
        if flask_games['count'] == 1: # unique
            game_board = flask_games['message']['name_search']
        else: # selection needed
            print(flask_games['message']) 
            game_id = int(input("Select the game_id for the game you want to continue: ")) 
            # TODO: if bad input ...
    # display game info
    flask_game = requests.post("http://localhost:5001/game", json={"game_id":game_id}).json()
    print("\nGAME INFO")
    print("Game Name: "+flask_game['game_name'])
    print("Game ID: "+str(flask_game["game_id"]))
    print("Player1: "+flask_game['player1'])
    print("Player2: "+flask_game['player2'])
    # determin current player
    flask_current_player = requests.post("http://localhost:5001/currentplayer", json={"game_id":game_id}).json()
    player = flask_current_player['current_player']
    return {"game_id":game_id, "player": player, "player1": flask_game['player1'],"player2": flask_game['player2']}

def make_move(game_id:int, player:str)->dict:
    move = input(f"{player} Move: ")
    # special cases
    if move == "exit":
        return {'message':'Game Exited', "game_over":True}
    if move == "userstats":
        return {'message': 'userstats', "success":False, 'game_over':False}
    # TODO add more: leader board, undo
    move_dict = {'move': move, "game_id":game_id}
    flask_move = requests.post("http://localhost:5001/move", json=move_dict).json()
    return flask_move

def display_userstats():
    select_user = input("Type a username to view their stats or press enter to view the full leader board: ")
    flask_leaderboard = requests.get('http://localhost:5001/userstats').json()
    if select_user == "":
        for key in flask_leaderboard:
            print(key, flask_leaderboard[key])
    else:
        print("\n")
        print(flask_leaderboard['Player'])
        print(flask_leaderboard[f'{select_user}'])


def run():
    # Intro and Instructions
    print(INTRO_TEXT)
    # Get game type
    resp_new = input("\nWhat kind of game do you want? \nA. New Game \nB. Saved Game\n> ")
    # new
    if resp_new[0].capitalize() == 'A' or resp_new[0].capitalize() == 'N':
        game_info = create_new_game()
        game_id = game_info["game_id"]
        player1 = game_info["player1"]
        player2 = game_info["player2"]
        player = player1
        # TODO: what if game creation failed: if id==0, while id==0
        # game creation succeeded, get empty_board
        display_board(game_id)    
    # old
    else:
        game_info = load_game()
        game_id = game_info['game_id']
        player1 = game_info['player1']
        player2 = game_info['player2'] ###not working!!
        player = game_info['player']
        display_board(game_id)
    # Make move
    move_outcome = make_move(game_id, player)
    while not move_outcome['game_over']: # game not over
            if not move_outcome['success']: 
                if move_outcome['message'] == 'userstats': #special input
                    display_userstats()
                else: # move failed   
                    print(move_outcome['message'])
                    print('try again')
            else: 
                if player == player1: #update current player
                    player = player2
                else: 
                    player = player1
            display_board(game_id) # display updated board
            move_outcome = make_move(game_id, player) # next move
    display_board(game_id) 
    print(move_outcome['message']) 
    return
   
if __name__ == "__main__":
    run()

