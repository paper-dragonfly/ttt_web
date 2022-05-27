from pydantic import BaseModel

# create classes for pydantic type enforcement 
class NewGame(BaseModel):
    game_name:str
    board_size:int=3 
    player1: str
    player2:str

class DisplayGames(BaseModel):
    name:str

class Move(BaseModel):
    game_id: int
    move:str