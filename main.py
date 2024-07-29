import sys
import colorama
import utils.config, utils.mapper, utils.continue_watching
from utils.common import colored_text, GREEN, CYAN, YELLOW, RED

colorama.init()

try:
    utils.config.set_up()
    #utils.mapper.map()

    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg.isdigit():
            number = int(arg)
            utils.continue_watching.attemptSync()
            available_list = utils.continue_watching.get_list()
            
            if number > len(available_list):
                print(colored_text([[RED, f'Anime not found in list!']]))
                quit()

            selected_anime = available_list[int(number) - 1]
            selected_anime_folder = selected_anime['folder']
            selected_anime_episode = selected_anime.get('progress',0) + 1
            episode_path = utils.continue_watching.get_episode_path(selected_anime_folder, selected_anime_episode)
            
            if not episode_path:
                print(colored_text([[RED, f'Episode not found! Check the folder below and add an episode offset if needed:\n{selected_anime_folder}']]))
                quit()

            utils.continue_watching.play_episode(episode_path,selected_anime)
        else:
            print(colored_text([[RED, f"The argument '{arg}' is not a valid number."]]))
            quit()
    else:
        utils.continue_watching.continue_watching()

except KeyboardInterrupt:  # If user uses Ctrl-C, don't error
    print()
    quit()
