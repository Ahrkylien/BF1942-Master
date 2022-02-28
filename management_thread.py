import os
import time
from datetime import datetime
import json
import socket
import select
import threading
from requests import get as requests_get

from misc import *

# create a master list with server stats based on the heartbeats + backup + GameTracker

#server sort key function:
def server_key(server):
    keys = (
        -1*int(server['query']['numplayers']) if server['alive'] else 1,
        server['source'] != 'heartBeat',
        server['IP'],
    )
    return(keys)

def getServerListFromGameTracker():
    URL_base = "https://www.gametracker.com/search/bf1942/?searchipp=50&sort=0&order=ASC&searchpge="
    servers = []
    try:
        for i in range(2): #ToDo: make a check on number of pages
            location = "delhi technological university"
            PARAMS = {'address':location}
            r = requests_get(url = URL_base+str(i), params = PARAMS)
            data = r.text
            # print(data)
            currentPointer = data.find("<table class=\"table_lst table_lst_srs\">")
            end_of_table = data.find("</table>", currentPointer)
            for j in range(51):
                if j == 0: continue
                start_of_tr = data.find("<tr>", currentPointer)
                currentPointer = data.find("</tr>", start_of_tr)
                #name
                start_of_name = data.find("<a  href=\"/server_info/", start_of_tr)
                if start_of_name == -1 or start_of_name > end_of_table: break
                start_of_name = data.find("\">", start_of_name)
                end_of_name = data.find("</a>", start_of_name)
                name = data[start_of_name+2:end_of_name].strip()
                #ip
                start_of_ip = data.find("<span class=\"ip\">", start_of_tr)
                end_of_ip = data.find("</span>", start_of_ip)
                ip = data[start_of_ip+len("<span class=\"ip\">"):end_of_ip].strip()
                #port
                start_of_port = data.find("<span class=\"port\">:", start_of_tr)
                end_of_port = data.find("</span>", start_of_port)
                port = int(data[start_of_port+len("<span class=\"port\">:"):end_of_port])
                #store
                servers.append((name, ip, port))
    except: pass
    return(servers)

def queryServer(ip, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #UDP
        s.setblocking(0)
        s.connect((ip, port))
        s.sendall(bytes("\\status\\", 'utf-8'))
        properties = {}
        for i in range(20): #max 20 packets
            ready = select.select([s], [], [], 3) #3 seconds timeout
            if ready[0]: dataBytes = s.recv(1024*16)
            else: return(None)
            dataList = dataBytes.decode("utf-8", errors='ignore').split("\\")
            dataList.pop(0)
            nrOfProperties = int(len(dataList)/2)
            for j in range(nrOfProperties):
                properties[dataList[j*2]] = dataList[j*2+1]
            if 'final' in properties:
                break
        s.close()
        if not 'gameId' in properties: return(None) #filter out BFV servers
        return(properties)
    except: return(None)


def addQueryInfo(server):
    query = queryServer(server['IP'], server['queryPort'])
    server['alive'] = query != None
    server['query'] = query if query != None else {}
    server['timestamp'] = datetime.now().timestamp()
 
def serverExists(serverList, IP, queryPort):
    for server in serverList:
        if server['IP'] == IP and server['queryPort'] == queryPort: return(True)
    return(False)

def managementThread():
    logDebug("start management")
    while True:
        #compose server list:
        server_list = []
        with open('heartbeats', 'r') as f:
            server_list_heartbeats = json.load(f)
            for server in server_list_heartbeats:
                if datetime.now().timestamp() - server[2] < 60*15:
                    if not serverExists(server_list, server[0], server[1]):
                        server_list.append({'IP' : server[0], "queryPort" : server[1], "source" : "heartBeat"})
        with open('server_list_backup', 'r') as f:
            server_list_static = json.load(f)
            for server in server_list_static:
                if not serverExists(server_list, server[0], server[1]):
                    server_list.append({'IP' : server[0], "queryPort" : server[1], "source" : "backup"})
        server_list_GameTracker = getServerListFromGameTracker()
        for server in server_list_GameTracker:
            if not serverExists(server_list, server[1], server[2]+8433):
                server_list.append({'IP' : server[1], "queryPort" : server[2]+8433, "source" : "GameTracker"})
        #query the servers in the list:
        query_treads = []
        for server in server_list:
            thread = threading.Thread(target=addQueryInfo, args=(server,))
            thread.start()
            query_treads.append(thread)
        for thread in query_treads: thread.join() #wait till all threads are done
        #sort the server list:
        server_list.sort(key=server_key)
        #store the server list:
        with open('server_list', 'w') as fout:
            json.dump(server_list , fout)
        # wait 4 minutes:
        time.sleep(60*4)



