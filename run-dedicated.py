from common import *

if __name__ == '__main__':
    path = get_cs2_path()
    if path is None:
        print('Failed to get CS2 path. Closing in 3 seconds...')
        time.sleep(3)
        exit()
    
    gameinfo_path, backup_path, core_gameinfo_path, core_backup_path = backup_files(path)
    
    modify_gameinfo(gameinfo_path, core_gameinfo_path)
    
    modify_gameinfo_p2p(gameinfo_path)
    
    cs2 = os.path.join(path, 'game', 'bin', 'win64', 'cs2.exe')
    process = subprocess.Popen([cs2, '-dedicated', '+map de_dust2', '-insecure'])
    process.wait()
    time.sleep(1)

    restore_files(backup_path, gameinfo_path, core_backup_path, core_gameinfo_path)
    try:
        if os.path.exists('steam_appid.txt'):
            os.remove('steam_appid.txt')
    except:
        pass