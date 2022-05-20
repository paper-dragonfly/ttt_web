import requests
import copy
import json
import pdb
from typing import Dict, List, Tuple, Union
from ttt_web.ttt_app import create_app

EXIT = 'exit'
# app = create_app('play_game')

def create_new_game()-> int:
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
        return game_id
    else:
        print(flask_game_created['message'])
        return 0

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

def run():
    print("Intro Text")
    resp_new = input("\nWhat kind of game do you want? \nA. New Game \nB. Saved Game\n> ")
    # new
    if resp_new[0].capitalize() == 'A' or resp_new[0].capitalize() == 'N':
        game_id = create_new_game()
        # game creation failed
        if game_id == 0:
            while game_id == 0:
                game_id = create_new_game()
        # game creation succeeded, get empty_board
        flask_viewgame = requests.post("http://localhost:5001/viewgame", json={'game_id':game_id})
        gb = flask_viewgame.json()['message']
        print_beautiful_board(add_axis_title(gb))
    else: #load game
        name_search = input("search for a game or press enter to list all games: ")
        if name_search == "": # all
            flask_games = requests.get("http://localhost:5001/games").json()
            print(flask_games["message"])
            # TODO: what if they don't put in correct input? 
            game_id = int(input("Select the game_id for the game you want to continue: "))    
        else:
            flask_games = requests.post("http://localhost:5001/games", json={'name':name_search}).json()
            if flask_games['count'] == 1:
                #load game directly
                pass
            else:
                print(flask_games['message'])
                game_id = int(input("Select the game_id for the game you want to continue: ")) 
                # TODO: if bad input ...
            

        






            
        

    #new
    return "DONE RUN"
    

def play() -> str:
    # DB connection has to happen in backend - removed from here
    
    print("INTRO TEXT") #fine, need to change to suit new game

    resp_game_type = input("\nWhat kind of game do you want? \nA. New Game \nB. Saved Game\n> ")
    # Saved game
    if resp_game_type[0].capitalize() == 'B' or resp_game_type[0].capitalize() == 'S':

        flask_resp = requests.post("http://localhost:5001", data={})
        game_state = load_saved_board(cur)
        gb = game_state.gb
        
    #New game
    else:
        player1, player2 = select_users(cur) 
        chosen_board_size = choose_board_size()
        if chosen_board_size == 4:
            gb = copy.deepcopy(EMPTY_4X4_BOARD)
        elif chosen_board_size == 3: 
            gb = copy.deepcopy(EMPTY_3X3_BOARD)
        game_state = GameState('new',gb,'x',list(),player1,player2)
    print_beautiful_board(add_axis_title(game_state.gb))

    winner = False
    while not winner:
        processed_user_input = get_move(game_state)
        # Save game
        if processed_user_input == 'save':
            save_game(game_state,cur, conn)
            print('your game has been saved')
            return EXIT
        # Undo last move
        elif processed_user_input == 'undo':
            last_coordinate = game_state.move_log.pop()
            game_state.gb = undo_turn(game_state.gb,last_coordinate)
            print_beautiful_board(add_axis_title(game_state.gb))
        # Print leader board and continue
        elif processed_user_input == 'leader_board':
            print("\nLEADER BOARD")
            display_leader_board(cur)
            if game_state.current_player == 'x':
                game_state.current_player = 'o'
            elif game_state.current_player == 'o':
                game_state.current_player = 'x'
        # End game - resign 
        elif processed_user_input == 'end':
            print('Game Resigned')
            return EXIT 
    # update game with new move
        else:
            game_state.gb = update_board(game_state, processed_user_input)
            game_state.move_log.append(processed_user_input)
            winner = check_win(game_state.gb, game_state.player1, game_state.player2)
            # Someone WON
            if winner:
                loser = game_state.player1
                if winner == game_state.player1:
                    loser = game_state.player2
                update_log(game_state,cur,conn,winner,loser)
                # update_user_stats(winner,loser)  
                break 
            # STALE MATE
            if len(game_state.move_log) == len(game_state.gb)**2:
                print('STALE MATE, GAME OVER!')
                update_log(game_state,cur,conn)
                return EXIT 
        if game_state.current_player == 'x':
            game_state.current_player = 'o'
        elif game_state.current_player == 'o':
            game_state.current_player = 'x'
            
    return EXIT
   

if __name__ == "__main__":
    run()

