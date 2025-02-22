import requests
import zipfile
import os
import shutil
from pathlib import Path
import time
from common import get_cs2_path


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

path = get_cs2_path()
if path is None:
    print("Failed to get CS2 path.")
    exit(1)

print(f"Setting up CS2KZ in {path}...")
download_and_extract_metamod(path)
download_cs2kz(path)
setup_asset_bin(path)

print("Setup complete, closing in 3 seconds...")
time.sleep(3)
