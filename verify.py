import os 
from steam.client import SteamClient 
from steam.client.cdn import CDNClient
import time
import common
import steam.protobufs.steammessages_contentsystem_pb2

APP_ID = 730 
FILE_PATHS = ['game/csgo/gameinfo.gi', 'game/csgo_core/gameinfo.gi']  

print('Attempting to restore gameinfo files...')
path = common.get_cs2_path()
if path is None:
    print('Failed to get CS2 path. Closing in 3 seconds...')
    time.sleep(3)
    exit()
    
# Initialize Steam client
print('Initializing Steam client...')
client = SteamClient()
client.anonymous_login()

# Wait for login to complete
client.wait_event('logged_on', timeout=10)

# Initialize CDN depot
mycdn = CDNClient(client)
print('Downloading gameinfo files...')
for gameinfo in FILE_PATHS:
    for file in mycdn.iter_files(730, gameinfo):
        with open(os.path.join(path, gameinfo), 'wb') as f:
            f.write(file.read())
        
# Disconnect from Steam
client.disconnect()
print('Done! Closing in 3 seconds...')

# Sleep for 3 seconds before closing
time.sleep(3)

