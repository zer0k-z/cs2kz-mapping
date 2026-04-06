
import time
from common import *
import os
import shutil

def wait_until_dll_loaded(exe_name: str, dll_name: str) -> bool:
    print(f"Waiting for '{dll_name}' to be loaded by '{exe_name}'...")
    while True:
        for proc in psutil.process_iter(["pid", "name"]):
            if exe_name.lower() not in proc.info["name"].lower():
                continue
            try:
                for module in proc.memory_maps():
                    if dll_name.lower() in module.path.lower():
                        print(f"'{dll_name}' is loaded in '{exe_name}' (PID {proc.pid}).")
                        return True
            except psutil.AccessDenied:
                continue
            except psutil.NoSuchProcess:
                return False

        time.sleep(0.2)

def run_cs2(cs2_tools_path):
    # Launch tools and wait until cs2.exe is observed before returning.
    subprocess.Popen([os.path.join(cs2_tools_path, 'csgocfg.exe'), '-insecure', '-gpuraytracing'], creationflags=0x208, cwd=cs2_tools_path,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    stdin=subprocess.DEVNULL)
    # Wait for cs2.exe to launch.
    while True:
        if any((p.info.get('name') or '').lower() == 'cs2.exe' for p in psutil.process_iter(['name'])):
            break

    if os.path.exists('steam_appid.txt'):
        os.remove('steam_appid.txt')

if __name__ == '__main__':
    path = get_cs2_path()
    if path is None:
        print('Failed to get CS2 path. Closing in 3 seconds...')
        time.sleep(3)
        exit()
    
    gameinfo_path = os.path.join(path, 'game', 'csgo', 'gameinfo.gi')
    gameinfo_core_path = os.path.join(path, 'game', 'csgo_core', 'gameinfo.gi')

    # Backup original gameinfo files
    backup_path = os.path.join(path, 'game', 'csgo', 'gameinfo_original.gi')
    backup_core_path = os.path.join(path, 'game', 'csgo_core', 'gameinfo_original.gi')
    temp_path = os.path.join(path, 'game', 'csgo', 'gameinfo_temp.gi')
    temp_core_path = os.path.join(path, 'game', 'csgo_core', 'gameinfo_temp.gi')
    if os.path.exists(backup_path):
        os.remove(backup_path)
    if os.path.exists(backup_core_path):
        os.remove(backup_core_path)
    if os.path.exists(temp_path):
        os.remove(temp_path)
    if os.path.exists(temp_core_path):
        os.remove(temp_core_path)
    print(f"Backing up original gameinfo from '{gameinfo_path}' to '{backup_path}'...")
    shutil.move(gameinfo_path, backup_path)
    print(f"Backing up original gameinfo from '{gameinfo_core_path}' to '{backup_core_path}'...")
    shutil.move(gameinfo_core_path, backup_core_path)
    # Create temp gameinfos and apply modifications to them instead of the original ones to avoid issues with cs2.exe locking the files.
    print(f"Creating temp gameinfo at '{temp_path}' from backup '{backup_path}'...")
    shutil.copyfile(backup_path, temp_path)
    print(f"Creating temp gameinfo at '{temp_core_path}' from backup '{backup_core_path}'...")
    shutil.copyfile(backup_core_path, temp_core_path)
    
    
    # Create a symlink from the temp gameinfo to the original location so that when cs2.exe locks the file, it locks the temp one instead of the original one.
    os.symlink(temp_path, gameinfo_path, target_is_directory=False)
    os.symlink(temp_core_path, gameinfo_core_path, target_is_directory=False)
    modify_gameinfo(gameinfo_path, gameinfo_core_path)


    cs2_tools_path = os.path.join(path, 'game', 'bin', 'win64')
    print(f"Launching CS2 tools from '{cs2_tools_path}'...")
    run_cs2(cs2_tools_path)
    wait_until_dll_loaded("cs2.exe", "cs2kz.dll")
    time.sleep(3)

    # Restore original gameinfo files
    os.remove(gameinfo_path)
    os.remove(gameinfo_core_path)
    shutil.move(backup_path, gameinfo_path)
    shutil.move(backup_core_path, gameinfo_core_path)
    print('Done! Closing in 3 seconds...')
    time.sleep(3)
