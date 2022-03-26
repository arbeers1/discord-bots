from msvcrt import kbhit
import datetime
import os
import sys
sys.path.append(sys.path[0].replace('F1 To Kick', ''))
from discord import Discord

CLIENT_ID = '956693017329283072'
BOT_TOKEN = os.environ['F1_BOT_TOKEN']

discord = Discord('F1 To Kick', CLIENT_ID, BOT_TOKEN)

#Definition for a voting object. These values should not be updated but instead copied to their respective Guild in the guild_votes dict with a Guild Id as the key.
vote = {
    'vote_in_progress': False,
    'yes': 0,
    'no': 0,
    'users_voted': {} #Tracks users voted to ensure a user only votes once
}

guild_votes = {}

def init_vote(interaction):
    kick_user_id = interaction['d']['data']['options'][0]['value']
    kick_nick = interaction['d']['data']['resolved']['members'][kick_user_id]['nick']
    kick_user = kick_nick if kick_nick != None else interaction['d']['data']['resolved']['users'][kick_user_id]['username']
    kick_initiator = interaction['d']['member']['nick'] if  interaction['d']['member']['nick'] != None else interaction['d']['member']['user']['username']

    guild_votes[interaction['d']['guild_id']]['vote_in_progress'] = True

    vote_end = datetime.datetime.now() + datetime.timedelta(minutes=1)
    message = 'Vote by: {}\r\n**Kick user:\r\n{}?**\r\n:white_check_mark:: 0\r\n❌: 0\r\n/F1 for YES\t/F2 for NO\r\nVote Ends: {}'.format(
        kick_initiator, kick_user, vote_end.strftime('%I:%M:%S'))
    discord.reply(interaction, message)

@discord.command(name='votekick', desc='Initiates a votekick for the given user', params={'name': 'user', 'description': 'user to kick', 'type': 6, 'required': True})
def kick(interaction):
    if not interaction['d']['guild_id'] in guild_votes:
        guild_votes[interaction['d']['guild_id']] = vote.copy()
        init_vote(interaction)
    elif guild_votes[interaction['d']['guild_id']]['vote_in_progress'] == False:
        init_vote(interaction)
    else:
        message = 'Vote already in progress. Wait until the current vote has ended.'
        discord.reply(interaction, message, secret_reply=True)

@discord.command(name='f1', desc='Vote yes', params=None)
def vote_yes(interaction):
    guild = interaction['d']['guild_id']
    caller = interaction['d']['member']['user']['id']

    if not guild in guild_votes:
        message = 'No vote in progress. Start a vote with /votekick @user.'
        discord.reply(interaction, message, secret_reply=True)
    elif guild_votes[guild]['vote_in_progress'] == False:
        message = 'No vote in progress. Start a vote with /votekick @user.'
        discord.reply(interaction, message, secret_reply=True) 
    elif caller in guild_votes[guild]['users_voted'] and guild_votes[guild]['users_voted'][caller] == True:
        message = 'You can only vote once per vote kick.'
        discord.reply(interaction, message, secret_reply=True) 
    else:
        guild_votes[guild]['users_voted'][caller] = True
        guild_votes[guild]['yes'] += 1
        message = 'You voted: ```yaml\r\nYES\r\n```'
        discord.reply(interaction, message, secret_reply=True)

@discord.command(name='f2', desc='Vote no', params=None)
def vote_no(interaction):
    guild = interaction['d']['guild_id']
    caller = interaction['d']['member']['user']['id']

    if not guild in guild_votes:
        message = 'No vote in progress. Start a vote with /votekick @user.'
        discord.reply(interaction, message, secret_reply=True)
    elif guild_votes[guild]['vote_in_progress'] == False:
        message = 'No vote in progress. Start a vote with /votekick @user.'
        discord.reply(interaction, message, secret_reply=True)
    elif caller in guild_votes[guild]['users_voted'] and guild_votes[guild]['users_voted'][caller] == True:
        message = 'You can only vote once per vote kick.'
        discord.reply(interaction, message, secret_reply=True)
    else:
        guild_votes[guild]['users_voted'][caller] = True
        guild_votes[guild]['no'] += 1
        message = 'You voted: ```arm\r\nNO\r\n```'
        discord.reply(interaction, message, secret_reply=True)


discord.open_connection()