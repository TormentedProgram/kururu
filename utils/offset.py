import utils.mapper, utils.config
from colorama import Fore, Style
import os

def create_offset():
    folder_map = utils.mapper.get_map()
    if len(folder_map) == 0:
        print("You currently have no mapped folders!")
        return
    print()
    i = 1
    folders = []
    for folder in folder_map:
        folders.append(folder)
    for folder in folders:
        anime_folder = utils.config.get_config()["anime_folder"]
        print(f'[{Fore.GREEN}{i}{Style.RESET_ALL}] {Fore.CYAN}{os.path.relpath(folder, anime_folder)}{Style.RESET_ALL}')
        i += 1
    folder_to_offset = int(input("\nSelect a folder to add an offset to: ")) - 1
    offset = int(input("Enter offset: "))
    folder_map[folders[folder_to_offset]]["offset"] = offset
    utils.mapper.save_map(folder_map)