import datetime
import websocket
import requests
import json

class Discord:

    API_URL = 'https://discord.com/api'

    def __init__(self, bot_name, token):
        self.bot_name = bot_name
        self.token = token
        self.heartbeat_interval = -1
        websocket.enableTrace(True)

    def __request(self, type, url, endpoint, payload, headers):
        url = url + endpoint if endpoint != None else url

        if type == 'get':
            response = requests.get(url=url, params=payload, headers=headers)
        elif type == 'post':
            response = requests.post(url=url, params=payload, headers=headers)

        if response.status_code >= 400:
            print('Exited with error: {}, response body: {}'.format(response.status_code, response.json()))
            exit(1)
        else:
            return response.json()

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
        ws.send(data=payload, opcode=1)

    def __connection_closed(self, ws, close_status_code, close_msg):
        print('Connection closed with code: {}. Close message: {}'.format(close_status_code, close_msg))

    def __message_recieved(self, ws, message):
        response = json.loads(message)
        if response['op'] == 10:
            self.heartbeat_interval = response['d']['heartbeat_interval']
            s = response['s']
            #TODO: START HEARTBEATING
        elif response['op'] == 11: pass #Acknowledgment code after heartbeat is sent. No action required.
        elif response['t'] == 'READY': print(self.bot_name + ' is now online.') 


    def __error_recieved(self, ws, error):
        print('ERROR ' + str(error))

    def open_connection(self):
        #Get gateway
        headers = {'Authorization': 'Bot ' + self.token}
        response = self.__request('get', Discord.API_URL, '/gateway/bot', None, headers)

        #Open websocket connection
        ws = websocket.WebSocketApp(response['url'], 
                                    on_open=self.__connection_opened, 
                                    on_close=self.__connection_closed, 
                                    on_message=self.__message_recieved, 
                                    on_error=self.__error_recieved)
        try:
            ws.run_forever()
        except KeyboardInterrupt: print('here')
        
        #Exchange hearbeats with server
        '''
        response = json.loads(ws.recv())
        self.heartbeat_interval = response['d']['heartbeat_interval']
        s = response['s']
        timer_start = datetime.datetime.now()
        while 1:
            delta = (datetime.datetime.now() - timer_start).seconds * 1000 #millisecond duration since last ping
            print(str(delta) + ' ' + str(self.heartbeat_interval))
            if delta >= self.heartbeat_interval:
                print('here')
                payload = {'op': 1, 'd': s}
                ws.send(payload)
                response = ws.recv()
                s = response[s]
                
                #reset time
                time_start = datetime.datetime.now()
            '''



    
