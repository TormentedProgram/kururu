import sys
import colorama
import utils.common
import utils.config, utils.mapper, utils.continue_watching
from utils.common import colored_text, GREEN, CYAN, YELLOW, RED
import tempfile

colorama.init()


def write_metadata_to_tempfile(metadata_dict): # it was like 2 am so i used chatgpt for this function but i did have to correct it ¯\_(ツ)_/¯
    # Create a temporary file in the /tmp directory with a random name
    temp_file = tempfile.NamedTemporaryFile(delete=False, dir='/tmp')
    
    # Write the metadata to the temporary file
    with open(temp_file.name, 'w') as file:
        file.write(';FFMETADATA1\n')
        
        # Ensure metadata_dict is a dictionary
        if not isinstance(metadata_dict, dict):
            raise ValueError("Metadata should be a dictionary.")
        
        # Identify and write chapters based on keys
        start_key_op = next((key for key in metadata_dict if 'op_' in key.lower()), None)
        end_key_op = next((key for key in metadata_dict if 'op_end' in key.lower()), None)
        start_key_ed = next((key for key in metadata_dict if 'ed_' in key.lower()), None)
        end_key_ed = next((key for key in metadata_dict if 'ed_end' in key.lower()), None)
        
        # Initialize default values
        start_value_ms_op = end_value_ms_op = start_value_ms_ed = end_value_ms_ed = 0
        end_value_ms_ed = 99999999 * 1000  # Default end time in milliseconds
        
        # Write opening chapter
        if start_key_op and end_key_op:
            start_value_op = metadata_dict.get(start_key_op, 0)
            end_value_op = metadata_dict.get(end_key_op, 0)
            start_value_ms_op = int(start_value_op * 1000)  # Convert to milliseconds
            end_value_ms_op = int(end_value_op * 1000)      # Convert to milliseconds
            file.write('[CHAPTER]\n')
            file.write('TIMEBASE=1/1000\n')
            file.write(f'START={start_value_ms_op}\n')
            file.write(f'END={end_value_ms_op}\n')
            file.write('TITLE=Opening\n\n')

        # Write episode chapter
        if end_key_op:
            end_value_op = metadata_dict.get(end_key_op, 0)
            end_value_ms_op = int(end_value_op * 1000)  # Convert to milliseconds
        else:
            end_value_ms_op = 0
        
        if start_key_ed:
            start_value_ed = metadata_dict.get(start_key_ed, 99999999)
            start_value_ms_ed = int(start_value_ed * 1000)  # Convert to milliseconds
        else:
            start_value_ms_ed = 99999999  # Default end time if end key is missing
        
        file.write('[CHAPTER]\n')
        file.write('TIMEBASE=1/1000\n')
        file.write(f'START={end_value_ms_op}\n')
        file.write(f'END={start_value_ms_ed}\n')
        file.write('TITLE=Episode\n\n')

        # Write ending chapter
        if start_key_ed and end_key_ed:
            start_value_ed = metadata_dict.get(start_key_ed, 0)
            end_value_ed = metadata_dict.get(end_key_ed, 0)
            start_value_ms_ed = int(start_value_ed * 1000)  # Convert to milliseconds
            end_value_ms_ed = int(end_value_ed * 1000)      # Convert to milliseconds
            file.write('[CHAPTER]\n')
            file.write('TIMEBASE=1/1000\n')
            file.write(f'START={start_value_ms_ed}\n')
            file.write(f'END={end_value_ms_ed}\n')
            file.write('TITLE=Ending\n\n')
    
    # Return the path to the temporary file
    return temp_file.name

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
            if arg == "-s":
                import os
                file_path = sys.argv[2]
                folder_map = utils.mapper.get_map()

                if len(sys.argv) >= 4:
                    episodeArg = int(sys.argv[3])
                else:
                    episodeArg = utils.common.get_episode_number(file_path, folder_map)
                    
                folder_path = os.path.split(file_path)[0]
                utils.continue_watching.attemptSync()

                selected_anime = folder_map[folder_path]
                selected_anime_episode = episodeArg

                timings_dict = {}
                theskips = utils.continue_watching.get_skip(selected_anime, selected_anime_episode)
                if len(theskips) > 0:
                    for cmd in theskips:
                        # Split the string by '=' to separate the key and value
                        key, value = cmd.split('=')
                        # Remove the prefix 'skip-' from the key
                        key = key.replace('skip-', '')
                        # Add the key-value pair to the dictionary
                        timings_dict[key] = float(value)

                    timings_dict["chapters-file"] = write_metadata_to_tempfile(timings_dict)
                    import json
                    json_str = json.dumps(timings_dict)
                    print(json_str)

            if arg == "-o":
                utils.continue_watching.continue_watching(False)

            if arg == "-wip":
                utils.qtUiController.main()
    else:
        utils.continue_watching.continue_watching(True)

except KeyboardInterrupt:  # If user uses Ctrl-C, don't error
    print()
    quit()