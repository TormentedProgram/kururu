import utils.config, utils.mapper, utils.continue_watching
from utils.common import get_module, clear_screen

colorama = get_module("Colorama")
colorama.init()

try:
    clear_screen()
    utils.config.set_up()
    utils.mapper.map()
    utils.continue_watching.continue_watching()
except KeyboardInterrupt:  # If user uses Ctrl-C, don't error
    print()
    quit()
