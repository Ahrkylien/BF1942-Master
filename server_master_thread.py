import os
import socket
import socketserver
import json
from datetime import datetime

from misc import *

# UDP on port 27900 of the master
# s->m: \heartbeat\23000\gamename\bfield1942
# m->s: \secure\qU5PpF3a
# s->m: \validate\g3ubf4uANcoA\weight\10\final\\queryid\2.1

def logUser(ip, packet):
    with open("heartbeat_users", 'a') as file:
        file.write("\n"+ip+packet)
        
def addHeartBeatServer(ip, port):
    with open('heartbeats', 'r+') as f:
        server_list = json.load(f)
        current_timestamp = datetime.now().timestamp()
        for i in reversed(range(len(server_list))):
            server = server_list[i]
            if current_timestamp - server[2] > 60*60: # 1 hour
                server.pop(i)
        server_list.append((ip, port, current_timestamp))
        f.seek(0)
        json.dump(server_list , f)
        f.truncate()

class MyUDPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        s = self.request #socket connected to the client
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
            addHeartBeatServer(self.client_address[0], port)

def serverMasterThread():
    logDebug("start s_>m")
    s = socketserver.ThreadingUDPServer(('0.0.0.0', 27900), MyUDPHandler, False) # Do not automatically bind
    s.allow_reuse_address = True # Prevent 'cannot bind to address' errors on restart
    s.server_bind()     # Manually bind, to support allow_reuse_address
    s.server_activate() # (see above comment)
    s.serve_forever()

