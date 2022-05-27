import os
import pytest
from pydantic import BaseModel, ValidationError
# from sandbox.sandcastles import db_connect
from ttt_web import ttt_backend as tb
from ttt_web import ttt_app as ta
import json
import pdb

from ttt_web import conftest as c 

def test_log_new_game():
    """
    GIVEN a NewGame object with game_info attributes 
    WHEN this object is passed to the ttt_backend.log_new_game function 
    THEN confirm that the game was saved to the database
    """
    class NewGame(BaseModel):
            game_name:str = 'twilight'
            board_size:int = 3
            player1: str = 'blueberry'
            player2:str = 'moonshine'
    game_info = NewGame()
    game_id = tb.log_new_game(game_info, 'testing')
    assert isinstance(game_id, int)
    c.clear_test_db()
    
def test_new_game(client):
    """
    GIVEN a flask app 
    WHEN new game is created using a POST request
    THEN confirm expected text is returned indicating successful creation of game
    """

    response = client.post("/new", data=json.dumps({
        "board_size":"3",
        "player1":"sun",
        "player2":"moon",
        "game_name":"twilight",
        'test':True}), content_type='application/json')
    assert response.status_code == 200
    assert b'game successfully created' in response.data
    # delete entry from db
    c.clear_test_db()
   

def test_check_convertable():
    """
    GIVEN a potential move (user input str)
    WHEN move is passed to check_convertable function
    THEN assert that move returns expected bool
    """
    assert tb.check_convertable('A1') == True
    assert tb.check_convertable('A9') == False
    assert tb.check_convertable('Fish') == False

def test_convert():
    """
    GIVEN a properly formated move
    WHEN passed through convert function
    THEN confirm output is correct coordinate:list"""
    assert tb.convert('a1') == [0,0]

def test_check_valid():
    """
    GIVEN a coordinate
    WHEN passed through check_valid function
    THEN confirm move is within board and available
    """
    conn, cur = tb.db_connect('testing')
    c.populate_game_log(0,'violets',3,'sam','ben',conn,cur)
    cur.execute("SELECT game_id FROM game_log WHERE game_name = 'violets' ")
    violets_game_id = cur.fetchone()
    c.populate_move_log(0,violets_game_id,'x','[0,0]',conn, cur)

    assert tb.check_valid(violets_game_id,[1,1],cur) == (True, "move valid")
    assert tb.check_valid(violets_game_id, [0,0],cur) == (False, "Spot already occupied")
    assert tb.check_valid(violets_game_id,[3,3],cur) == (False,"Invalid Move, not in board range")
    cur.close()
    conn.close()
    c.clear_test_db()

def test_update_move_log():
    """
    GIVEN a valid move
    WHEN move is passed through update_move_log function
    THEN assert expected text is returned - text confirming successful update of log
    """
    # insert past moves into test db
    conn, cur = tb.db_connect('testing')
    c.populate_move_log(0, 5,'x','[0,0]',conn, cur)
    c.populate_move_log(0,5,'o','[1,1]',conn,cur)
    c.populate_move_log(0,5,'x','[2,2]',conn,cur)
    # assert that given a new valid move the move is inserted into db with right symbol
    assert tb.update_move_log(5,[0,2],conn,cur) == 'o'
    cur.close()
    conn.close()
    c.clear_test_db()

def test_check_win():
    """
    GIVEN a game_id  
    WHEN game_id and player_symbol are passed to check_win function
    THEN check if player has won the game
    """
    # insert past moves into test db - hor win, vert win, di win, no win
    conn,cur = tb.db_connect('testing')
    c.populate_game_log(5,'checking_wins',3,'cherry','leaf',conn,cur)
    c.populate_move_log(0, 5,'x','[0,0]',conn, cur)
    c.populate_move_log(0,5,'o','[2,2]',conn,cur)
    c.populate_move_log(0,5,'x','[0,1]',conn,cur)
    c.populate_move_log(0,5,'o','[1,2]',conn,cur)
    c.populate_move_log(0,5,'x','[1,1]',conn,cur)
    assert tb.check_win(conn, cur, 5,'o') == (False, 'no_win') 
    c.populate_move_log(0,5,'x','[0,2]',conn,cur) #hor win
    # run gb through check_win
    assert tb.check_win(conn,cur,5,'x') == (True, 'horizontal')
    cur.execute("UPDATE move_log SET player_symbol = 'o' WHERE move_coordinate = '[0,2]' ") # vert win
    conn.commit()
    assert tb.check_win(conn,cur,5,'o') == (True, 'vertical')
    cur.execute("UPDATE move_log SET player_symbol = 'x' WHERE move_coordinate = '[2,2]' ") # di win
    conn.commit()
    assert tb.check_win(conn,cur,5,'x') == (True, 'diagonal')
    cur.close()
    conn.close()
    c.clear_test_db()

def test_check_stale_mate():
    """
    GIVEN a game_id
    WHEN game_id is passed through check_stale_mate
    THEN check if game board is full
    """
    conn, cur = tb.db_connect('testing')
    # create game - not stale mate
    c.populate_game_log(5,'stale_bread',3,'butter','jam',conn,cur)
    c.populate_move_log(0, 5,'x','[0,0]',conn, cur)
    c.populate_move_log(0,5,'o','[0,1]',conn,cur)
    c.populate_move_log(0,5,'x','[1,1]',conn,cur)
    c.populate_move_log(0,5,'o','[0,2]',conn,cur)
    c.populate_move_log(0,5,'x','[1,2]',conn,cur)
    c.populate_move_log(0,5,'o','[1,0]',conn,cur)
    c.populate_move_log(0,5,'x','[2,0]',conn,cur)
    c.populate_move_log(0,5,'o','[2,2]',conn,cur)
    assert tb.check_stale_mate(cur,5) == False
    # pdb.set_trace()
    c.populate_move_log(0,5,'x','[2,1]',conn,cur) 
    assert tb.check_stale_mate(cur,5) == True
    cur.close()
    conn.close()
    c.clear_test_db()

