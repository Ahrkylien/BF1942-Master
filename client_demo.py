import json

from misc import *

#A script demonstrating how to retrieve data from the master server as client

ipList = getServerListFromMaster("master.bf1942.org")

print(json.dumps(ipList))

