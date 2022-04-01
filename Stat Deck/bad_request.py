def check(response, interaction, summoner_id, discord):
    if type(response) != int:
        return False
    elif response == 404:
        discord.edit_interaction(interaction, 'Summoner {} was not found.'.format(summoner_id))
        return True
    elif response == 429:
        discord.edit_interaction(interaction, 'Rate Limit Exceeded. Please try again later.')
        return True
    else:
        discord.edit_interaction(interaction, 'While processing your request a {} error was encountered. The error has been logged.')
        return True