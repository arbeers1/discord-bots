import sys
from bs4 import BeautifulSoup
sys.path.append(sys.path[0].replace('Stat Deck', ''))
from discord import Discord
import cfscrape

def cs_match_history():
    ''''''
    steam_id = 76561198094731327
    url = 'https://csgostats.gg/player/{}#/matches'.format(steam_id)
    depth = 10

    #Cf scraper is used to bypass bot protection on cloudfare protected sites to scrape data.
    scraper = cfscrape.create_scraper()
    html = scraper.get(url).text
    soup = BeautifulSoup(html)

    matches =  soup.findAll('tr', {'class': 'js-link'})
    match_stats = []

    for x in range(depth):
        if x >= len(matches):
            break
        
        stats = matches[x].findAll('td')
        stat_line = (stats[0].text.strip(), stats[2].text.strip(), stats[3].text.strip(), 'rank: to be implemented', stats[6].text.strip(), stats[7].text.strip(), stats[8].text.strip(),
                     stats[11].text.strip())
        match_stats.append(stat_line)

    print(match_stats[1])

cs_match_history()

'''
League shit
payload = {
    'api_key': 'RGAPI-7bfe2788-99a2-475b-9859-34aba067294d'
}

url = 'https://americas.api.riotgames.com'
endpoint = '/lol/match/v5/matches/by-puuid/{}/ids'.format('MvWeS2jLgSphhghi1v_hIAgr7lg-HglMHONLzEwus51jDYboiTOUd6LEFsmPdoCz7OCB5AVLePjT5g')
#endpoint = '/lol/summoner/v4/summoners/by-name/{}'.format('BlackPower9k')
endpoint = '/lol/match/v5/matches/{}'.format('NA1_4258995502')

import requests
response = requests.get(url+endpoint, params=payload)
print(response.json())
'''
