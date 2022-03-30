import datetime
import websocket
import threading
import requests
import logging
from logging.handlers import RotatingFileHandler
import json
import time

class http:
    def request(type, url, endpoint, payload, headers):
        url = url + endpoint if endpoint != None else url

        if type == 'get':
            response = requests.get(url=url, params=payload, headers=headers)
        elif type == 'post':
            response = requests.post(url=url,json=payload, headers=headers)
        elif type =='patch':
            response = requests.patch(url=url,json=payload, headers=headers)

        if response.status_code >= 400:
            print('Exited with error: {}, response body: {}'.format(response.status_code, response.json()))
            Discord.log.error(str(response.status_code) + ': ' + str(response.json()))
            exit(1)
        else:
            try:
                return response.json()
            except requests.exceptions.JSONDecodeError : pass

class Discord: #TODO: make log a class var. test new seq

    API_URL = 'https://discord.com/api'
    log = None

    def __init__(self, bot_name, client_id, token):
        log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
        my_handler = RotatingFileHandler(Discord.log_file, mode='a', maxBytes=1*1024*1024*1024, 
                                        backupCount=2, encoding='utf-8', delay=0)
        my_handler.setFormatter(log_formatter)
        my_handler.setLevel(logging.INFO)
        Discord.log = logging.getLogger('root')
        Discord.log.setLevel(logging.INFO)
        Discord.log.addHandler(my_handler)

        self.client_id = client_id
        self.bot_name = bot_name
        self.token = token
        self.s = None
        self.session = None
        self.resume = False
        self.error = None
        self.heartbeat_requested = False
        self.ws = None
        self.thread = None #Tracks current message handler thread to join it with the main thread on reconnect.
        self.commands = {}
        self.guilds = {}
        self.auth_header = {'Authorization': 'Bot ' + self.token}
        #websocket.enableTrace(True) #Verbose debug

    def __heartbeat(self, heartbeat_interval):
        '''Discord websocket connection requires a 'heartbeat' or ping on a certain interval to maintain connection'''
        timer_start = datetime.datetime.now()

        while 1:
            delta = (datetime.datetime.now() - timer_start).seconds * 1000 #millisecond duration since last ping

            if delta >= heartbeat_interval or  self.heartbeat_requested == True:
                #If resume is set to true then the websocket is closed. Breaking will terminate this thread and a new 
                #heartbeat thread will be created when the conneciton is re-opened
                if self.resume:
                   self.resume = False
                   break

                self.heartbeat_requested = False
                payload = {'op': 1, 'd': self.s}
                self.ws.send(data=json.dumps(payload), opcode=1)
                
                #reset timer
                timer_start = datetime.datetime.now()

    def __connection_opened(self, ws):
        print('Connection Opened')

        #if self.resume: #Resume operations if connection is opened following a disconnect
        #    self.__resume()
        
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
                'intents': 129 #1 << 0 (Guilds) 1 << 7 (Voice State Update)
            }
        }
        payload = json.dumps(identity)
        self.ws.send(data=payload, opcode=1)
        Discord.log.info('Identity Sent')

    def __connection_closed(self, ws, close_status_code, close_msg):
        print('Connection closed with code: {}. Close message: {}'.format(close_status_code, close_msg))
        Discord.log.warning('Connection closed with code: {}. Close message: {}'.format(close_status_code, close_msg))

        if self.error == 'Connection to remote host was lost.':
            self.error = None
            Discord.log.info('Attempting reconnect')
            print('Connection lost. Attempting reconnect.')
            self.resume = True
            self.open_connection()

    def __error_recieved(self, ws, error):
        if(len(str(error)) != 0):
            print('ERROR ' + str(error))
        Discord.log.error(error)
        self.error = error

    def __message_recieved(self, ws, message):
        Discord.log.info(message)
        def run(*args):
            response = json.loads(message)
            self.s = response['s']
            if response['op'] == 10: #Case if initial connection to Discord webhook
                heartbeat_interval = response['d']['heartbeat_interval']
                self.__heartbeat(heartbeat_interval)
            elif response['op'] == 11:  pass #Acknowledgment code after heartbeat is sent. 
            elif response['t'] == 'READY': #Case if Bot is identified and status set to online 
                print(self.bot_name + ' is now online.') 
                self.session = response['d']['session_id']
            elif response['t'] == 'GUILD_CREATE': # Case where guild information is recieved. A guild object is created
                if response['d']['id'] not in self.guilds:
                    self.guilds[response['d']['id']] = Guild(response['d']['id'], self.token, response)
            elif response['t'] == 'INTERACTION_CREATE': #Case if a slash method is called by a user
                self.commands[response['d']['data']['name']](response) #Call the func ptr of the named command
            elif response['t'] == 'VOICE_STATE_UPDATE': #Case if a user joins/leaves voice channel
                self.guilds[response['d']['guild_id']].update_user(response)
            elif response['op'] == 7: #Case if discord requests that the websocket be closed and a new one opened
                Discord.log.info('Attempting reconnect')
                print('Reconnect requested.')
                #self.thread.daemon = True
                #self.thread.join()
                self.resume = True
                self.ws.close()
                self.open_connection()
            elif response['op'] == 1: #Case if discord requests a heartbeat be sent immediately
                self.heartbeat_requested = True

        self.thread = threading.Thread(target=run)
        self.thread.start() #Respond to events on seperate thread to handle mutliple with extended queue times.

    def open_connection(self):
        #Get gateway
        response = http.request('get', Discord.API_URL, '/gateway/bot', None, self.auth_header)

        #Open websocket connection
        self.ws = websocket.WebSocketApp(response['url'], 
                                    on_open=self.__connection_opened, 
                                    on_close=self.__connection_closed, 
                                    on_message=self.__message_recieved, 
                                    on_error=self.__error_recieved)
        Discord.log.info('Connection Opened')
        self.ws.run_forever()

    def __resume(self):
        def run():
            logging.info('Resume request sent')
            payload = {'op': 6, 'd': {'token': self.token, 'session_id': self.session, 'seq': self.s}}
            self.ws.send(data=json.dumps(payload), opcode=1)
        threading.Thread(target=run).start()

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
                http.request('post', Discord.API_URL, '/v8/applications/{}/commands'.format(self.client_id), command, self.auth_header)
            return
        return reg

    def reply(self, interaction, message, secret_reply=None):
        '''Replies to the chat where the interaction object was sent'''
        def run():
            endpoint = '/interactions/{}/{}/callback'.format(interaction['d']['id'], interaction['d']['token'])
            msg_data = {'type': 4, 'data': {'content': message}}
            
            #Flag 64 indicates only user who invoked interaction can see the response
            if secret_reply == True:
                msg_data['data']['flags'] = 64

            http.request('post', Discord.API_URL, endpoint, msg_data, self.auth_header)
        threading.Thread(target=run).start()

    def edit_interaction(self, interaction, new_message, secret_reply=None):
        '''Edits an existing interaction response message in the chat'''
        def run():
            endpoint = '/v8/webhooks/{}/{}/messages/@original'.format(self.client_id, interaction['d']['token'])
            msg_data = {'content': new_message}
            
            #Flag 64 indicates only user who invoked interaction can see the response
            if secret_reply == True:
                msg_data['data']['flags'] = 64

            http.request('patch', Discord.API_URL, endpoint, msg_data, self.auth_header)
        threading.Thread(target=run).start()

    def user_connected(self, guild_id, user_id):
        users = self.guilds[guild_id].users_connected
        if user_id not in users:
            return False
        else:
            return users[user_id]

    def num_users_connected(self, guild_id):
        return len(self.guilds[guild_id].users_connected)

    def move_user(self, guild_id, user_id, channel):
        def run():
            endpoint = '/guilds/{}/members/{}'.format(guild_id, user_id)
            payload = {'channel_id': channel}
            print('Moving user {} to {}'.format(user_id, channel))
            http.request('patch', Discord.API_URL, endpoint, payload, self.auth_header)
        threading.Thread(target=run).start()
        
class Guild:

    def __init__(self, id, bot_token, guild_create):
        '''Param guild_create = json given on the GUILD_CREATE event by discord'''
        self.id = id

        self.users_connected = {}
        for user in guild_create['d']['voice_states']:
            channel = user['channel_id']
            self.users_connected[user['user_id']] = channel

    def update_user(self, response):
        '''Sets a users status to True/False (online/offline)'''
        user_id = response['d']['member']['user']['id']
        channel = response['d']['channel_id']

        if channel == None:
            self.users_connected[user_id] = False
        else:
            self.users_connected[user_id] = channel