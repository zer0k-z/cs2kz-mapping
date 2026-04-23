import requests
import zipfile
import os
import shutil
from pathlib import Path
import time
from common import get_cs2_path


def download_and_extract_metamod(cs2_dir: str):
    releases = requests.get("https://api.github.com/repos/alliedmodders/metamod-source/releases").json()
    prerelease = next(r for r in releases if r["prerelease"] and not r["draft"])
    asset = next(a for a in prerelease["assets"] if a["name"].endswith(".zip") and "windows" in a["name"].lower())
    archive_path = Path(asset["name"])

    print(f"Downloading Metamod from {asset['browser_download_url']}...")
    archive_path.write_bytes(requests.get(asset["browser_download_url"]).content)

    output_dir_path = Path(cs2_dir) / 'game' / 'csgo'
    with zipfile.ZipFile(archive_path, 'r') as zip_ref:
        zip_ref.extractall(output_dir_path)

    os.remove(archive_path)
    print(f"Metamod has been successfully extracted to {output_dir_path}.")

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

def modify_sdkenginetools(sdkenginetools_path):
    print(f"Modifying sdkenginetools.txt for Particle Editor support...")
    with open(sdkenginetools_path, 'r') as f:
        lines = f.readlines()

    modified_lines = []
    inside_pet = False
    skip = 0

    for line in lines:
        # Find start of "pet" block
        if 'm_Name = "pet"' in line:
            inside_pet = True

        # Find end of "pet" block
        if inside_pet and line.strip() == "},":
            inside_pet = False

        # If inside "pet" block and see m_ExcludeFromMods, skip this line and the next 3 lines
        if inside_pet and 'm_ExcludeFromMods =' in line:
            skip = 4
        if skip > 0:
            skip -= 1
        else:
            modified_lines.append(line)

    with open(sdkenginetools_path, 'w') as f:
        f.writelines(modified_lines)

def modify_assettypes_common(assettypes_common_path):
    print(f"Modifying assettypes_common.txt for Particle Asset support...")
    with open(assettypes_common_path, 'r') as f:
        lines = f.readlines()

    modified_lines = []
    inside_particle_asset = False
    skip = 0

    for line in lines:
        # Find start of particle_asset block
        if 'particle_asset =' in line:
            inside_particle_asset = True

        # Find end of particle_asset block
        if inside_particle_asset and line.strip() == "}":
            inside_particle_asset = False

        # If inside particle_asset block and see m_HideForRetailMods, skip this line and the next 3 lines
        if inside_particle_asset and 'm_HideForRetailMods =' in line:
            skip = 4
        if skip > 0:
            skip -= 1
        else:
            modified_lines.append(line)

    with open(assettypes_common_path, 'w') as f:
        f.writelines(modified_lines)

def modify_csgo_fgd(csgo_fgd_path):
    print(f"Modifying csgo.fgd for CSM support...")
    with open(csgo_fgd_path, 'r') as f:
        lines = f.readlines()

    # Find and remove CSM lines
    modified_lines = []
    skip = 0

    for line in lines:
        if 'numcascades(remove_key)' in line:
            skip = 12  # Skip this line and the next 11 lines
        if skip > 0:
            skip -= 1
        else:
            modified_lines.append(line)

    with open(csgo_fgd_path, 'w') as f:
        f.writelines(modified_lines)

path = get_cs2_path()
if path is None:
    print("Failed to get CS2 path.")
    exit(1)

print(f"Setting up CS2KZ in {path}...")
download_and_extract_metamod(path)
download_cs2kz(path)
try:
    setup_asset_bin(path)
    setup_metamod_content_path(path)
except Exception as e:
    print(f"Warning: Failed to setup asset bin or content path: {e}")
    print("This might be because mapping tools are probably not installed.")

# csgo.fgd
csgo_fgd_path = os.path.join(path, "game", "csgo", "csgo.fgd")
if os.path.exists(csgo_fgd_path):
    modify_csgo_fgd(csgo_fgd_path)
else:
    print(f"csgo.fgd not found at {csgo_fgd_path}, skipping modification.")

# assettypes_common.txt
assettypes_common_path = os.path.join(path, "game", "bin", "assettypes_common.txt")
if os.path.exists(assettypes_common_path):
    modify_assettypes_common(assettypes_common_path)
else:
    print(f"assettypes_common.txt not found at {assettypes_common_path}, skipping modification.")

# sdkenginetools.txt
sdkenginetools_path = os.path.join(path, "game", "bin", "sdkenginetools.txt")
if os.path.exists(sdkenginetools_path):
    modify_sdkenginetools(sdkenginetools_path)
else:
    print(f"sdkenginetools.txt not found at {sdkenginetools_path}, skipping modification.")

print("Setup complete, closing in 3 seconds...")
time.sleep(3)
