import datetime
from email import header
import websocket
import threading
import requests
import json

class http:
    def request(type, url, endpoint, payload, headers):
        url = url + endpoint if endpoint != None else url

        if type == 'get':
            response = requests.get(url=url, params=payload, headers=headers)
        elif type == 'post':
            response = requests.post(url=url,json=payload, headers=headers)

        if response.status_code >= 400:
            print('Exited with error: {}, response body: {}'.format(response.status_code, response.json()))
            exit(1)
        else:
            try:
                return response.json()
            except requests.exceptions.JSONDecodeError : pass

class Discord:

    API_URL = 'https://discord.com/api'

    def __init__(self, bot_name, client_id, token):
        self.client_id = client_id
        self.bot_name = bot_name
        self.token = token
        self.s = None
        self.ws = None
        self.commands = {}
        self.guilds = {}
        websocket.enableTrace(True) #Verbose debug

    def __heartbeat(self, heartbeat_interval):
        '''Discord websocket connection requires a 'heartbeat' or ping on a certain interval to maintain connection'''
        timer_start = datetime.datetime.now()
        while 1:
            delta = (datetime.datetime.now() - timer_start).seconds * 1000 #millisecond duration since last ping

            if delta >= heartbeat_interval:
                payload = {'op': 1, 'd': self.s}
                self.ws.send(data=json.dumps(payload), opcode=1)
                
                #reset timer
                timer_start = datetime.datetime.now()

    def __connection_opened(self, ws):
        print('Connection Opened')

        #Ready bot
        identity = {
            'op': 2,
            'd': {
                'token': self.token,
                'properties': {
                    '$os': 'Windows/Linux',
                    '$browser': '-',
                    '$device': 'pc'
                },
                'shard': [0, 1],
                'presence': {
                    'since': None,
                    'status': 'online',
                    'afk': False,
                    'activities': [{
                        'name': 'Kicking bots',
                        'type': 4
                    }]
                },
                'intents': 513 # 1 << 9 (Guild Messages), 1 << 0 (Guilds)
            }
        }
        payload = json.dumps(identity)
        self.ws.send(data=payload, opcode=1)

    def __connection_closed(self, ws, close_status_code, close_msg):
        print('Connection closed with code: {}. Close message: {}'.format(close_status_code, close_msg))

    def __error_recieved(self, ws, error):
        if(len(str(error)) != 0):
            print('ERROR ' + str(error))

    def __message_recieved(self, ws, message):
        def run(*args):
            response = json.loads(message)
            if response['op'] == 10: #Case if initial connection to Discord webhook
                heartbeat_interval = response['d']['heartbeat_interval']
                s = response['s']
                self.__heartbeat(heartbeat_interval)
            elif response['op'] == 11:  self.s = response['s'] #Acknowledgment code after heartbeat is sent. 
            elif response['t'] == 'READY': #Case if Bot is identified and status set to online 
                print(self.bot_name + ' is now online.') 
            elif response['t'] == 'GUILD_CREATE': # Case where guild information is recieved. A guild object is created
                if response['d']['id'] not in self.guilds:
                    self.guilds[response['d']['id']] = Guild(response['d']['id'], self.token)
            elif response['t'] == 'INTERACTION_CREATE': #Case if a slash method is called by a user
                self.commands[response['d']['data']['name']](response) #Call the func ptr of the named command
        threading.Thread(target=run).start() #Respond to events on seperate thread to handle mutliple with extended queue times.

    def open_connection(self):
        #Get gateway
        headers = {'Authorization': 'Bot ' + self.token}
        response = http.request('get', Discord.API_URL, '/gateway/bot', None, headers)

        #Open websocket connection
        self.ws = websocket.WebSocketApp(response['url'], 
                                    on_open=self.__connection_opened, 
                                    on_close=self.__connection_closed, 
                                    on_message=self.__message_recieved, 
                                    on_error=self.__error_recieved)
        self.ws.run_forever()

    ###################################################
    ###METHOD DECORATOR FOR DECLARING SLASH COMMANDS###
    ###################################################
    def command(self, name, desc, params):
        def reg(func):
            if name in self.commands:
                print('Error: Command name {} already exists. Duplicate command names not allowed'.format(name))
                exit(1)
            else:
                self.commands[name] = func
                command = {
                    "name": name,
                    "type": 1,
                    "description": desc,
                }
                if params != None:
                    command['options'] = [params]
                headers = {'Authorization': 'Bot ' + self.token}
                http.request('post', Discord.API_URL, '/v8/applications/{}/commands'.format(self.client_id), command, headers)
            return
        return reg

    def reply(self, interaction, message, secret_reply=None):
        '''Replies to the chat where the interaction object was sent'''
        endpoint = '/interactions/{}/{}/callback'.format(interaction['d']['id'], interaction['d']['token'])
        headers = {'Authorization': 'Bot ' + self.token}
        ping_data = {'type': 4, 'data': {'content': message}}
        
        #Flag 64 indicates only user who invoked interaction can see the response
        if secret_reply == True:
            ping_data['data']['flags'] = 64

        http.request('post', Discord.API_URL, endpoint, ping_data, headers)
        

class Guild:

    def __init__(self, id, bot_token):
        self.id = id

        #Save guild members for quick refrence in future
        #headers = {'Authorization': 'Bot ' + bot_token}
        #response = http.request('get', Discord.API_URL, '/guilds/{}/members'.format(id), None, headers)
        #print(response)
        #exit(0)



