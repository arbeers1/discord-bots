from msilib.schema import Error
import sys
import os
import cfscrape
from sql import SqlPool
from bs4 import BeautifulSoup
from bad_request import check
from data.defenitions import *
sys.path.append(sys.path[0].replace('Stat Deck', ''))
from discord import Discord, http

CLIENT_ID = '958807036483739738'
BOT_TOKEN = os.environ['STAT_DECK_TOKEN']

sql_pool = SqlPool(10)
db = sql_pool.get_db()
db[1].execute(SQL.CREATE_TABLE)
sql_pool.commit(db)

Discord.log_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data/log.txt')
discord = Discord('Stat Deck', CLIENT_ID, BOT_TOKEN)

@discord.command('register', 'register a summoner or steam id', params=Commands.REGISTER_PARAMS)
def register(interaction):
    discord.reply(interaction, 'Processing ID Register')
    game = interaction['d']['data']['options'][0]['value']
    user_id = interaction['d']['data']['options'][1]['value']
    user = user_display_name(interaction, user_id)
    game_id = interaction['d']['data']['options'][2]['value']

    db = sql_pool.get_db()
    db[1].execute(SQL.USER_EXISTS, (user_id,))
    data = db[1].fetchone()
    if data != None:
        if game == 'cs':
            db[1].execute(SQL.UPDATE_CS_ID, (game_id, user_id))
        elif game == 'lol':
            db[1].execute(SQL.UPDATE_LOL_ID, (game_id, user_id))
    else:
        if game == 'cs':
            db[1].execute(SQL.CREATE_USER, (user_id, game_id, None))
        elif game == 'lol':
            db[1].execute(SQL.CREATE_USER, (user_id, None, game_id))
    sql_pool.commit(db)
    discord.edit_interaction(interaction, 'Registered id {} to {} for user: {}'.format(game_id, game, user))

def get_depth(interaction):
    if len(interaction['d']['data']['options']) > 1:
        depth = interaction['d']['data']['options'][1]['value']
    else:
        depth = 1
    if depth > 9:
        discord.reply(interaction, 'Error: Max supported depth is 9', secret_reply=True)
        return -1
    elif depth < 1:
        discord.reply(interaction, 'Error: Depth must be positive number 1 or greater', secret_reply=True)
        return -1
    else: return depth


@discord.command('cs', 'get user\'s cs match history', params=Commands.MATCH_PARAMS)
def cs(interaction):
    user_id = interaction['d']['data']['options'][0]['value']
    user = user_display_name(interaction, user_id)
    depth = get_depth(interaction)
    if depth == -1 : return

    discord.reply(interaction, 'Getting cs match history for \'{}\' with depth: {}'.format(user, str(depth)))

    db = sql_pool.get_db()
    db[1].execute(SQL.CS_ID, (user_id,))
    cs_id = db[1].fetchone()
    sql_pool.commit(db)
    if cs_id == None or cs_id[0] == None:
        discord.edit_interaction(interaction, 'User \'{}\' not registered for cs. Use /register to register your steam id.'.format(user))
        return
    cs_id = cs_id[0]

    scraper = cfscrape.create_scraper()
    html = scraper.get(Api.CS_URL.replace('{sid}', str(cs_id))).text
    if '404 Page not found!' in html:
        discord.edit_interaction(interaction, 'Steam id {} was not found.'.format(cs_id))
        return
    soup = BeautifulSoup(html, 'html.parser')

    matches =  soup.findAll('tr', {'class': 'js-link'})
    match_stats = 'Notice: Due to reliance on csgostats.gg matches may be missing or significantly delayed.\r\n'
    match_stats += 'User {}\'s match history. depth={}\r\n'.format(user, depth)
    match_stats += '```\r\n    Date    |     Map      |  Score  |      Rank      |    KDA   | ADR\r\n'
    for x in range(depth):
        if x >= len(matches) : break
        stats = matches[x].findAll('td')
        date = stats[0].text.strip()
        for month in months:
            date = re.sub(month + ' ..', '', date)
        match_stats += date.center(12) + '|'
        match_stats += stats[2].text.strip().center(14) + '|'
        match_stats += stats[3].text.strip().center(9) + '|'
        rank = stats[4].findAll('img')
        if not rank : rank = 'Unranked'
        else:
            rank = re.findall('..\.png', str(rank[0].get('src')))
            rank = CS_RANKS[rank[0]]
        match_stats += rank.center(16) + '|'
        kda = stats[6].text.strip() + '/' + stats[7].text.strip() + '/' + stats[8].text.strip()
        match_stats +=  kda.center(10) + '|'
        match_stats += stats[11].text.strip().center(6)
        match_stats += '\r\n'
    match_stats += '```'
    discord.edit_interaction(interaction, match_stats)

