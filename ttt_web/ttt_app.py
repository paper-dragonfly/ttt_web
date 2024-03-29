from flask import Flask, request, redirect, url_for 
from ttt_web import ttt_backend as ttt 
from typing import Dict, List, Tuple, Union
import pdb
import json
from pydantic import BaseModel, ValidationError
from ttt_web.post_classes import NewGame, DisplayGames, Move

def create_app(db):
    ttt_app = Flask(__name__)

    @ttt_app.route('/new', methods=['POST'])
    def new_game():
        # use pydantic to enforce type hints for POSTed data 
        try:
            new_game_info:NewGame = NewGame.parse_obj(request.get_json())
        except ValidationError as e:
            return json.dumps({'status_code': 400, "message": e})
        # validate board size
        valid_board_sizes = [3,4]
        if not new_game_info.board_size in valid_board_sizes:
            return json.dumps({'status_code': 400, 'message':'invalid board size. Must be 3 or 4'})
        # Given valid info, add new game to game_log
        game_id = ttt.log_new_game(new_game_info,db) #False if failed
        if game_id:
            return json.dumps({"status_code": 200, "message" : "game successfully created", "game_id" : game_id })
        else:
            return json.dumps({"status_code": 500, "message":'error:no game_id returned'})
    
    @ttt_app.route('/currentplayer', methods =['POST'])
    def current_player():
    #who's move is it, x/o?
        game_id = request.get_json()['game_id']
        try:
            conn, cur=ttt.db_connect(db)
            sql = "SELECT COUNT(*) FROM move_log WHERE game_id = %s AND player_symbol = %s"
            cur.execute(sql,(game_id,"x"))
            x_count= cur.fetchone()[0]
            cur.execute(sql,(game_id,"o"))
            o_count = cur.fetchone()[0]
            player_symbol = "x"
            if x_count>o_count:
                player_symbol = "o" 
            cur.execute("SELECT player1, player2 FROM game_log WHERE game_id = %s",(game_id,))
            players = cur.fetchone()
            if player_symbol == "x":
                player = players[0] #player1
            else:
                player = players[1] #player2
        finally:
            cur.close()
            conn.close()
        return json.dumps({"current_player":player})

    @ttt_app.route('/move', methods=['POST'])
    def make_move():
        # extract user input and game_id
        try:
            move_info:Move = Move.parse_obj(request.get_json())
        except ValidationError as e:
            return json.dumps({"message": e, "success": False, "game_over":False})
        game_id:int = move_info.game_id
        move:str = move_info.move
        #check if move is in correct format 
        if not ttt.check_convertable(move):
            return json.dumps({"message":'Move must be a letter followed by a number within the range of the board, eg A2', "success": False, "game_over":False})
        # convert move (eg. A1) to coordinates (0,0)
        coordinates:list = ttt.convert(move)
        #open db connection
        try:
            conn,cur = ttt.db_connect(db)
            #is move valid? i.e. on board, open spot
            valid:Tuple[bool,str] = ttt.check_valid(game_id, coordinates, cur)
            if not valid[0]:
                return json.dumps({"message":valid[1], "success": False, "game_over":False}) #why not valid
            #add move to db
            # TODO shouldn't have to calculate player symbole here - but I'm leaving it because it works and I'm fed up
            player_symbol = ttt.update_move_log(game_id, coordinates,conn,cur)
            
            #check win
            win = ttt.check_win(conn,cur, game_id, player_symbol)
            if win[0]:# Win!
                ttt.update_game_log(conn, cur, game_id, player_symbol) #update winner column in game_log
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
            return json.dumps({"message":f"{player_symbol} wins! Game Over.", "success":True, "game_over":True})
        elif stale_mate:
            return json.dumps({"message":"Stalemate! Game Over", "success":True, "game_over":True})
        else:
            return json.dumps({"message":"move added","success":True,"game_over":False})
       

    @ttt_app.route("/games", methods=['GET','POST'])
    def display_games():
        try: 
            # open db connection
            conn, cur = ttt.db_connect(db)
            if request.method == 'POST': #search for games                
                try:
                    display_games_info = DisplayGames.parse_obj(request.get_json()) #has name attribute
                except ValidationError as e:
                    return json.dumps({"message":e, "count": 0 })
                name_search = display_games_info.name
                sql = """SELECT game_name, game_id FROM game_log 
                            WHERE winner is null AND game_name LIKE %s ORDER BY game_name"""
                str_subs = (f'%{name_search}%',)
                cur.execute(sql,str_subs)
                game_names = cur.fetchall()
                count = len(game_names)
            else:
            # GET all game_id and game_name 
                cur.execute("SELECT game_name, game_id FROM game_log WHERE winner is null")
                game_names = cur.fetchall()
                count = len(game_names)
        finally:
            cur.close()
            conn.close()
        # add games to List[dict]
        all_games = [] 
        for i in range(count):
            all_games.append({'game_name':game_names[i][0],'game_id':game_names[i][1]})
        return json.dumps({"message": all_games, "count":count})

    @ttt_app.route("/users", methods=['GET'])
    def display_users():
        try: 
            conn, cur = ttt.db_connect(db)
            users:List[str]=ttt.display_users(cur)
        finally: 
            cur.close()
            conn.close()
        return json.dumps({"message":f'{users}'})

    @ttt_app.route("/userstats", methods=['GET'])
    def return_userstats():
        try: 
            conn, cur = ttt.db_connect(db)
            leader_board:dict = ttt.generate_leader_board(conn,cur)
        finally:
            cur.close()
            conn.close()  
        return json.dumps(leader_board)

    @ttt_app.route("/viewgame", methods=["POST"])
    def view_game():
        try:
            conn, cur = ttt.db_connect(db)
            game_id = request.get_json()['game_id']
            gb = ttt.display_gb(cur, game_id)
        finally:
            cur.close()
            conn.close()
        return json.dumps({"message":gb})
    
    @ttt_app.route("/game", methods = ['POST'])
    def game_info():
        game_id = request.get_json()['game_id']
        try: 
            conn, cur = ttt.db_connect(db)
            cur.execute("SELECT game_name, game_id, player1, player2 FROM game_log WHERE game_id = %s",(game_id,))
            data = cur.fetchone()
            game_info = {"game_name":data[0], "game_id":data[1],"player1":data[2],"player2":data[3]}
        finally:
            cur.close()
            conn.close()
        return json.dumps(game_info)

    return ttt_app

if __name__ == "__main__":
    ttt_app = create_app('play_game')
    ttt_app.run(host='localhost',port=5001)
