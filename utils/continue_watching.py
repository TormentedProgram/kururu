import subprocess, os
import utils.anilist_requests, utils.mapper, utils.offset, utils.config
from utils.common import colored_text, GREEN, CYAN, YELLOW, RED, BLUE
import re
import json 
import sys
import requests
from concurrent.futures import ThreadPoolExecutor, TimeoutError

def sync_with_anilist(online=True):
    watchlist = utils.anilist_requests.get_watching_list(1, online)
    folder_map = utils.mapper.get_map()
    for _, o in folder_map.items():
        anilist_id = o['anilist_id']
        if anilist_id in watchlist:
            o['status'] = watchlist[anilist_id]['status'] or "UNLISTED"
            anilist_progress = watchlist[anilist_id]['progress'] or 0
            if 'progress' in o and o['progress'] > anilist_progress:
                # TODO: Add colors to this (way too lazy to do this rn)
                print(f'\nMismatched progress for {watchlist[anilist_id]["title"]}!\n')
                keep = input(f'AniList progress: {anilist_progress}\nLocal progress: {o["progress"]}\n\nKeep local? [y/n] ') == 'y'
                if not keep:
                    o['progress'] = watchlist[anilist_id]['progress'] or 0
                else:
                    utils.anilist_requests.update_progress(anilist_id, o['progress'])
            else:
                o['progress'] = watchlist[anilist_id]['progress']
        else:
            o['status'] = "UNLISTED"
            o['progress'] = 0
            continue
    utils.mapper.save_map(folder_map)

def check_local_progress(available_list):
    folder_map = utils.mapper.get_map()
    print(folder_map)
    for _, v in folder_map.items():

        print(available_list)
        if 'local_progress' in v and v['local_progress'] > available_list[v['title']]['progress']:
            print('ye')

def get_list():
    folder_map = utils.mapper.get_map()
    return [{**v, 'folder': k} for k, v in folder_map.items() if 'status' in v and v['status'] != 'COMPLETED' and get_episode_path(k, v.get("progress", 0) + 1)]

def attemptSync(online):
    if not online:
        print(colored_text([[BLUE, f'\n[OFFLINE MODE]']]))
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(sync_with_anilist, online)
        try:
            future.result(timeout=5)
            return True
        except TimeoutError:
            print("\nCan't connect to AniList: \nTimed Out!")
            return False
        except Exception as e:
            print(f"\nCan't connect to AniList: \n{type(e).__name__}: {e}")
            return False

def continue_watching(online=True):
    worked = attemptSync(online)

    if not worked:
        attemptSync(False)

    # We do a little trolling
    available_list = get_list()
    folder_map = utils.mapper.get_map()

    if not available_list:
        print('\nNo valid items found!')
        more_options()
    
    print()
    for i, anime in enumerate(available_list):
        animeInfo = [
            [None, '['],
            [GREEN, str(i + 1)],
            [None, '] '],
            [None, '['],
            [YELLOW, f"EP {int(anime.get('progress', 0)) + 1}/{anime.get('length', 0)}"],
            [None, '] '],
            [CYAN, anime['title']],
            [None, ' [' if 'shortlink' in anime and anime['shortlink'] else ""],
            [YELLOW, anime['shortlink'].replace("https://", "www.") if 'shortlink' in anime and anime['shortlink'] else ""],
            [None, ']' if 'shortlink' in anime and anime['shortlink'] else ""],
        ]
        if utils.config.get_config()["image_previews"]:
            if not os.path.exists(anime['local_poster']):
                for folder_path, folder_dict in folder_map.items():
                    if anime['anilist_id'] == folder_map[folder_path]["anilist_id"]:
                        dlPath = utils.mapper.download_image(anime['poster'])
                        folder_map[folder_path]["local_poster"] = dlPath
                        anime['local_poster'] = dlPath
                        break
                    else:
                        continue
                utils.mapper.save_map(folder_map)
            animeInfo.append([None, "\n\n" + subprocess.run(["chafa", "--align=top,left", "--scale=1.0", "--polite=on", anime['local_poster']], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True).stdout.strip()])
        print(colored_text(animeInfo))

    user_input = input("Select a show ('m' for more options): ")
    if user_input == 'm':
        more_options()
    
    selected_anime = available_list[int(user_input) - 1]
    selected_anime_folder = selected_anime['folder']
    selected_anime_episode = selected_anime.get('progress',0) + 1
    episode_path = get_episode_path(selected_anime_folder, selected_anime_episode)
    if not episode_path:
        utils.anilist_requests.show_message_box("Warning", f'Episode not found! Check the folder below and add an episode offset if needed:\n{selected_anime_folder}')
        continue_watching(False)
    play_episode(episode_path, selected_anime)
    continue_watching(False)

def get_episode_path(selected_anime_folder, selected_anime_episode):
    episodes = []
    for file in sorted(os.listdir(selected_anime_folder)):
        if file.startswith('.'):
            continue
        episodes.append(file)
    folder_map = utils.mapper.get_map()
    offset = 0
    if 'offset' in folder_map[selected_anime_folder]:
        offset = folder_map[selected_anime_folder]['offset']
    index_to_play = selected_anime_episode - 1 - offset
    try:
        return f'{selected_anime_folder}/{episodes[index_to_play]}'
    except:
        return None

