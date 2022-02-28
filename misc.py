import socket

from encryption import enctype2_decoder,enctype2_encoder

#A few shared or miscellaneous functions

def logDebug(message):
    with open("log", 'a') as file:
        file.write("\n"+message)

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