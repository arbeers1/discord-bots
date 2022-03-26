from msvcrt import kbhit
import os
import sys
sys.path.append(sys.path[0].replace('F1 To Kick', ''))
from discord import Discord

CLIENT_ID = '956693017329283072'
BOT_TOKEN = os.environ['F1_BOT_TOKEN']

discord = Discord('F1 To Kick', CLIENT_ID, BOT_TOKEN)

vote = {
    'vote_in_progress': False,
    'yes': 0,
    'no': 0,
    'users_voted': {} #Tracks users voted to ensure a user only votes once
}

@discord.command(name='votekick', desc='Initiates a votekick for the given user', params={'name': 'user', 'description': 'user to kick', 'type': 6, 'required': True})
def kick(interaction):
    if not vote['vote_in_progress']:
        kick_user = interaction['d']['data']['options'][0]['value']
        kick_user = interaction['d']['data']['resolved']['users'][kick_user]['username']
        kick_initiator = interaction['d']['member']['user']['username']

        message = 'Vote by: {}\r\n**Kick user:\r\n{}?**\r\n:white_check_mark:: 0\r\n❌: 0\r\n/F1 for YES\t/F2 for NO'.format(kick_initiator, kick_user)
        discord.reply(interaction, message)
    else:
        message = 'Vote already in progress. Wait until the current vote has ended.'
        discord.reply(interaction, message, secret_reply=True)

@discord.command(name='f1', desc='Vote yes', params=None)
def vote_yes(interaction):
    print('User voted yes')

@discord.command(name='f2', desc='Vote no', params=None)
def vote_no(interaction):
    print('User voted no')


discord.open_connection()

