import os
import socketserver
import json

from misc import *

# TCP on port 28900 of the master
# m->c: \basic\\secure\fT9YlX
# c->m: \gamename\bfield1942\gamever\2\location\0\validate\kvbJMkWb\enctype\2\final\\queryid\1.1\
# c->m: \list\cmp\gamename\bfield1942\final\
# m->c: <encripted data>

def logUser(ip, packet):
    with open("users", 'a') as file:
        file.write("\n"+ip+packet)
        
def load_IP_port_list():
    ip_port_list = []
    with open('server_list', 'r') as f:
        server_list = json.load(f)
        for server in server_list:
            ip_port_list.append((server['IP'], server['queryPort']))
    return(ip_port_list)

class MyTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        s = self.request #socket connected to the client
        s.sendall(bytes('\\basic\\\\secure\\MASTER', 'utf-8'))
        packet = s.recv(1024).decode('utf-8')
        if not "final" in packet:
            packet += s.recv(1024).decode('utf-8')
        #ToDo: add timout and add secure/validate check
        IP_port_list = load_IP_port_list()
        DataOut = getBytesFromServerList(IP_port_list)
        s.sendall(DataOut)
        logUser(self.client_address[0], packet)

def clientMasterThread():
    logDebug("start c->m")
    s = socketserver.ThreadingTCPServer(('0.0.0.0', 28900), MyTCPHandler, False) # Do not automatically bind
    s.allow_reuse_address = True # Prevent 'cannot bind to address' errors on restart
    s.server_bind()     # Manually bind, to support allow_reuse_address
    s.server_activate() # (see above comment)
    s.serve_forever()

