import json, sys, os, subprocess
import requests
from utils.common import colored_text, escape_windows_path, GREEN, RED

def set_up():
    if os.path.exists(os.path.join(sys.path[0], 'config.json')):
        return

    update_lua_script()

    print(colored_text([[GREEN, 'Running setup!\n']]))
    anime_folder = input('Anime folder path: ')
    anilist_user = input('AniList username: ')
    mpv_path = get_mpv_path()
    config = {
        'anime_folder': anime_folder,
        'anilist_user': anilist_user,
        'mpv_path': mpv_path,
        'token': ''
    }
    save_config(config)

    print(colored_text([
        [None, '\nPlease manually enter your '],
        [GREEN, "'token' "],
        [None, 'into '],
        [GREEN, "'config.json'\n"],
        [None, 'To get your token, visit '],
        [GREEN, 'https://anilist.co/api/v2/oauth/authorize?client_id=7723&response_type=token']

    ]))
    input('\nPress enter when done.')

    print(colored_text([
        [None, 'Please copy '],
        [GREEN, "'anilist.lua' "],
        [None, 'into your mpv script folder.']
    ]))
    input('\nPress enter when done.')
    print()

def get_mpv_path():
    is_windows = os.name == 'nt'
    try:
        if is_windows:
            mpv_path = subprocess.check_output(['where', 'mpv']).decode("utf-8").splitlines()[0]
        else:
            mpv_path = subprocess.check_output(['which', 'mpv']).decode("utf-8").splitlines()[0]
        print(colored_text([[GREEN, f'\nFound mpv path: {mpv_path}']]))
    except:
        print(colored_text([[RED, '\nCould not find mpv in your PATH']]))
        if is_windows:
            example = 'ex. C:\\Program Files\\mpv\\mpv.exe'
        else:
            example = 'ex. /usr/local/bin/mpv'
        mpv_path = input(f'\nPath to mpv ({example}): ')

    if is_windows:
        mpv_path = escape_windows_path(mpv_path)

    return mpv_path

def update_lua_script():
    if not os.path.exists(os.path.join(sys.path[0], 'anilist.lua')):
        response = requests.get("https://raw.githubusercontent.com/hotsno/keroro/main/anilist.lua")
        if response.status_code == 200:
            with open(os.path.join(sys.path[0], 'anilist.lua'), 'w') as file:
                file.write(response.text)
        else:
            print(f"Failed to fetch latest lua script: {response.status_code}")
            return None

    python_path = sys.executable
    update_path = os.path.join(sys.path[0], 'utils', 'update_progress.py')
    update_presence_path = os.path.join(sys.path[0], 'presence', 'update_presence.py')
    run_presence_path = os.path.join(sys.path[0], 'presence', 'run_presence.py')

    is_windows = os.name == 'nt'
    if is_windows:
        python_path = escape_windows_path(python_path)
        update_path = escape_windows_path(update_path)
        update_presence_path = escape_windows_path(update_presence_path)
        run_presence_path = escape_windows_path(run_presence_path)

    to_prepend = f'local python_path = "{python_path}"\nlocal update_path = "{update_path}"\nlocal update_presence_path = "{update_presence_path}"\nlocal run_presence_path = "{run_presence_path}"\n'
    with open(os.path.join(sys.path[0], 'anilist.lua'), 'r+') as f:
        content = f.read()
        f.seek(0, 0)
        f.write(to_prepend + '\n' + content)

def get_config():
    with open(os.path.join(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'config.json')) as f:
        config = json.load(f)
        return config

def save_config(config):
    with open(os.path.join(sys.path[0], 'config.json'), 'w') as f:
        f.seek(0)
        json.dump(config, f, indent=4)
        f.truncate()