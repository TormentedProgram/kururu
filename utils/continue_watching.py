import subprocess, os
import utils.anilist_requests, utils.mapper, utils.offset, utils.config
from utils.common import colored_text, GREEN, CYAN, YELLOW, RED
import re
import pick 
from concurrent.futures import ThreadPoolExecutor, TimeoutError

def sync_with_anilist():
    watchlist = utils.anilist_requests.get_watching_list()
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

def attemptSync():
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(sync_with_anilist)
        try:
            future.result(timeout=5)
        except TimeoutError:
            print("\nCan't connect to AniList: \nTimed Out!")
        except Exception as e:
            print(f"\nCan't connect to AniList: \n{type(e).__name__}: {e}")

def continue_watching():
    attemptSync()

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

    user_input = input("\nSelect a show ('m' for more options): ")
    if user_input == 'm':
        more_options()
    
    selected_anime = available_list[int(user_input) - 1]
    selected_anime_folder = selected_anime['folder']
    selected_anime_episode = selected_anime.get('progress',0) + 1
    episode_path = get_episode_path(selected_anime_folder, selected_anime_episode)
    if not episode_path:
        print(colored_text([[RED, f'Episode not found! Check the folder below and add an episode offset if needed:\n{selected_anime_folder}']]))
        continue_watching()
    play_episode(episode_path, selected_anime)
    continue_watching()

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

    if utils.config.get_config()["aniskip"]:
        aniskipCMD = ["/usr/local/bin/ani-skip", "-q", str(selected_anime.get('mal_id')), "-e", str(selected_anime.get('progress',0) + 1)]
        aniskipArgs = re.findall(r'--[^\s]+', subprocess.run(aniskipCMD, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True).stdout.strip())

        if aniskipArgs:
            for aniskipArg in aniskipArgs:
                arg.append(aniskipArg.strip())
        else:
            print(colored_text([[RED, f"Couldn't find intro skips for this episode.."]]))

    subprocess.Popen(arg, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

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
