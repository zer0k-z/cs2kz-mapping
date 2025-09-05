import os 
import time
import common
import urllib.request

BASE_URL = 'https://raw.githubusercontent.com/SteamDatabase/GameTracking-CS2/refs/heads/master/'
FILE_PATHS = ['game/csgo/gameinfo.gi', 'game/csgo_core/gameinfo.gi']  

print('Attempting to restore gameinfo files...')
path = common.get_cs2_path()
if path is None:
    print('Failed to get CS2 path.')
    exit()

# Download file from the file paths
for file_path in FILE_PATHS:
    url = BASE_URL + file_path
    print(f'Downloading {url}...')
    file = urllib.request.urlopen(url)
    if file.getcode() != 200:
        print(f'Failed to download {url}. ({file.getcode()})')
        continue
    
    with open(os.path.join(path, file_path), 'wb') as f:
        f.write(file.read())

print('Done! Closing in 3 seconds...')

# Sleep for 3 seconds before closing
time.sleep(3)

