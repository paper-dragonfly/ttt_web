import os
import pytest
from ttt_web import ttt_backend as tb
from ttt_web import ttt_app as ta
from ttt_web.initialize_db import create_test_db
from ttt_web.initialize_db import db_connect
import json

# db = 'testing'
app = ta.create_app('testing')

@pytest.fixture
def client():
    return app.test_client()


def clear_test_db():
    conn, cur = db_connect('testing',True)
    cur.execute("DELETE FROM move_log *")
    cur.execute("DELETE FROM game_log *")


def clear_game_db():
    conn, cur = db_connect('postgresql',True)
    cur.execute("DELETE FROM move_log *")
    cur.execute("DELETE FROM game_log *")


def delete_test_db():
    conn, cur = db_connect('testing',True)
    cur.execute("""DROP DATABASE "ttt_http_api_test" """)
    cur.close()
    conn.close()


def populate_game_log(game_id:int, game_name:str, board_size:int, player1:str, player2:str,conn, cur)-> bool:
    if game_id == 0:
        sql = "INSERT INTO game_log(game_name, board_size, player1, player2) VALUES(%s,%s,%s,%s) ON CONFLICT DO NOTHING"
        str_subs = (game_name, board_size, player1, player2)
    else:
        sql = "INSERT INTO game_log(game_id, game_name, board_size, player1, player2) VALUES(%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING"
        str_subs = (game_id, game_name, board_size, player1, player2)
    cur.execute(sql,str_subs)
    conn.commit()
    return True


def populate_move_log(move_id:int, game_id:int, player_symbol:str, move_coordinate:str,conn, cur)-> bool:
    if move_id == 0:
        sql = "INSERT INTO move_log(game_id, player_symbol, move_coordinate) VALUES(%s,%s,%s) ON CONFLICT DO NOTHING"
        str_subs = (game_id, player_symbol, move_coordinate)
    else:
        sql = "INSERT INTO move_log(move_id, game_id, player_symbol, move_coordinate) VALUES(%s,%s,%s,%s) ON CONFLICT DO NOTHING"
        str_subs = (game_id, player_symbol, move_coordinate)
    cur.execute(sql,str_subs)
    conn.commit()
    return True