def play_episode(episode_path, selected_anime):
    if not os.path.exists(episode_path):
        print(colored_text([[RED, f"\n'{episode_path}' does not exist!"]]))
        exit()

    mpv_path = utils.config.get_config()['mpv_path']
    arg = []
    
    if "/usr/bin/flatpak" in mpv_path:
        arg.append(mpv_path)
        arg.append("run")
        arg.append("io.mpv.Mpv")
    else:
        arg.append(mpv_path)

    arg.append(episode_path)

    subprocess.Popen(arg, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

CACHE_FILE = os.path.join(sys.path[0], 'data', 'cached_requests.json')
def load_cache():
    """Load the entire cache."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_cache(cache_data):
    """Save the entire cache."""
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache_data, f, indent=4, ensure_ascii=False)

cache_data = load_cache()
def get_skip(selected_anime, episode):
    global cache_data
    if str(selected_anime.get('anilist_id')) in cache_data:
        libby = libria(selected_anime.get('anilist_id'), episode)
        if libby:
            return opt2list(libby.strip())
        else:
            print(colored_text([[RED, f"Couldn't find skips for this episode.."]]))
            return {}
    else:
        aniskipCMD = ["/usr/local/bin/ani-skip", "-q", str(selected_anime.get('mal_id')), "-e", str(episode)]
        aniskipArg = subprocess.run(aniskipCMD, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True).stdout.strip()

        if "not found" not in aniskipArg.lower():
            return opt2list(aniskipArg.strip())
        else:
            libby = libria(selected_anime.get('anilist_id'), episode)
            if libby:
                return opt2list(libby.strip())
            else:
                print(colored_text([[RED, f"Couldn't find skips for this episode.."]]))
                return {}
                
def opt2list(script_opts):
    # Find the index of '--script-opts=' in the string
    prefix = '--script-opts='
    if prefix in script_opts:
        # Extract the part after '--script-opts='
        opts_part = script_opts.split(prefix, 1)[1]

        if ' ' in opts_part:
            opts_part = opts_part.split(' ', 1)[0]
    else:
        return

    # Split the extracted part by commas to separate each key-value pair
    opts = opts_part.split(',')

    # Initialize an empty list to store the result
    result = []

    # Iterate through each option
    for opt in opts:
        # Remove any leading or trailing spaces
        opt = opt.strip()
        # Append the cleaned option to the result list
        result.append(opt)

    return result

def libria(mediaId, progress):
    global cache_data
    if str(mediaId) in cache_data:
        json_data = cache_data[str(mediaId)]  # Use cached data if available
    else:
        variables = {
            "id": mediaId
        }
        query = '''
        query ($id: Int) {
          Media(id: $id) {
             title {
               romaji
             }
          }
        }
        '''
        result = utils.anilist_requests.anilist_call(query, variables)
        try:
            title = result["data"]["Media"]["title"]["romaji"]
        except Exception as e:
            return None

        title = title.lower().replace(' ', '-')

        response = requests.get("https://api.anilibria.tv/v3/title?code=" + title)
        if response.status_code == 200:
            json_data = response.json()
            cache_data[mediaId] = json_data  # Update cache with new data
            save_cache(cache_data)  # Save the entire cache
        else:
            print(f"Anilibria failed with status code {response.status_code}")
            return

    episodes_list = json_data.get("player", {}).get("list", {})
    if not episodes_list:
        print("No episode list found.")
        return
    episode_data = episodes_list.get(str(progress), {})
    if not episode_data:
        print("No episode data found.")
        return
    opening_timings = episode_data.get("skips", {}).get("opening", [])
    ending_timings = episode_data.get("skips", {}).get("ending", [])

    baseCMD = []
    if opening_timings:
        if opening_timings[0]:
            baseCMD.append("skip-op_start=" + str(opening_timings[0]))
        if opening_timings[1]:
            baseCMD.append("skip-op_end=" + str(opening_timings[1]))
    if ending_timings:
        if ending_timings[0]:
            baseCMD.append("skip-ed_start=" + str(ending_timings[0]))
        if ending_timings[1]:
            baseCMD.append("skip-ed_end=" + str(ending_timings[1]))

    if len(baseCMD) > 0:
        full_cmd = "--script-opts=" + ",".join(baseCMD)
        return full_cmd.strip()
    else:
        return

def more_options():
    while True:
        print(colored_text([
            [GREEN, '\nm'],
            [None, ' - map folders to AniList IDs\n'],
            [GREEN, 'r'],
            [None, ' - attempt auto remapping\n'],
            [GREEN, 'o'],
            [None, ' - add offset\n'],
            [GREEN, 'w'],
            [None, ' - watch\n'],
            [GREEN, 'q'],
            [None, ' - quit'],
        ]))
        user_input = input('\nInput: ')
        if user_input == 'm':
            utils.mapper.map()
        elif user_input == 'r':
            utils.mapper.remap()
        elif user_input == 'o':
            utils.offset.create_offset()
        elif user_input == 'w':
            continue_watching()
        elif user_input == 'q':
            quit()
        else:
            print('\nInvalid option!')
