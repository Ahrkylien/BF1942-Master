import os
import time
from datetime import datetime
import json
import threading
from requests import get as requests_get

from misc import *
from server_data import servers

# create a master list with server stats based on the heartbeats + backup + GameTracker

def getServerListFromGameTracker():
    URL_base = "https://www.gametracker.com/search/bf1942/?searchipp=50&sort=0&order=ASC&searchpge="
    servers = []
    try:
        for i in range(3): #ToDo: make a check on number of pages
            location = "delhi technological university"
            PARAMS = {'address':location}
            r = requests_get(url = URL_base+str(1+i), params = PARAMS)
            data = r.text
            # print(data)
            currentPointer = data.find("<table class=\"table_lst table_lst_srs\">")
            end_of_table = data.find("</table>", currentPointer)
            for j in range(51):
                start_of_tr = data.find("<tr>", currentPointer)
                currentPointer = data.find("</tr>", start_of_tr)
                if j == 0: continue
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
            if '<span>NEXT</span>' in data: #grayed out next button
                break
    except: pass
    return(servers)

def addQueryInfo(server):
    query = queryServer(server['IP'], server['queryPort'])
    server['query'] = query
    server['query_timestamp'] = datetime.now().timestamp()
    server['heartbeat_timestamp'] = None
 
def managementThread():
    logDebug("start management")
    while True:
        #compose server list:
        current_server_list = servers.getList()
        server_list = []
        #servers with heartbeats:
        for server in current_server_list:
            if server['source'] == 'heartBeat':
                if datetime.now().timestamp() - server['heartbeat_timestamp'] < 60*15:
                    if not serverExists(server_list, server[0], server[1]):
                        server_list.append({'IP' : server[0], "queryPort" : server[1], "source" : "heartBeat"})
        #servers from backup:
        with open('server_list_backup', 'r') as f:
            server_list_static = json.load(f)
            for server in server_list_static:
                if not serverExists(server_list, server[0], server[1]):
                    server_list.append({'IP' : server[0], "queryPort" : server[1], "source" : "backup"})
        #servers from GameTracker:
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
        #remove servers that didnt respond:
        for i in reversed(range(len(server_list))):
            if server_list[i]['query'] == None:
                server_list.pop(i)
        #add the server list to the data module:
        servers.addQueryInfos(server_list)
        # wait 4 minutes:
        time.sleep(60*4)



