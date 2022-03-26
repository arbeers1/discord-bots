import datetime
import time
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
    'vote_end': 0,
    'kick_initiator': None,
    'kick_user': None,
    'yes': 0,
    'no': 0,
    'users_voted': {}, #Tracks users voted to ensure a user only votes once
    'interaction': None #The interaction object given by Discord when a user calls /votekick
}

guild_votes = {} #Seperates vote objects by guild id (server id) in the case that the bot is in multiple servers at once and multiple instances of vote are needed

def end_vote():
    #TODO: work on this bruv
    print('VOTE ENDED')

def init_vote(interaction):
    '''Set up vote fields and server id for a vote kick to occur and replies to user'''
    kick_user_id = interaction['d']['data']['options'][0]['value']
    kick_nick = interaction['d']['data']['resolved']['members'][kick_user_id]['nick']
    kick_user = kick_nick if kick_nick != None else interaction['d']['data']['resolved']['users'][kick_user_id]['username']
    kick_initiator = interaction['d']['member']['nick'] if  interaction['d']['member']['nick'] != None else interaction['d']['member']['user']['username']
    #discord.guild(interaction['d']['guild_id'], kick_user_id)

    guild = interaction['d']['guild_id']
    guild_votes[guild]['vote_in_progress'] = True
    guild_votes[guild]['interaction'] = interaction
    guild_votes[guild]['kick_initiator'] = kick_initiator
    guild_votes[guild]['kick_user'] = kick_user

    vote_end = datetime.datetime.now() + datetime.timedelta(minutes=1)
    guild_votes[interaction['d']['guild_id']]['vote_end'] = vote_end
    message = 'Vote by: {}\r\n**Kick user:\r\n{}?**\r\n:white_check_mark:: 0\r\n❌: 0\r\n/F1 for YES\t/F2 for NO\r\nVote Ends: {}'.format(
        kick_initiator, kick_user, vote_end.strftime('%I:%M:%S'))
    discord.reply(interaction, message)

    #Check for vote end
    while True:
        if datetime.datetime.now() >= vote_end:
            break
        else:
            time.sleep(1)
    end_vote()


def update_vote_count_display(interaction):
    '''Updates the vote count message as votes come in so users can see current tally'''
    guild_id = interaction['d']['guild_id']
    new_message = 'Vote by: {}\r\n**Kick user:\r\n{}?**\r\n:white_check_mark:: {}\r\n❌: {}\r\n/F1 for YES\t/F2 for NO\r\nVote Ends: {}'.format(
        guild_votes[guild_id]['kick_initiator'], guild_votes[guild_id]['kick_user'], guild_votes[guild_id]['yes'], guild_votes[guild_id]['no'],  
        guild_votes[guild_id]['vote_end'].strftime('%I:%M:%S'))
    discord.edit_interaction(interaction, new_message)

@discord.command(name='votekick', desc='Initiates a votekick for the given user', params={'name': 'user', 'description': 'user to kick', 'type': 6, 'required': True})
def kick(interaction):
    guild = interaction['d']['guild_id']
    kick_user = interaction['d']['data']['options'][0]['value']

    if  not discord.user_connected(guild, kick_user):
        message = 'Failed to start votekick. User not in server.'
        discord.reply(interaction, message, secret_reply=True)
    elif not guild in guild_votes:
        guild_votes[guild] = vote.copy()
        init_vote(interaction)
    elif guild_votes[guild]['vote_in_progress'] == False:
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
        update_vote_count_display(guild_votes[guild]['interaction'])
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
        update_vote_count_display(guild_votes[guild]['interaction'])
        message = 'You voted: ```arm\r\nNO\r\n```'
        discord.reply(interaction, message, secret_reply=True)

discord.open_connection() #Starts the bot