import sys
import os
import importlib

def install_package(package):
    import subprocess
    try:
        importlib.import_module('pip')
    except ImportError:
        print("Pip installing now")
        subprocess.run([sys.executable, "-m", "ensurepip", "--upgrade"])

    subprocess.run([sys.executable, "-m", "pip", "install", package])
    return True

def get_module(package_name, forceinstall=False):
    if forceinstall:
        try:
            package = importlib.import_module(package_name)
        except ImportError:
            print(f"{package_name} is not installed. Installing...")
            if install_package(package_name):  # Wait for install_package to return True
                package = importlib.import_module(package_name)
            else:
                print(f"Failed to install {package_name}.")
                return None  # Return None if installation failed
            return package
    
    try:
        package = importlib.import_module(package_name)
    except ImportError:
        package = get_module(package_name.lower(), True)
    return package

Style = get_module('Colorama').Style
Fore = get_module('Colorama').Fore

GREEN = Fore.GREEN
RED = Fore.RED
BLUE = Fore.BLUE
CYAN = Fore.CYAN
YELLOW = Fore.YELLOW

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def escape_windows_path(path):
    new_path = ""
    i = 0
    while i < len(path):
        if path[i] == '\\':
            new_path += '\\\\'
            while i < len(path) - 1 and path[i + 1] == '\\':
                i += 1
        else:
            new_path += path[i]
        i += 1
    return new_path

def colored_text(text_arr):
    s = ''
    for style, text in text_arr:
        if not style:
            style = Style.RESET_ALL
        s += str(style) + str(text)
    return s + Style.RESET_ALL

def get_episode_number(file_path, folder_map):
    folder_path, file_name = os.path.split(file_path)
    if folder_path not in folder_map:
        quit()
    offset = 0
    if 'offset' in folder_map[folder_path]:
        offset = folder_map[folder_path]['offset']
    sorted_file_names = [file for file in sorted(os.listdir(folder_path)) if not file.startswith('.')]
    return sorted_file_names.index(file_name) + 1 + offset
