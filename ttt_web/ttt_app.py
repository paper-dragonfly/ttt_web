from flask import Flask, request, redirect, url_for 
import ttt_backend as ttt 

ttt_app = Flask(__name__)

@ttt_app.route('/home')
def home():
    return ttt.INTRO_TEXT

@ttt_app.route('/new', methods=['GET','POST'])
def new_game():
    # import pdb; pdb.set_trace()
    if request.method == 'POST':
        new_game_POST_info:dict = request.get_json()
        game_id_tup = ttt.log_new_game(new_game_POST_info)
        game_id = int(game_id_tup[0])
        if game_id:
            #TODO: don't actually want to redirect to display_game. Testing
            return redirect(url_for("display_game"))
        else:
            return 'error:no game_id returned' 
    else:
        return "<h1>Request Fields:\nboard_size\nplayer1\nplayer2\ngame_name</h1>"


# Customize URL based on game_id? Do I even need this endpoint? 
@ttt_app.route('/5', methods=['GET','POST'])
def display_game():
    return "Success!"



if __name__ == "__main__":
    ttt_app.run(host='localhost',port=5001)
