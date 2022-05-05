from flask import Flask, request, redirect, url_for 
import ttt_backend as ttt 
from typing import Dict, List, Tuple, Union
import pdb


ttt_app = Flask(__name__)

@ttt_app.route('/home')
def home():
    return ttt.INTRO_TEXT

@ttt_app.route('/new', methods=['GET','POST'])
def new_game():
    # import pdb; pdb.set_trace()
    if request.method == 'POST':
        new_game_POST_info:dict = request.get_json()
        game_id = ttt.log_new_game(new_game_POST_info)
        if game_id:
            #TODO: don't actually want to redirect to display_game. Testing
            return f"Game successfully created. Game_id: {game_id}"
        else:
            return 'error:no game_id returned' 
    else:
        return "<h1>Request Fields:\nboard_size\nplayer1\nplayer2\ngame_name</h1>"


# Customize URL based on game_id? Do I even need this endpoint? 
@ttt_app.route('/move', methods=['GET','POST'])
def make_move():
    if request.method == "POST":
        # extract user input
        move_POST_input:dict = request.get_json()
        game_id:int = move_POST_input["game_id"]
        move:str = move_POST_input["move"]
        # convert move (eg. A1) to coordinates (0,0)
        coordinates:tuple = ttt.convert(move)
        #open db connection
        conn,cur = ttt.db_connect()
        #is move valid?
        valid:Tuple[bool,str] = ttt.check_valid(game_id, coordinates, cur)
        if not valid[0]:
            return valid[1]
        #add move to db
        add_move:Tuple[bool,str] = ttt.update_move_log(game_id, coordinates,conn,cur)
        #close db connection
        cur.close()
        conn.close()
        return add_move[1]
    else:
        return "Request Fields: game_id, move"

@ttt_app.route("/games")
def display_games():
    # open db connection
    conn, cur = ttt.db_connect()
    # get all game_id and game_name 
    cur.execute("SELECT game_name, game_id FROM game_log ORDER BY game_name")
    game_names = cur.fetchall()
    cur.close()
    conn.close()
    return f"Game Name | Game ID \n{game_names}"



if __name__ == "__main__":
    ttt_app.run(host='localhost',port=5001)
