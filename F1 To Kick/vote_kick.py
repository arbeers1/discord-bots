import os
import sys
sys.path.append(sys.path[0].replace('F1 To Kick', ''))
from discord import Discord

API_ENDPOINT = 'https://discord.com/api'
CLIENT_ID = '956693017329283072'
BOT_TOKEN = os.environ['F1_BOT_TOKEN']
PERMISSIONS = '3074'


discord = Discord('F1 To Kick', BOT_TOKEN)
discord.open_connection()
#print('hello')
#discord.close_connection()

