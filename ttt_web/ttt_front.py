import requests
import copy
import json
import pdb
from typing import Dict, List, Tuple, Union
from ttt_web.ttt_app import create_app
import yaml 

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
## NICO: is this the right way to config the root url?
def root_url(config_purpose:str='play_game',config_file:str='ttt_web/config/config.yaml') -> dict:
    with open(f'{config_file}', 'r') as f:
        config_dict = yaml.safe_load(f)
    host = config_dict[config_purpose]['host']
    # port = config_dict[config_purpose]['port']
    return f"http://{host}:5001" 
    # NICO: Question: when I put the port number in the config file it breaks the program at the connect_db stage. It starts that step and seems to get stuck. No error message or anything, just continual nothing ? What's the problem?

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
    url = root_url()+"/new" #http://localhost:5001/new
    flask_game_created = requests.post(url, json=data).json() # {"status_code": #, "message":"...","game_id":#}
    # success
    if flask_game_created['status_code'] == 200:
        game_id = flask_game_created["game_id"]
        return {"status_code": flask_game_created['status_code'],"game_id":game_id, "player1":player1, "player2":player2}
    else:
        print(flask_game_created['status_code'], flask_game_created['message'])
        return {"status_code": flask_game_created['status_code']} #TODO: I don't think this return is doing anything, need to deal with 500 error in run() function perhaps? Or return EXIT?

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

def display_board(game_id:int):
    url = root_url()+'/viewgame'
    flask_viewgame = requests.post(url, json={'game_id':game_id})
    gb = flask_viewgame.json()['message']
    print_beautiful_board(add_axis_title(gb))

def load_game()->dict:
    # capture user serach
    name_search = input("search for a game or press enter to list all games: ")
    game_id_valid = False
    if name_search == "": # search all
        # pdb.set_trace()
        url = root_url()+'/games'
        flask_games:dict = requests.get(url).json()
        # Print out games
        print("Game_Name | Game_ID")
        all_games:List[dict] = flask_games['message']
        for game in all_games:
            print(game['game_name']+' : '+ str(game['game_id']))
        # select game by id, ensure choice is valid game_id
        while not game_id_valid:
            try: 
                game_id = int(input("Select the game_id for the game you want to continue: "))
                for game in flask_games['message']:
                    if game_id in game.values():
                        game_id_valid = True
            except ValueError:
                print("must be an integer matching a valid game_id")   
    else: # search subset of games
        url = root_url()+'/games'
        flask_games = requests.post(url, json={'name':name_search}).json()
        # if perfect match skip second selection step
        if flask_games['count'] == 1 and 'name_search' in flask_games['message'].keys(): # unique + full game_name
            game_id = flask_games['message']['name_search']
        else: # selection needed
            # Print out games
            print("Game_Name | Game_ID")
            all_games:List[dict] = flask_games['message'] 
            for game in all_games:
                for key in game:
                    print(game[key])
            try: 
                game_id = int(input("Select the game_id for the game you want to continue: ")) 
                for game in flask_games:
                    if game_id in game.values():
                        game_id_valid = True
            except ValueError:
                print("must be an integer matching a valid game_id")    
    # display game info
    url = root_url()+'/game'
    flask_game = requests.post(url, json={"game_id":game_id}).json()
    print("\nGAME INFO")
    print("Game Name: "+flask_game['game_name'])
    print("Game ID: "+str(flask_game["game_id"]))
    print("Player1: "+flask_game['player1'])
    print("Player2: "+flask_game['player2'])
    # determin current player
    url = root_url()+'/currentplayer'
    flask_current_player = requests.post(url, json={"game_id":game_id}).json()
    player = flask_current_player['current_player']
    return {"game_id":game_id, "player": player, "player1": flask_game['player1'],"player2": flask_game['player2']}

def make_move(game_id:int, player:str)->dict:
    move = input(f"{player} Move: ")
    # special cases
    if move == "exit":
        return {'message':'Game Exited', "game_over":True}
    if move == "userstats":
        return {'message': 'userstats', "success":False, 'game_over':False}
    # TODO add more: undo
    move_dict = {'move': move, "game_id":game_id}
    url = root_url()+'/move'
    flask_move = requests.post(url, json=move_dict).json()
    return flask_move # dict with keys: message:str, success:boolean, game_over:boolean 

def display_userstats():
    select_user = input("Type a username to view their stats or press enter to view the full leader board: ")
    url = root_url()+'/userstats'
    flask_leaderboard = requests.get(url).json()
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

