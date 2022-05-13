import os
import pytest
import ttt_backend as tb
import ttt_app as ta
import json

app = ta.create_app()

@pytest.fixture
def client():
    return app.test_client()

def test_home(client):
    response = client.get("/home")
    assert b"Welcome to Tick_Tack_Toe!" in response.data

def test_home_post(client):
    response = client.post("/home")
    assert response.status_code == 405

def test_new_game(client):
    response = client.get("/new")
    assert b"Request Fields" in response.data
    response = client.post("/new", data=json.dumps({"board_size":"3","player1":"sun","player2":"moon","game_name":"twilight"}), content_type='application/json')
    assert response.status_code == 200
    assert b'Game successfully created' in response.data

    # delet entry from db?
    conn, cur = tb.db_connect()
    cur.execute("DELETE FROM game_log WHERE game_name = %s",('twilight',))
    conn.commit()
    cur.close()
    conn.close()






