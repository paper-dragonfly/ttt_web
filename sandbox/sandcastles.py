import psycopg2
from configparser import ConfigParser #to do with accesing .ini files

# Get db connection data from config.ini 
def config(config_file:str='config/config.ini', section:str='postgresql') -> dict:
    parser = ConfigParser()
    parser.read(config_file)
    db_params = {}
    if parser.has_section(section):
        item_tups = parser.items(section)
        for tup in item_tups:
            db_params[tup[0]] = tup[1]
    else:
        raise Exception(f"Section {section} not found in file {config_file}")
    return db_params 

#connect to db and make curser
def db_connect():
    conn = None
    params = config()
    conn = psycopg2.connect(**params)
    cur = conn.cursor()
    return conn,cur

def fetch():
    conn, cur = db_connect()
    cur.execute("select * from game_log")
    x = cur.fetchone()[0]
    print(type(x))
    print(x) 

fetch()
