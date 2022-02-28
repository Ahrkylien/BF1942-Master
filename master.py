import threading
import time

from client_master_thread import clientMasterThread
from server_master_thread import serverMasterThread
from management_thread import managementThread
from misc import logDebug

#The main/kern script of the master server that start all threads

logDebug("####### start of master #######")

client_master_thread = threading.Thread(target=clientMasterThread)
server_master_thread = threading.Thread(target=serverMasterThread)
management_thread = threading.Thread(target=managementThread)

client_master_thread.start()
server_master_thread.start()
management_thread.start()

while True:
    time.sleep(60*40000)