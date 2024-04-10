import sys
import utils.config, utils.mapper, utils.continue_watching, utils.search
from utils.mapper import map_folder
from utils.common import get_module, clear_screen
from utils.search import get_anilist_id

colorama = get_module("Colorama")
colorama.init()

def main():
    if len(sys.argv) == 3:
        path = str(sys.argv[1])
        search = str(sys.argv[2])
        if path and search:
            id = get_anilist_id(search)
            map_folder(path, id)
        else:
            main()
        return
    try:
        clear_screen()
        utils.config.set_up()
        utils.mapper.map()
        utils.continue_watching.continue_watching()
    except KeyboardInterrupt:  # If user uses Ctrl-C, don't error
        print()
        quit()

if __name__ == "__main__":
    main()