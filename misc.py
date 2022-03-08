import socket
import select

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