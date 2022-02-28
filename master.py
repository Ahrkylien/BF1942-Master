import threading
import time
import json
import os

from client_master_thread import clientMasterThread
from server_master_thread import serverMasterThread
from management_thread import managementThread
from misc import logDebug

#The main/kern script of the master server that starts and maintains all threads

logDebug("####### start of master #######")

#prepare some files:
for filePath in ['server_list', 'server_list_backup', 'heartbeats']:
    if not os.path.isfile('heartbeats'):
        with open("heartbeats", 'w') as file:
            file.write("[]")
# for filePath in []:
    # if not os.path.isfile('heartbeats'):
        # with open("heartbeats", 'w') as file:
            # file.write("")

thread_targets = [
    clientMasterThread,
    serverMasterThread,
    managementThread,
]

threads = [threading.Thread(target=thread_target) for thread_target in thread_targets]
for thread in threads: thread.start()

while True:
    for i, thread in enumerate(threads):
        if not thread.is_alive():
            logDebug("thread crashed: "+thread.name)
            with open('heartbeats', 'w') as f:
                json.dump([] , f)
            thread = threading.Thread(target=thread_targets[i])
            thread.start()
            threads[i] = thread
    time.sleep(30)