def test_update_game_log():
    """
    GIEN a game_id and player_symbole
    WHEN game_id and player_symbole are passed to update_game_log
    THEN confirm True is returned indicating successful change of game_log winner
    """
    conn, cur = tb.db_connect('testing')
    #generate a game without a winner
    c.populate_game_log(1,'pie',3,'apple','pecan',conn, cur)
    c.populate_game_log(2,'pizza',3,'ham','cheese',conn, cur)
    #change winner col to pecan
    assert tb.update_game_log(conn,cur,1,'o',True) == None
    cur.execute('SELECT winner FROM game_log WHERE game_id =1')
    winner = cur.fetchone()[0]
    assert winner == 'pecan'
    #change winner col to stalemate
    assert tb.update_game_log(conn,cur,2,'x',False) == None
    cur.execute('SELECT winner FROM game_log WHERE game_id =2')
    winner = cur.fetchone()[0]
    assert winner == 'stalemate'
    cur.close()
    conn.close()
    c.clear_test_db()

def test_move(client):
    """
    GIVEN a flash app
    WHEN a non-winning POST request with a valid move is sent to /move
    THEN check that 'move successful' str is returned
    """
    conn, cur = tb.db_connect('testing')
    #create game
    c.populate_game_log(1,'iliketomoveit',3,'fish','chips',conn,cur)
    cur.close()
    conn.close()
    # send POST request
    response = client.post("/move", data=json.dumps({"game_id":1, "move":"a1"}),content_type='application/json') 
    assert b"move added" in response.data
    c.clear_test_db()

def test_games(client):
    # add games to db to return 
    conn, cur = tb.db_connect('testing')
    cur.execute("INSERT INTO game_log(game_name, board_size) VALUES('apple',3),('bird',4),('cat',3)" )
    conn.commit()
    # pdb.set_trace()
    resp = client.get("/games") #all names
    assert b'apple' in resp.data and b'bird' in resp.data and b'cat' in resp.data
    resp = client.post("/games", data=json.dumps({"name":"pp"}), content_type='application/json')
    assert b'apple' in resp.data
    cur.close()
    conn.close()
    c.clear_test_db()

def test_display_users(client):
    # populate db with names
    conn, cur = tb.db_connect('testing')
    cur.execute("Insert INTO game_log(player1,player2) VALUES('kaja','nico'),('sun','moon'),('nico','moon'),('kaja','moon')")
    conn.commit()
    resp = client.get("/users")
    # assert get returns expected 
    assert resp.status_code == 200
    assert b"['kaja', 'moon', 'nico', 'sun']" in resp.data
    c.clear_test_db()

def test_create_leader_board():
    #populate db with user info
    conn, cur = tb.db_connect('testing')
    sql = "INSERT INTO game_log(player1, player2, winner) VALUES(%s,%s,%s),(%s,%s,%s),(%s,%s,%s),(%s,%s,%s),(%s,%s,%s)"
    str_subs = ('kaja','nico','kaja','sun','moon','stalemate','nico','moon','moon','kaja','moon','kaja','nico','kaja','kaja')
    cur.execute(sql, str_subs)
    conn.commit()
    leader_board = tb.generate_leader_board(conn, cur)
    assert leader_board == {'Player': ['Total Games', '%wins', 'Rank'], 'kaja': [3.0, 100.0, 1], 'moon': [3.0, 33.33333333333333, 2], 'nico': [3.0, None, 3], 'sun': [1.0, None, 3]}
    c.clear_test_db()

def test_userstats(client):
    #populate db with user info
    conn, cur = tb.db_connect('testing')
    sql = "INSERT INTO game_log(player1, player2, winner) VALUES(%s,%s,%s),(%s,%s,%s),(%s,%s,%s),(%s,%s,%s),(%s,%s,%s)"
    str_subs = ('kaja','nico','kaja','sun','moon','stalemate','nico','moon','moon','kaja','moon','kaja','nico','kaja','kaja')
    cur.execute(sql, str_subs)
    conn.commit()
    # send get request and assess 
    resp = client.get('userstats')
    assert b'{"Player": ["Total Games", "%wins", "Rank"], "kaja": [3.0, 100.0, 1], "moon": [3.0, 33.33333333333333, 2], "nico": [3.0, null, 3], "sun": [1.0, null, 3]}' in resp.data 
    c.clear_test_db()

def test_viewgame(client):
    #populate test_db
    conn, cur = tb.db_connect('testing')
    cur.execute("INSERT INTO game_log(game_id,board_size) VALUES (1,3)")
    cur.execute("INSERT INTO move_log(game_id,player_symbol, move_coordinate) VALUES(1,'x','[0,0]'),(1,'o','[1,1]'),(1,'x','[0,2]')") 
    conn.commit() 
    resp = client.post('/viewgame', data=json.dumps({"game_id":1}), content_type='application/json')
    assert b'{"message": [["x", "_", "x"], ["_", "o", "_"], ["_", "_", "_"]]}' in resp.data
    c.clear_test_db()













    


    












    








