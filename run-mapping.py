
import time
from common import *
import os

def run_cs2(cs2_tools_path):
    # Run the program
    subprocess.run([cs2_tools_path, '-insecure', '-gpuraytracing'])

    while any(p.name() == 'cs2.exe' for p in psutil.process_iter(['name'])):
        time.sleep(1)

    if os.path.exists('steam_appid.txt'):
        os.remove('steam_appid.txt')

if __name__ == '__main__':
    path = get_cs2_path()
    if path is None:
        print('Failed to get CS2 path. Closing in 3 seconds...')
        time.sleep(3)
        exit()
    
    gameinfo_path, backup_path, core_gameinfo_path, core_backup_path = backup_files(path)
    
    modify_gameinfo(gameinfo_path, core_gameinfo_path)
    
    cs2_tools_path = os.path.join(path, 'game', 'bin', 'win64', 'csgocfg.exe')
    run_cs2(cs2_tools_path)
    
    restore_files(backup_path, gameinfo_path, core_backup_path, core_gameinfo_path)
