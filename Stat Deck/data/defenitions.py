'''
Container file for various variable definitions. Includes command paramaters as well as 
api urls and endpoints.
'''
import os
import re
import json

class Commands:
    REGISTER_PARAMS = [
        {
            'name': 'game',
            'type': 3,
            'description': 'Game to register id with',
            'required': True,
            'choices': [
                {
                    'name': 'cs',
                    'value': 'cs'
                },
                {
                    'name': 'lol',
                    'value': 'lol'
                }
            ]
        },
        {
            'name': 'user',
            'description': 'Discord user to register',
            'type': 6,
            'required': True
        },
        {
            'name': 'game_user',
            'description': 'CS = Enter steam id | LOL = Enter summoner id',
            'type': 3,
            'required': True
        }
    ]

    MATCH_PARAMS = [
        {
            'name': 'user',
            'description': 'user to search',
            'type': 6,
            'required': True
        },
        {
            'name': 'depth',
            'description': 'Number of matches to return. Defaults is 1.',
            'type': 4,
            'required': False
        }
    ]

class Api:
    KEY = os.environ['LolApiKey']
    AMERICA_URL = 'https://americas.api.riotgames.com'
    NA_URL = 'https://na1.api.riotgames.com'
    SUMMONER_ENDPOINT = '/lol/summoner/v4/summoners/by-name/' #i35
    USER_MATCHES_ENDPOINT = '/lol/match/v5/matches/by-puuid/{puuid}/ids' #i31
    MATCH_STATS_ENDPOINT = '/lol/match/v5/matches/' #i22

class SQL:
    CREATE_TABLE = 'CREATE TABLE IF NOT EXISTS Users (User_Id INTEGER PRIMARY KEY, Steam_Id INTEGER, Summoner_Id VARCHAR(16))'
    USER_EXISTS = 'SELECT * FROM USERS WHERE User_Id=?'
    CREATE_USER = 'INSERT INTO Users (User_Id, Steam_Id, Summoner_Id) VALUES(?,?,?)'
    UPDATE_CS_ID = 'UPDATE Users SET Steam_Id=? WHERE User_Id=?'
    UPDATE_LOL_ID = 'UPDATE Users SET Summoner_Id=? WHERE User_Id=?'
    SUMMONER_ID = 'SELECT SUMMONER_ID FROM Users WHERE User_Id=?'

    PRINT_DEBUG = 'SELECT * FROM Users'

queue_types = {}
with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'queue_types.json'), 'r') as f:
    queue_json = json.load(f)
    for queue in queue_json:
        desc = re.sub('5v5 | games', '', str(queue['description']))
        queue_types[queue['queueId']] = desc

def user_display_name(interaction, user_id):
    '''Return user display name from id'''
    user_nick = interaction['d']['data']['resolved']['members'][user_id]['nick']
    user = user_nick if user_nick != None else interaction['d']['data']['resolved']['users'][user_id]['username']
    return user