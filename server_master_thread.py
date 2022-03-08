import os
import socket
import socketserver
import json
from datetime import datetime

from misc import *
from server_data import servers

# UDP on port 27900 of the master
# s->m: \heartbeat\23000\gamename\bfield1942
# m->s: \secure\qU5PpF3a
# s->m: \validate\g3ubf4uANcoA\weight\10\final\\queryid\2.1

def logUser(ip, packet):
    with open("heartbeat_users", 'a') as file:
        file.write("\n"+ip+packet)

def logUserDebug(ip, packet):
    with open("heartbeat_users_debug", 'a') as file:
        file.write("\n"+ip+packet)
        
class MyUDPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        packet = self.request[0].decode('utf-8')
        socket = self.request[1]
        if "heartbeat" in packet:
            start = packet.find("\\heartbeat\\")
            end = packet.find("\\gamename", start)
            port = int(packet[start+len("\\heartbeat\\"):end])
            #ToDo add secure/validate check
            # socket.sendto("\secure\bfMASTER".encode('utf-8'), self.client_address)
            # packet += socket.recv(1024).decode('utf-8')
            logUser(self.client_address[0], packet)
            query = queryServer(self.client_address[0], port)
            if query != None:
                server = {
                    'source': 'Heartbeat',
                    'IP': self.client_address[0],
                    'queryPort': port,
                    'query': query,
                    'query_timestamp': datetime.now().timestamp(),
                    'heartbeat_timestamp': datetime.now().timestamp(),
                }
                servers.addQueryInfos([server], True)
        else:
            logUserDebug(self.client_address[0], packet)

def serverMasterThread():
    logDebug("start s->m")
    s = socketserver.ThreadingUDPServer(('0.0.0.0', 27900), MyUDPHandler, False) # Do not automatically bind
    s.allow_reuse_address = True # Prevent 'cannot bind to address' errors on restart
    s.server_bind()     # Manually bind, to support allow_reuse_address
    s.server_activate() # (see above comment)
    s.serve_forever()

