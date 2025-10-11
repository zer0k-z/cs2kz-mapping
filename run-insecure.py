from common import *
if __name__ == '__main__':
    path = get_cs2_path()
    if path is None:
        print('Failed to get CS2 path. Closing in 3 seconds...')
        time.sleep(3)
        exit()

    cs2 = os.path.join(path, 'game', 'bin', 'win64', 'cs2.exe')
    print(f"Launching CS2 insecure instance from '{cs2}'...")
    process = subprocess.Popen([cs2, '-insecure'])