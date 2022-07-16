import socket
import select
import traceback

from encryption import enctype2_decoder,enctype2_encoder

#A few shared or miscellaneous functions

def logDebug(debugStr):
    with open("debug", 'a') as file:
        file.write("\n"+debugStr)

def parseIPList(listRaw):
    list=[]
    i=0
    while i+5 < len(listRaw):
        list.append((str(listRaw[i])+'.'+str(listRaw[i+1])+'.'+str(listRaw[i+2])+'.'+str(listRaw[i+3]), listRaw[i+4]*256+listRaw[i+5]))
        i+=6
    return(list)

def packIPList(list):
    listRaw=[]
    for IP in list:
        ip = IP[0].split('.')
        for nr in ip:
            listRaw.append(int(nr))
        listRaw.append(IP[1]>>8)
        listRaw.append(IP[1]&0xff)
    return(listRaw)
    
def getServerListFromMaster(IP):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((IP, 28900))
    data = s.recv(1024)
    s.sendall(bytes('\\gamename\\bfield1942\\gamever\\2\\location\\0\\validate\\bfMaster\\enctype\\2\\final\\\\queryid\\1.1\\', 'utf-8'))
    s.sendall(bytes('\\list\\cmp\\gamename\\bfield1942\\final\\', 'utf-8'))
    dataBytes = s.recv(1024)
    s.close()
    dataDecoded = enctype2_decoder("HpWx9z",list(dataBytes))
    return(parseIPList(dataDecoded))
    
def getBytesFromServerList(ip_port_list):
    data = packIPList(ip_port_list)
    dataOutEnc = enctype2_encoder("HpWx9z",data)
    return(bytes(dataOutEnc))

def queryServer(ip, port):
    unprintableChars = list(range(0, 31+1)) + list(range(127, 159+1))
    latinChars = list(range(65, 90+1)) + list(range(97, 122+1))
    non_latinChars = list(range(192, 255+1)) #like cyrillic
    player_properties = ['playername','keyhash','team','score','kills','deaths','ping']
    int_properties = ['allied_team_ratio','averageFPS','axis_team_ratio','bandwidth_choke_limit','content_check',
        'cpu','dedicated','hostport','maxplayers','name_tag_distance','name_tag_distance_scope','number_of_rounds',
        'numplayers','reservedslots','roundTime','roundTimeRemain','status','tickets1','tickets2','time_limit','location']
    float_properties = [] # maybe: averageFPS, bandwidth_choke_limit, name_tag_distance, name_tag_distance_scope
    bool_properties = ['password','sv_punkbuster','hit_indicator','free_camera','external_view', 'auto_balance_teams','allow_nose_cam']
    list_properties = ['unpure_mods']
    str_properties = ['gamename','gamever','gameId','gamemode','gametype','hostname','mapId','mapname','version','active_mods','kickback',
        'kickback_on_splash','soldier_friendly_fire','soldier_friendly_fire_on_splash','spawn_delay','spawn_wave_time','ticket_ratio',
        'tk_mode','vehicle_friendly_fire','vehicle_friendly_fire_on_splash','teamname_0','teamname_1','game_start_delay','language']
    
    def bf1942_bytes_to_str(bf1942_bytes):
        # removeUnprintableBytes:
        bf1942_bytearray = bytearray(bf1942_bytes)
        for i, byte in enumerate(bf1942_bytearray):
            if byte in unprintableChars:
                bf1942_bytearray[i] = 0x20 # space
        return(bf1942_bytearray.decode("cp1252", errors='ignore'))
    
    def apply_predicted_bf1942_encoding_to_str(bf1942_str):
        # guesse if chars are non cp1251 chars:
        bf1942_bytearray = bytearray(bf1942_str, 'cp1252')
        num_latinChars = len([1 for byte in bf1942_bytearray if byte in latinChars])
        num_non_latinCharss = len([1 for byte in bf1942_bytearray if byte in non_latinChars])
        if num_non_latinCharss + num_latinChars != 0:
            if num_non_latinCharss/(num_non_latinCharss + num_latinChars) >= 0.8:
                return(bf1942_bytearray.decode("cp1251", errors='ignore'))
        return(bf1942_bytearray.decode("cp1252", errors='ignore'))
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #UDP
        s.setblocking(0)
        s.connect((ip, port))
        s.sendall(bytes("\\status\\", 'utf-8'))
        properties = {}
        final = False
        for i in range(20): #max 20 packets
            ready = select.select([s], [], [], 3) #3 seconds timeout
            if ready[0]:
                try:
                    dataBytes = s.recv(1024*16)
                except: return(None)
            else: return(None)
            dataList = bf1942_bytes_to_str(dataBytes).split("\\")
            dataList.pop(0)
            nrOfProperties = int(len(dataList)/2)
            for j in range(nrOfProperties):
                properties[dataList[j*2]] = dataList[j*2+1]
            if 'final' in properties:
                final = int(properties['queryid'].split(".")[1]) #number of expected packets
            if final: # if the final packet and the expected number of packets have been received
                if i == final - 1:
                    break
        s.close()
        
        if not 'gameId' in properties: return(None) #filter out BFV servers
        
        players = []
        for i in range(int(properties['numplayers'])):
            players.append({player_property: properties[player_property+'_'+str(i)] for player_property in player_properties if player_property+'_'+str(i) in properties})
        for player in players:
            player['playername'] = apply_predicted_bf1942_encoding_to_str(player['playername'])
        
        for property_name in list(properties.keys()):
            if property_name.startswith(tuple(player_properties)):
                del properties[property_name]
        del properties['final']
        del properties['queryid']
        
        for property_name in properties:
            if property_name in int_properties:
                try:
                    properties[property_name] = int(properties[property_name])
                except: pass
            elif property_name in float_properties:
                try:
                    properties[property_name] = float(properties[property_name])
                except: pass
            elif property_name in bool_properties:
                properties[property_name] = properties[property_name] in ['on', 'yes', '1']
            elif property_name in list_properties:
                properties[property_name] = [item.strip() for item in properties[property_name].split(',') if len(item) > 0]
            elif not property_name in str_properties:
                logDebug("query: "+ip+": unknown property: "+property_name+": "+properties[property_name])
        for player in players:
            for player_property_name in player:
                if not player_property_name in ['playername', 'keyhash']:
                    player[player_property_name] = int(player[player_property_name])
            
        properties['players'] = players
        
        return(properties)
    except Exception as e:
        logDebug("query: "+ip+": "+str(e))
        logDebug(str(traceback.print_exc()))
        try: logDebug(bf1942_bytes_to_str(dataBytes))
        except: pass
        return(None)