@discord.command('lol', 'get user\'s league of legends match history', params=Commands.MATCH_PARAMS)
def lol(interaction):
    user_id = interaction['d']['data']['options'][0]['value']
    user = user_display_name(interaction, user_id)
    depth = get_depth(interaction)
    if depth == -1 : return

    discord.reply(interaction, 'Getting league match history for \'{}\' with depth: {}'.format(user, str(depth)))

    db = sql_pool.get_db()
    db[1].execute(SQL.SUMMONER_ID, (user_id,))
    summoner_id = db[1].fetchone()
    sql_pool.commit(db)
    if summoner_id == None or summoner_id[0] == None:
        discord.edit_interaction(interaction, 'User \'{}\' not registered for lol. Use /register to register your summoner id.'.format(user))
        return
    summoner_id = summoner_id[0]

    response = http.request('get', Api.NA_URL, Api.SUMMONER_ENDPOINT + summoner_id, {'api_key': Api.KEY}, None) #Get user puuid
    if check(response, interaction, summoner_id, discord) : return
    matches = http.request('get', Api.AMERICA_URL, Api.USER_MATCHES_ENDPOINT.replace('{puuid}', response['puuid']), {'api_key': Api.KEY}, None) #Get match ids
    if check(matches, interaction, summoner_id, discord) : return

    header = 'Summoner {}\'s match history. depth={}\r\n```\r\n'.format(summoner_id, depth)
    header += ' Win |    Mode    | Lane |    Champ    |   KDA    |Chmp Dmg|CS/Min|Vis/Min\r\n'
    user_match_info = ''
    for i in range(depth):
        if i >= len(matches) :break

        response = http.request('get', Api.AMERICA_URL, Api.MATCH_STATS_ENDPOINT + matches[i], {'api_key': Api.KEY}, None)
        if check(response, interaction, summoner_id, discord) : return
        for stat in response['info']['participants']:
            if stat['summonerName'] == summoner_id:
                user_match_info += str(i+1) + ': '
                user_match_info = user_match_info + 'W'.ljust(2) + '|' if stat['win'] else user_match_info + 'L'.ljust(2) + '|'
                queue = QUEUE_TYPES[response['info']['queueId']]
                user_match_info += queue.center(12) + '|'
                if stat['individualPosition'] == 'JUNGLE' : lane = 'JUNG'
                elif stat['individualPosition'] == 'Invalid' : lane = 'N/A'
                elif stat['individualPosition'] == 'UTILITY' : lane = 'SUP'
                else : lane = stat['individualPosition'][0:3]
                user_match_info += lane.center(6) + '|'
                user_match_info += stat['championName'].center(13) + '|'
                user_match_info += '{}/{}/{}'.format(stat['kills'], stat['deaths'], stat['assists']).center(10) + '|'
                user_match_info += '{:,}'.format(stat['totalDamageDealtToChampions']).center(8) + '|'
                cs_per_minute = str(round(stat['totalMinionsKilled'] / (response['info']['gameDuration'] / 60), 2))
                user_match_info += cs_per_minute.center(6) + '|'
                try:
                    vision_per_min = str(round(stat['challenges']['visionScorePerMinute'], 2))
                except KeyError: vision_per_min = 'N/A'
                user_match_info += vision_per_min.center(6)
                user_match_info += '\r\n'
                break
    discord.edit_interaction(interaction, header  + user_match_info + '```')

discord.open_connection()