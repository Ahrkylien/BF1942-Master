# BF1942-Master server
A Battlefield 1942 Master server written in Python.
## Requirements:
- Python 3
- Open UDP port: 27900
- Open TCP port: 28900
## Usage:
- Run master.py with python3 (it doesn’t daemonize itself, so use something like nohup)
- If you are interested you can run the client_demo.py to see how to query the master
## ToDo:
- Add secure/validate check on in both client->master as server->master protocols
- Query servers based on current list and in sync with the heartbeat