import subprocess
import time
import shutil
import common
import os
import psutil

path = common.get_cs2_path()
if path is None:
	print('Failed to get CS2 path. Closing in 3 seconds...')
	time.sleep(3)
	exit()
# Paths
gameinfo_path = os.path.join(path, 'game', 'csgo', 'gameinfo.gi')
backup_path = os.path.join(path, 'game', 'csgo', 'gameinfo.gi.bak')

core_gameinfo_path = os.path.join(path, 'game', 'csgo_core', 'gameinfo.gi')
core_backup_path = os.path.join(path, 'game', 'csgo_core', 'gameinfo.gi.bak')

cs2_tools_path = os.path.join(path, 'game', 'bin', 'win64', 'csgocfg.exe')

shutil.copyfile(gameinfo_path, backup_path)
shutil.copyfile(core_gameinfo_path, core_backup_path)

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
        skip = 4  # Skip this line and the next 4 lines
    if skip > 0:
        skip -= 1
    else:
        modified_lines.append(line)

# Run the program
process = subprocess.run([cs2_tools_path, '-insecure', '-gpuraytracing'])

while any(p.name() == 'cs2.exe' for p in psutil.process_iter(['name'])):
    time.sleep(1)

if os.path.exists('steam_appid.txt'):
    os.remove('steam_appid.txt')
shutil.move(backup_path, gameinfo_path)
shutil.move(core_backup_path, core_gameinfo_path)