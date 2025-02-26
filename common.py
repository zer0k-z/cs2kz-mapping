import time
import winreg
import os
import vdf
import subprocess
import shutil
import psutil

def get_steam_directory():
    """Get the Steam installation directory from the Windows Registry."""
    try:
        # Open the Steam key in the registry
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
            # Get the SteamPath value
            steam_path, _ = winreg.QueryValueEx(key, "SteamPath")
            return steam_path
    except FileNotFoundError:
        print("Steam is not installed or the registry key was not found.")
        return None

def find_cs2_library_path(libraryfolders_path):
    """Parse the libraryfolders.vdf file to get all library paths."""
    if not os.path.exists(libraryfolders_path):
        print(f"libraryfolders.vdf not found at {libraryfolders_path}")
        return []

    with open(libraryfolders_path, 'r', encoding='utf-8') as file:
        library_data = vdf.load(file)

    if 'libraryfolders' in library_data:
        for _, folder in library_data['libraryfolders'].items():
            if 'apps' in folder and '730' in folder['apps']:
                return folder['path']
    print("Failed to find CS2 library path.")
    return None

def get_cs2_path():
    steam_path = get_steam_directory()
    if steam_path is None:
        return None
    library_path = find_cs2_library_path(os.path.join(steam_path, "steamapps", "libraryfolders.vdf"))
    if library_path is None:
        return None
    with open(os.path.join(library_path, 'steamapps', 'appmanifest_730.acf'), 'r', encoding='utf-8') as file:
        return os.path.join(library_path, 'steamapps', 'common', vdf.load(file)['AppState']['installdir'])
    print("Failed to get CS2 path.")

def modify_gameinfo(gameinfo_path, core_gameinfo_path):
    with open(gameinfo_path, 'r') as f:
        lines = f.readlines()

    # Insert metamod into gameinfo config
    target_line = "			Game	csgo\n"
    new_line = "			Game	csgo/addons/metamod\n"
    modified_lines = []

    for line in lines:
        if line == target_line:
            modified_lines.append(new_line)
        modified_lines.append(line)

    with open(gameinfo_path, 'w') as f:
        f.writelines(modified_lines)


    with open(core_gameinfo_path, 'r') as f:
        other_file_lines = f.readlines()

    # Find and remove CustomNavBuild
    modified_lines = []
    skip = 0

    for line in other_file_lines:
        if 'CustomNavBuild' in line:
            skip = 5  # Skip this line and the next 4 lines
        if skip > 0:
            skip -= 1
        else:
            modified_lines.append(line)

    with open(core_gameinfo_path, 'w') as f:
        f.writelines(modified_lines)

def modify_gameinfo_p2p(gameinfo_path):
    
    modified_lines = []
    
    with open(gameinfo_path, 'r') as f:
        lines = f.readlines()

    for line in lines:
        if line == "		// Bandwidth control default: 300,000 Bps\n":
            modified_lines.append('		"net_p2p_listen_dedicated" "1"\n')
        elif line == "	GameInstructor\n":
            modified_lines.append('	NetworkSystem\n')
            modified_lines.append('	{\n')
            modified_lines.append('		"CreateListenSocketP2P" "2"\n')
            modified_lines.append('	}\n')
        modified_lines.append(line)

    with open(gameinfo_path, 'w') as f:
        f.writelines(modified_lines)



def backup_files(path):
    gameinfo_path = os.path.join(path, 'game', 'csgo', 'gameinfo.gi')
    backup_path = os.path.join(path, 'game', 'csgo', 'gameinfo.gi.bak')
    
    core_gameinfo_path = os.path.join(path, 'game', 'csgo_core', 'gameinfo.gi')
    core_backup_path = os.path.join(path, 'game', 'csgo_core', 'gameinfo.gi.bak')
    
    shutil.copyfile(gameinfo_path, backup_path)
    shutil.copyfile(core_gameinfo_path, core_backup_path)
    
    return gameinfo_path, backup_path, core_gameinfo_path, core_backup_path

def restore_files(backup_path, gameinfo_path, core_backup_path, core_gameinfo_path):
    shutil.move(backup_path, gameinfo_path)
    shutil.move(core_backup_path, core_gameinfo_path)