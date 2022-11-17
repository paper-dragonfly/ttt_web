# Project Title: Tick Tack Toe 

## Motivation
This game is a leanring exercise for me. It provided a way for me to practice python and lean new tools including using a backend database and a REST API to communicate between a frontend and backend program. 

## Summary of Game 
The game is played in the terminal. Players take turns to lay down peices ('x'/'o') attempting to fill a full row/colum/diagonal. The game board can be 3x3 or 4x4. When the program is run players are prompted to create a new games or coninue an old game. Existing games can be searched for and loaded. Game information is saved in a postgres database. The database is automatically updated every move so players do not need to actively save their games. Users can view the player leaderboard or statistics for an individual player. 

### Setup and Play
#### Initial setup
* Navigate to ttt_web/config/config.yaml and change the user and password values to match your postgres user and password. 
* Run ```ttt_web/initialize_db.py``` to create the postgres databases that will store game and test information 
#### To play the game
* Run the api: ```ttt_web/ttt_app.py```
* Open a seperate terminal and run the game: ```ttt_web/ttt_front.py```
* Follow the instructions to play the game!


### Features
Written in Python
Runs in terminal 
Built using Flask app
Uses HTTP requests to communicate between a frontend and backend
Saves data in postgres database



