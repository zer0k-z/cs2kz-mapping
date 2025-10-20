import time
import os
import winreg
import vdf
import subprocess
import shutil
import psutil
import requests
import zipfile
from pathlib import Path
import urllib.request
import hashlib

def get_steam_directory():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
            steam_path, _ = winreg.QueryValueEx(key, "SteamPath")
            return steam_path
    except FileNotFoundError:
        print("Steam is not installed or the registry key was not found.")
        return None

def find_cs2_library_path(libraryfolders_path):
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

def modify_gameinfo(gameinfo_path, core_gameinfo_path):
    with open(gameinfo_path, 'r') as f:
        lines = f.readlines()

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

    modified_lines = []
    skip = 0

    for line in other_file_lines:
        if 'CustomNavBuild' in line:
            skip = 5
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

def get_latest_metamod_version():
    try:
        latest_mm_url = "https://mms.alliedmods.net/mmsdrop/2.0/mmsource-latest-windows"
        response = requests.get(latest_mm_url)
        response.raise_for_status()
        return response.text.strip()
    except:
        return None

def download_and_extract_metamod(cs2_dir: str):
    try:
        latest_mm_url = "https://mms.alliedmods.net/mmsdrop/2.0/mmsource-latest-windows"
        response = requests.get(latest_mm_url)
        response.raise_for_status()
        
        mm_download_url = f"https://mms.alliedmods.net/mmsdrop/2.0/{response.text}"
        archive_path = Path(os.getcwd()) / response.text

        print(f"Downloading Metamod from {mm_download_url}...")
        with requests.get(mm_download_url, stream=True) as r:
            r.raise_for_status()
            with open(archive_path, 'wb') as f:
                f.write(r.content)
        print("Download complete.")

        output_dir_path = Path(cs2_dir) / 'game' / 'csgo'
        print(f"Extracting {archive_path} to {cs2_dir}...")
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(output_dir_path)

        print(f"Removing temporary file: {archive_path}")
        os.remove(archive_path)

        print(f"Metamod has been successfully extracted to {output_dir_path}.")

    except requests.exceptions.RequestException as e:
        print(f"Error downloading Metamod: {e}")
    except zipfile.BadZipFile as e:
        print(f"Error extracting Metamod archive: {e}. Ensure the file is a valid ZIP archive.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def get_latest_cs2kz_version():
    try:
        response = requests.get("https://api.github.com/repos/KZGlobalTeam/cs2kz-metamod/releases/latest")
        if response.status_code == 200:
            return response.json().get('tag_name', '')
    except:
        pass
    return None

def get_mapping_api_hash():
    try:
        response = requests.get("https://raw.githubusercontent.com/KZGlobalTeam/cs2kz-metamod/refs/heads/master/mapping_api/game/csgo_core/csgo_internal.fgd")
        if response.status_code == 200:
            return hashlib.md5(response.content).hexdigest()
    except:
        pass
    return None

def download_cs2kz(cs2_dir: str):
    print(f"Downloading CS2KZ plugin...")
    response = requests.get("https://api.github.com/repos/KZGlobalTeam/cs2kz-metamod/releases/latest")
    if response.status_code != 200:
        raise Exception(f"Failed to fetch latest release: {response.status_code} - {response.text}")

    release_data = response.json()

    if "assets" not in release_data or len(release_data["assets"]) == 0:
        raise Exception("No assets found in the latest release.")
    
    for asset in release_data["assets"]:
        if asset["name"] == "cs2kz-windows-master.zip":
            asset_url = asset["browser_download_url"]

            response = requests.get(asset_url)
            if response.status_code != 200:
                raise Exception(f"Failed to download asset: {response.status_code} - {response.text}")

            with open(asset["name"], "wb") as file:
                file.write(response.content)
                path = os.path.join(cs2_dir, "game", "csgo")
                with zipfile.ZipFile(asset["name"], "r") as zip_ref:
                    zip_ref.extractall(path)
                print(f"CS2KZ unzipped to '{path}'")
            os.remove(asset["name"])
            break

    print(f"Downloading mapping API FGD...")
    response = requests.get("https://raw.githubusercontent.com/KZGlobalTeam/cs2kz-metamod/refs/heads/master/mapping_api/game/csgo_core/csgo_internal.fgd")
    if response.status_code != 200:
        raise Exception(f"Failed to fetch mapping API FGD: {response.status_code} - {response.text}")
    path = os.path.join(cs2_dir, "game", "csgo_core")
    if not os.path.exists(path):
        os.makedirs(path)
    with open(os.path.join(path, "csgo_internal.fgd"), "wb") as file:
        file.write(response.content)

def setup_asset_bin(cs2_dir: str):
    print(f"Setting up asset bin...")
    shutil.copyfile(os.path.join(cs2_dir, "game", "csgo", "readonly_tools_asset_info.bin"), os.path.join(cs2_dir, "game", "csgo", "addons", "metamod", "readonly_tools_asset_info.bin"))

def setup_metamod_content_path(path: str):
    print('Creating necessary folder for hammer...')
    os.makedirs(os.path.join(path, 'content', 'csgo', 'addons', 'metamod'), exist_ok = True)

def load_versions(cs2_dir: str):
    version_file = os.path.join(os.getenv('TEMP'), '.cs2kz_versions.txt')
    versions = {}
    if os.path.exists(version_file):
        with open(version_file, 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    versions[key] = value
    return versions

def save_versions(cs2_dir: str, versions: dict):
    version_file = os.path.join(os.getenv('TEMP'), '.cs2kz_versions.txt')
    with open(version_file, 'w') as f:
        for key, value in versions.items():
            f.write(f"{key}={value}\n")

def check_setup_needed(cs2_dir: str):
    version_file = os.path.join(os.getenv('TEMP'), '.cs2kz_versions.txt')
    print(f"Checking versions at: {version_file}")
    
    metamod_path = os.path.join(cs2_dir, 'game', 'csgo', 'addons', 'metamod')
    cs2kz_path = os.path.join(cs2_dir, 'game', 'csgo', 'addons', 'cs2kz')
    
    if not os.path.exists(metamod_path) or not os.path.exists(cs2kz_path):
        return True
    
    current_versions = load_versions(cs2_dir)
    
    latest_metamod = get_latest_metamod_version()
    latest_cs2kz = get_latest_cs2kz_version()
    latest_mapping_api = get_mapping_api_hash()
    
    if latest_metamod and current_versions.get('metamod') != latest_metamod:
        return True
    if latest_cs2kz and current_versions.get('cs2kz') != latest_cs2kz:
        return True
    if latest_mapping_api and current_versions.get('mapping_api') != latest_mapping_api:
        return True
    
    return False

def run_setup(cs2_dir: str):
    print(f"Setting up CS2KZ in {cs2_dir}...")
    download_and_extract_metamod(cs2_dir)
    download_cs2kz(cs2_dir)
    try:
        setup_asset_bin(cs2_dir)
        setup_metamod_content_path(cs2_dir)
    except Exception as e:
        print(f"Warning: Failed to setup asset bin or content path: {e}")
        print("This might be because mapping tools are probably not installed.")
    
    versions = {
        'metamod': get_latest_metamod_version() or 'unknown',
        'cs2kz': get_latest_cs2kz_version() or 'unknown',
        'mapping_api': get_mapping_api_hash() or 'unknown'
    }
    save_versions(cs2_dir, versions)
    print("Setup complete.")

def run_listen_server(cs2_path):
    print(f"Launching CS2 listen server from '{cs2_path}'...")
    process = subprocess.Popen([cs2_path, '-insecure'])
    
    while any(p.name() == 'cs2.exe' for p in psutil.process_iter(['name'])):
        time.sleep(1)
    
    try:
        if os.path.exists('steam_appid.txt'):
            os.remove('steam_appid.txt')
    except:
        pass

def verify_gameinfo(path):
    BASE_URL = 'https://raw.githubusercontent.com/SteamDatabase/GameTracking-CS2/refs/heads/master/'
    FILE_PATHS = ['game/csgo/gameinfo.gi', 'game/csgo_core/gameinfo.gi']
    
    print('Restoring gameinfo files...')
    for file_path in FILE_PATHS:
        url = BASE_URL + file_path
        print(f'Downloading {url}...')
        file = urllib.request.urlopen(url)
        if file.getcode() != 200:
            print(f'Failed to download {url}. ({file.getcode()})')
            continue

        content = file.read().decode('utf-8').replace('\n', '\r\n')
        out_path = os.path.join(path, file_path)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, 'wb') as f:
            f.write(content.encode('utf-8'))
    print('Gameinfo files restored.')

if __name__ == '__main__':
    path = get_cs2_path()
    if path is None:
        print('Failed to get CS2 path. Closing in 3 seconds...')
        time.sleep(3)
        exit()
    
    if check_setup_needed(path):
        print("Setup needed - running installation...")
        run_setup(path)
    else:
        print("Setup check passed - files up to date.")
    
    gameinfo_path, backup_path, core_gameinfo_path, core_backup_path = backup_files(path)
    modify_gameinfo(gameinfo_path, core_gameinfo_path)
    modify_gameinfo_p2p(gameinfo_path)
    
    cs2_exe = os.path.join(path, 'game', 'bin', 'win64', 'cs2.exe')
    run_listen_server(cs2_exe)
    
    restore_files(backup_path, gameinfo_path, core_backup_path, core_gameinfo_path)
    verify_gameinfo(path)
    
    print('Done! Closing in 3 seconds...')
    time.sleep(3)