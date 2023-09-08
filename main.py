import os
from random import shuffle
import keybinds
import re
import requests
from collections import defaultdict

def random_keybind(available_keys):
    random_key = available_keys.pop()
    mapped_value = keybinds.keybind_mapping[random_key]
    return random_key, mapped_value

def fetch_character_and_server_names(region, account_path):
    server_and_characters = {}
    all_dirs = [d for d in os.listdir(account_path) if os.path.isdir(os.path.join(account_path, d))]
    server_dirs = [d for d in all_dirs if d != 'SavedVariables']

    for server in server_dirs:
        server_path = os.path.join(account_path, server)
        character_dirs = [d for d in os.listdir(server_path) if os.path.isdir(os.path.join(server_path, d))]
        server_and_characters[server] = character_dirs

    return fetch_character_class(region, server_and_characters)

def fetch_character_class(region, server_and_characters):
    wow_classes = [
        "Druid", "Hunter", "Mage", "Paladin",
        "Priest", "Rogue", "Shaman", "Warlock",
        "Warrior", "Monk", "Demon Hunter", "Death Knight"
    ]

    for server, characters in server_and_characters.items():
        new_characters = {}
        server_url_friendly = server.replace(" ", "-")
        for character in characters:
            url = f"https://worldofwarcraft.blizzard.com/en-gb/character/{region}/{server_url_friendly}/{character}"
            response = requests.get(url)
            if response.status_code != 200:
                print(f"Failed to fetch data for {character} on {server}. Skipping...")
                continue
            response_text = response.text.lower()
            character_class = next((cls for cls in wow_classes if cls.lower() in response_text), None)
            if character_class:
                new_characters[character] = character_class
            else:
                print(f"Could not determine class for {character} on {server}.")
        server_and_characters[server] = new_characters
    return server_and_characters

def populate_keybinds(lines, available_keys, class_keybinds):
    new_lines = []
    bindpad_macros = []
    general_keybindings = []
    macro_name_counter = 1
    current_class = None

    wow_classes = "Druid|Hunter|Mage|Paladin|Priest|Rogue|Shaman|Warlock|Warrior|Monk|Demon Hunter|Death Knight"
    pattern = re.compile(
        rf"\[({wow_classes} - \w+)|(Classic {wow_classes})|(TBC {wow_classes})|(WOTLK {wow_classes})\]")

    for line in lines:
        stripped_line = line.strip()
        match = pattern.match(stripped_line)
        if match:
            current_class = match.group(1)
            available_keys = list(keybinds.keybind_mapping.keys())
            shuffle(available_keys)
        elif stripped_line.startswith("["):
            current_class = None

        if current_class and "=" in stripped_line:
            key, _ = stripped_line.split("=", 1)
            key = key.strip()

            if key != "Potion" and "START" not in key and available_keys:
                new_key, mapped_value = random_keybind(available_keys)
                formatted_new_key = new_key.replace(" + ", "-").replace(" ", "")
                new_line = f"{key}={mapped_value};"
                new_lines.append(new_line)

                if current_class:
                    class_keybinds[current_class].append(f'bind {formatted_new_key} CLICK BindPadMacro:{macro_name_counter}')

                bindpad_macro = (
                    "\t\t\t\t{",
                    f'\t\t\t\t\t["type"] = "CLICK",',
                    f'\t\t\t\t\t["name"] = "{macro_name_counter}",',
                    f'\t\t\t\t\t["macrotext"] = "/cast {key}",',
                    f'\t\t\t\t\t["action"] = "CLICK BindPadMacro:{macro_name_counter}",',
                    '\t\t\t\t\t["texture"] = 132089,',
                    "\t\t\t\t},"
                )
                bindpad_macros.append('\n'.join(bindpad_macro))

                general_keybindings.append(f'\t\t\t\t["{formatted_new_key}"] = "BindPadMacro:{macro_name_counter}",')

                macro_name_counter += 1

    return new_lines, bindpad_macros, general_keybindings

def main(config_path, account_path, region):
    region = region.lower()
    available_keys = list(keybinds.keybind_mapping.keys())
    shuffle(available_keys)
    class_keybinds = defaultdict(list)

    AllServersWithCharacterList = fetch_character_and_server_names(region, account_path)

    with open(config_path, 'r', encoding='utf-16') as configfile:
        lines = configfile.readlines()

    new_lines, bindpad_macros, general_keybindings = populate_keybinds(lines, available_keys, class_keybinds)
    new_text_map = {k: v for k, v in (line.split("=", 1) for line in new_lines)}

    updated_lines = []
    for line in lines:
        stripped_line = line.strip()
        if "=" in stripped_line:
            key, value = stripped_line.split("=", 1)
            key = key.strip()
            if key in new_text_map:
                updated_lines.append(f"{key}={new_text_map[key]}")
            else:
                updated_lines.append(line.strip())
        else:
            updated_lines.append(line.strip())

    updated_text = '\n'.join(updated_lines)

    with open(config_path, 'w', encoding='utf-16') as configfile:
        configfile.write(updated_text)

    bindpad_macro_text = '\n'.join(bindpad_macros)
    general_keybindings_text = '\n'.join(general_keybindings)

    for server, characters in AllServersWithCharacterList.items():
        for character, char_class in characters.items():
            bindpad_path = os.path.join(account_path, 'SavedVariables', 'BindPad.lua')
            bindings_cache_path = os.path.join(account_path, server, character, "bindings-cache.wtf")

            bindings_cache_content = '\n'.join(class_keybinds.get(char_class, []))

            with open(bindings_cache_path, 'w', encoding='utf-8') as cache_file:
                cache_file.write(bindings_cache_content)

            with open(bindpad_path, 'r', encoding='utf-8') as bindpad_file:
                original_content = bindpad_file.read()

            # Insert bindpad_macro_text
            macro_insert_position = original_content.find('["CharacterSpecificTab1"] = {')
            if macro_insert_position == -1:
                print("Could not find BindPadVars section in bindpad.lua")
                continue
            macro_insert_position += len('["CharacterSpecificTab1"] = {') + 1
            new_content = original_content[:macro_insert_position] + bindpad_macro_text + '\n' + original_content[macro_insert_position:]

            # Insert general_keybindings_text
            profile_name = f"PROFILE_{server}_{character}"
            profile_position = new_content.find(f'["{profile_name}"] = {{')
            if profile_position == -1:
                print(f"Could not find profile section for {profile_name} in bindpad.lua")
                continue
            all_keybindings_position = new_content.find('["AllKeyBindings"] = {', profile_position)
            if all_keybindings_position == -1:
                print("Could not find CharacterSpecificTab1 section in bindpad.lua")
                continue
            all_keybindings_position += len('["AllKeyBindings"] = {') + 1
            final_content = new_content[:all_keybindings_position] + general_keybindings_text + '\n' + new_content[all_keybindings_position:]

            # Write the new content back to bindpad.lua
            with open(bindpad_path, 'w', encoding='utf-8') as bindpad_file:
                bindpad_file.write(final_content)

