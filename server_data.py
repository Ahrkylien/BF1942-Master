from threading import Lock
import json
from datetime import datetime

# this module defines the shared memory between threads

# a 'server' is a dict with the folowing keys:
    # source
    # IP
    # queryPort
    # query
    # query_timestamp
    # heartbeat_timestamp

#server sort key function:
def server_key(server):
    keys = (
        -1*int(server['query']['numplayers']),
        server['source'] != 'Heartbeat',
        server['IP'],
    )
    return(keys)

class Servers:
    def __init__(self):
        self.server_list = []
        self.lock = Lock()
    
    def addQueryInfos(self, server_list_new_data, afterHeartbeat = False):
        self.lock.acquire()
        for server_new_data in server_list_new_data:
            server_old_data = None
            for server in self.server_list:
                if server['IP'] == server_new_data['IP'] and server['queryPort'] == server_new_data['queryPort']:
                    server_old_data = server
                    break
            if server_old_data == None:
                self.server_list.append(server_new_data)
            else:
                if server_old_data['heartbeat_timestamp'] != None and datetime.now().timestamp() - server_old_data['heartbeat_timestamp'] < 60*30:
                    server_old_data['source'] = 'Heartbeat' #just to be 100% sure that the source does not get overwritten by the management module
                else:
                    server_old_data['source'] = server_new_data['source']
                server_old_data['query'] = server_new_data['query']
                server_old_data['query_timestamp'] = server_new_data['query_timestamp']
                if afterHeartbeat:
                    server_old_data['heartbeat_timestamp'] = server_new_data['heartbeat_timestamp']
        #remove dead servers:
        for i in reversed(range(len(self.server_list))):
            if datetime.now().timestamp() - self.server_list[i]['query_timestamp'] > 60*30: # drop servers that didnt respond in 30 min
                self.server_list.pop(i)
        #sort the server list:
        self.server_list.sort(key=server_key)
        #store the server list:
        with open('server_list', 'w') as f:
            json.dump(self.server_list , f)
        self.lock.release()
    
    def getList(self):
        self.lock.acquire()
        server_list = self.server_list.copy()
        self.lock.release()
        return(server_list)
        
servers = Servers()