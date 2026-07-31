import time
import common

print('Attempting to restore gameinfo files...')
path = common.get_cs2_path()
if path is None:
    print('Failed to get CS2 path.')
    exit()

common.download_gameinfo_files(path)

print('Done! Closing in 3 seconds...')

# Sleep for 3 seconds before closing
time.sleep(3)
