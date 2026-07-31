
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
    subprocess.run([os.path.join(cs2_tools_path, 'csgocfg.exe'), '-insecure', '-gpuraytracing'], creationflags=0x208, cwd=cs2_tools_path,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    stdin=subprocess.DEVNULL)
    # Wait for cs2.exe to launch.
    # If we wait for too long and cs2.exe doesn't launch, it might be because the user closed the tools window
    #  so we should probably exit instead of waiting indefinitely.
    start_time = time.time()
    print("Waiting for 'cs2.exe' to launch...")
    while True:
        if any((p.info.get('name') or '').lower() == 'cs2.exe' for p in psutil.process_iter(['name'])):
            break
        if time.time() - start_time > 2:
            print("cs2.exe did not launch within 2 seconds. Exiting early...")
            return False

    if os.path.exists('steam_appid.txt'):
        os.remove('steam_appid.txt')
    return True

def recover_gameinfo(path, relative_gi_path, backup_path, temp_path, label):
    # gameinfo.gi is only ever a symlink while cs2.exe is running under this tool.
    # If it's still a symlink here, a previous run crashed/was killed before it could
    # restore the original file, so we need to recover before touching backup/temp files.
    gi_path = os.path.join(path, relative_gi_path)
    if os.path.islink(gi_path):
        print(f"Detected leftover symlink at '{gi_path}' from an unclean previous run.")
        os.remove(gi_path)
        if os.path.isfile(backup_path):
            print(f"Restoring '{label}' from backup '{backup_path}'...")
            shutil.move(backup_path, gi_path)
        else:
            print(f"No valid backup found for '{label}'. Downloading a clean copy instead (same as verify.py)...")
            try:
                download_gameinfo_file(path, relative_gi_path)
            except Exception as e:
                print(f"Failed to download a clean copy of '{label}': {e}")
                print("Please run verify.py or verify integrity of game files via Steam, then try again.")
                time.sleep(5)
                exit()

    # Clean up any stale backup/temp files left over from a previous run.
    # Safe now: gi_path is confirmed to be a real file, not a symlink depending on them.
    if os.path.lexists(backup_path):
        print(f"Removing stale backup at '{backup_path}'...")
        os.remove(backup_path)
    if os.path.lexists(temp_path):
        print(f"Removing stale temp file at '{temp_path}'...")
        os.remove(temp_path)

if __name__ == '__main__':
    # Creating symlinks below requires admin rights unless Developer Mode is enabled,
    # which is why this can intermittently fail depending on the user's system. Relaunch elevated if needed.
    ensure_admin()

    path = get_cs2_path()
    if path is None:
        print('Failed to get CS2 path. Closing in 3 seconds...')
        time.sleep(3)
        exit()

    gameinfo_relative_path = os.path.join('game', 'csgo', 'gameinfo.gi')
    gameinfo_core_relative_path = os.path.join('game', 'csgo_core', 'gameinfo.gi')
    gameinfo_path = os.path.join(path, gameinfo_relative_path)
    gameinfo_core_path = os.path.join(path, gameinfo_core_relative_path)

    # Backup original gameinfo files
    backup_path = os.path.join(path, 'game', 'csgo', 'gameinfo_original.gi')
    backup_core_path = os.path.join(path, 'game', 'csgo_core', 'gameinfo_original.gi')
    temp_path = os.path.join(path, 'game', 'csgo', 'gameinfo_temp.gi')
    temp_core_path = os.path.join(path, 'game', 'csgo_core', 'gameinfo_temp.gi')

    recover_gameinfo(path, gameinfo_relative_path, backup_path, temp_path, 'csgo/gameinfo.gi')
    recover_gameinfo(path, gameinfo_core_relative_path, backup_core_path, temp_core_path, 'csgo_core/gameinfo.gi')

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
    if run_cs2(cs2_tools_path):
        wait_until_dll_loaded("cs2.exe", "cs2kz.dll")
        time.sleep(3)
    else:
        try:
            os.remove(temp_path)
            os.remove(temp_core_path)
        except OSError as e:
            print(f"Error occurred while removing temp files: {e}")
    # Restore original gameinfo files
    os.remove(gameinfo_path)
    os.remove(gameinfo_core_path)
    shutil.move(backup_path, gameinfo_path)
    shutil.move(backup_core_path, gameinfo_core_path)
    print('Closing in 3 seconds...')
    time.sleep(3)
