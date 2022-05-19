from flask import Flask, request, redirect, url_for 
from ttt_web import ttt_backend as ttt 
from typing import Dict, List, Tuple, Union
import pdb
import json

#TODO: eliminate 'GET' method option for routes that don't need it

def create_app(db):
    ttt_app = Flask(__name__)

    @ttt_app.route('/home')
    def home():
        return json.dumps({"message": ttt.INTRO_TEXT})

    @ttt_app.route('/new', methods=['GET','POST'])
    def new_game():
        # import pdb; pdb.set_trace()
        if request.method == 'POST':
            new_game_POST_info:dict = request.get_json()
            game_id = ttt.log_new_game(new_game_POST_info,db)
            if game_id:
                return json.dumps({"message" : "Game successfully created", "game_id" : game_id })
            else:
                return json.dumps({"message":'error:no game_id returned'})
        else:
            return json.dumps({"message":"Request Fields:\nboard_size\nplayer1\nplayer2\ngame_name"})


    @ttt_app.route('/move', methods=['GET','POST'])
    def make_move():
        if request.method == "POST":
            # extract user input
            move_POST_input:dict = request.get_json()
            game_id:int = move_POST_input["game_id"]
            move:str = move_POST_input["move"]
            #check if move is in correct format 
            if not ttt.check_convertable(move):
                return json.dumps({"message":'Move must be a letter followed by a number within the range of the board, eg A2'})
            # convert move (eg. A1) to coordinates (0,0)
            coordinates:list = ttt.convert(move)
            #open db connection
            try:
                conn,cur = ttt.db_connect(db)
                #is move valid?
                valid:Tuple[bool,str] = ttt.check_valid(game_id, coordinates, cur)
                if not valid[0]:
                    return json.dumps({"message":valid[1]})
                #add move to db
                player_symbol = ttt.update_move_log(game_id, coordinates,conn,cur)
                
                #check win
                win = ttt.check_win(conn,cur, game_id, player_symbol)
                if win[0]:
                    winner_updated = ttt.update_game_log(conn, cur, game_id, player_symbol)
                # check stalemate 
                stale_mate = ttt.check_stale_mate(cur,game_id)
                if stale_mate:
                    winner_updated = ttt.update_game_log(conn, cur, game_id, player_symbol,False)
            finally:
                #close db connection
                cur.close()
                conn.close()
            if win[0]:
                #TODO: change to player name
                return json.dumps({"message":f"{player_symbol} wins! Game Over."})
            elif stale_mate:
                return json.dumps({"message":"Stalemate! Game Over"})
            else:
                return json.dumps({"message" : "move successful"})
        else:
            return json.dumps({"message": "Request Fields: game_id, move"})

    @ttt_app.route("/games", methods=['GET','POST'])
    def display_games():
        try: 
            # open db connection
            conn, cur = ttt.db_connect(db)
            if request.method == 'POST':
                display_POST_input = request.get_json()
                name_search = display_POST_input['name']
                sql = """SELECT game_name, game_id FROM game_log 
                            WHERE game_name LIKE %s ORDER BY game_name"""
                str_subs = (f'%{name_search}%',)
                cur.execute(sql,str_subs)
                game_names = cur.fetchall()
            else:
            # get all game_id and game_name 
                cur.execute("SELECT game_name, game_id FROM game_log")
                game_names = cur.fetchall()
        finally:
            cur.close()
            conn.close()
        return json.dumps({"message":f"Game Name | Game ID \n{game_names}"})

    @ttt_app.route("/users", methods=['GET'])
    def display_users():
        try: 
            conn, cur = ttt.db_connect(db)
            users:List[str]=ttt.display_users(cur)
        finally: 
            cur.close()
            conn.close()
        return json.dumps({"message":f'{users}'})

    @ttt_app.route("/userstats", methods=['GET','POST'])
    def display_userstats():
        try: 
            conn, cur = ttt.db_connect(db)
            leader_board:dict = ttt.generate_leader_board(conn,cur)
        finally:
            cur.close()
            conn.close()
        if request.method == 'POST':
            user = request.get_json()['user_name']
            return json.dumps({"message":f'{user}, {leader_board[user]}'})
        else:  
            return json.dumps({"message":f'{leader_board}'})

    @ttt_app.route("/viewgame", methods=["GET","POST"])
    def view_game():
        try:
            conn, cur = ttt.db_connect(db)
            if request.method == 'POST':
                game_id = request.get_json()['game_id']
                gb = ttt.display_gb(cur, game_id)
                r = f'{gb}'
            else:
                r = "Must POST valid game_id"
        finally:
            cur.close()
            conn.close()
        return json.dumps({"message":r})
    return ttt_app

if __name__ == "__main__":
    ttt_app = create_app('play_game')
    ttt_app.run(host='localhost',port=5001)
