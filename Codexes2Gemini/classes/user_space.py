import json
import logging
import os
import pickle
import time
import traceback
from datetime import datetime
from typing import Dict, List, Optional
import streamlit as st

# Define a maximum size for the pickle file (in bytes)
MAX_PICKLE_SIZE = 100 * 1024 * 1024  # 100 MB


# TO DO Warning: Pickle file is empty. Returning a new UserSpace object.
# TO DO seems to be running selected doc #1 multiple times

class SavedContext:
    """
    Represents a saved context with its name, content, and optional tags.

    Attributes:
        name (str): The name of the saved context.
        content (str): The content of the saved context.
        tags (List[str], optional): A list of tags associated with the context. Defaults to an empty list.
    """

    def __init__(self, name: str, content: str, tags: Optional[List[str]] = None):
        self.name = name
        self.content = content
        self.tags = tags or []


class PromptPack:
    def __init__(self, name, system_instructions, user_prompts, custom_prompt, override, chunking_prompts):
        self.name = name
        self.system_instructions = system_instructions
        self.user_prompts = user_prompts
        self.custom_prompt = custom_prompt
        self.override = override
        self.chunking_prompts = chunking_prompts or []


class UserSpace:
    """
    A class to manage user-specific data, including filters, prompts, saved contexts, results, and prompt plans.

    Attributes:
        filters (Dict): A dictionary to store user-defined filters.
        prompts (Dict): A dictionary to store user-defined prompts.
        saved_contexts (Dict): A dictionary to store saved contexts.
        results (List): A list to store generated results.
        prompt_plans (List): A list to store prompt plans.
        name (str): The name of the UserSpace.

    Methods:
        save_filter(name: str, filter_data: Dict): Saves a filter with the given name and data.
        save_prompt(name: str, prompt: str): Saves a prompt with the given name and text.
        save_context(name: str, content: str, tags: Optional[List[str]] = None): Saves a context with the given name, content, and optional tags.
        get_filtered_contexts(filter_text: str) -> Dict[str, SavedContext]: Returns a dictionary of contexts that match the given filter text.
        save_result(result: str): Saves a generated result to the results list.
        save_prompt_plan(prompt_plan: Dict): Saves a prompt plan to the prompt plans list.
        add_result(key, result): Adds a result to the UserSpace object under the specified key.
        get_unique_name(name: str) -> str: Returns a unique name based on the given name, avoiding collisions with existing names.
    """

    def __init__(self, name: str = "Default"):
        self.filters = {}
        self.prompts = {}
        self.saved_contexts = {}
        self.results = []
        self.prompt_plans = []
        self.name = self.get_unique_name(name)
        with open("resources/json/promptpack_definitions.json", "r") as f:
            prompt_pack_data = json.load(f)
        self.prompt_packs = {
            pack_name: PromptPack(**data)
            for pack_name, data in prompt_pack_data["prompt_packs"].items()
        }

        """
        Note:the default audience/age classifier ending in _nimble uses on a subset of audiences, if you want the full list, drop the _nimble
        """

    def get_filtered_contexts(self, filter_text: str) -> Dict[str, SavedContext]:
        """Returns a dictionary of contexts that match the given filter text.

        Args:
            filter_text (str): The text to filter by.

        Returns:
            Dict[str, SavedContext]: A dictionary of contexts that match the filter.
        """
        return {
            name: context for name, context in self.saved_contexts.items()
            if filter_text.lower() in name.lower() or
               any(filter_text.lower() in tag.lower() for tag in context.tags)
        }

    def get_prompt_packs(self) -> Dict[str, PromptPack]:
        """Returns a dictionary of saved PromptPacks.

        Returns:
            Dict[str, PromptPack]: A dictionary where keys are pack names and values are PromptPackobjects.
        """
        if not hasattr(self, 'prompt_packs'):
            self.prompt_packs = {}
        return self.prompt_packs

    def get_unique_name(self, name: str) -> str:
        """Returns a unique name based on the given name, avoiding collisions with existing names.

        Args:
            name (str): The desired name.

        Returns:
            str: A unique name.
        """
        existing_names = [f.replace("user_space_", "").replace(".pkl", "") for f in os.listdir() if
                          f.startswith("user_space_")]
        if name not in existing_names:
            return name
        else:
            counter = 1
            while f"{name}_{counter}" in existing_names:
                counter += 1
            return f"{name}_{counter}"

    def save_result(self, result: str):
        """Saves a generated result to the results list.

        Args:
            result (str): The generated result.
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.results.append({"timestamp": timestamp, "result": result})

    def save_prompt_plan(self, prompt_plan: Dict):
        """Saves a prompt plan to the prompt plans list.

        Args:
            prompt_plan (Dict): The prompt plan data.
        """
        self.prompt_plans.append(prompt_plan)

    def save_filter(self, name: str, filter_data: Dict):
        """Saves a filter with the given name and data.

        Args:
            name (str): The name of the filter.
            filter_data (Dict): The data associated with the filter.
        """
        if not name:
            name = f"Filter_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.filters[name] = filter_data

    def save_prompt(self, name: str, prompt: str):
        """Saves a prompt with the given name and text.

        Args:
            name (str): The name of the prompt.
            prompt (str): The text of the prompt.
        """
        if not name:
            name = f"Prompt_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.prompts[name] = prompt

    def save_context(self, name: str, content: str, tags: Optional[List[str]] = None):
        """Saves a context with the given name, content, and optional tags.

        Args:
            name (str): The name of the context.
            content (str): The content of the context.
            tags (List[str], optional): A list of tags associated with the context. Defaults to None.
        """
        if not name:
            name = f"Context_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.saved_contexts[name] = SavedContext(name, content, tags)

    def add_result(self, key, result):
        """Adds a result to the UserSpace object under the specified key.

        Args:
            key (str): The key to store the result under.
            result (Any): The result to store.
        """
        timestamp = time.time()  # this gives a timestamp
        self.__dict__[key] = {"result": result, "time": timestamp}

    def create_prompt_pack(self, pack_name: str, system_instructions: List[str],
                           user_prompts: Dict[str, str], custom_prompt: str, override: bool):
        """Creates a new PromptPack and saves it to the UserSpace.

        Args:
            pack_name (str): The name of the new PromptPack.
            system_instructions (List[str]): A list of system instruction keys.
            user_prompts (Dict[str, str]): A dictionary of user prompt keys and their corresponding prompts.
            custom_prompt (str): A custom user prompt.
            override (bool): Whether the custom prompt should override other user prompts.
        """
        if pack_name in self.get_prompt_packs():
            raise ValueError(f"PromptPack '{pack_name}' already exists.")

        pack = PromptPack(pack_name, system_instructions, user_prompts, custom_prompt, override)
        self.save_instruction_pack(pack)

    def read_prompt_pack(self, pack_name: str) -> PromptPack:
        """Reads an PromptPackfrom the UserSpace.

        Args:
            pack_name (str): The name of the PromptPack to read.

        Returns:
            PromptPack: The PromptPackobject if found, otherwise None.
        """
        return self.get_prompt_packs().get(pack_name)

    def update_prompt_pack(self, pack_name: str, system_instructions: Optional[List[str]] = None,
                           user_prompts: Optional[Dict[str, str]] = None,
                           custom_prompt: Optional[str] = None, override: Optional[bool] = None):
        """Updates an existing PromptPack in the UserSpace.

        Args:
            pack_name (str): The name of the PromptPack to update.
            system_instructions (List[str], optional): The updated list of system instruction keys.
            user_prompts (Dict[str, str], optional): The updated dictionary of user prompt keys and prompts.
            custom_prompt (str, optional): The updated custom user prompt.
            override (bool, optional): Whether the custom prompt should override other user prompts.
        """
        pack = self.read_prompt_pack(pack_name)
        if not pack:
            raise ValueError(f"PromptPack '{pack_name}' not found.")

        if system_instructions is not None:
            pack.system_instructions = system_instructions
        if user_prompts is not None:
            pack.user_prompts = user_prompts
        if custom_prompt is not None:
            pack.custom_prompt = custom_prompt
        if override is not None:
            pack.override = override

        self.save_instruction_pack(pack)

    def destroy_prompt_pack(self, pack_name: str):
        """Deletes an PromptPack from the UserSpace.

        Args:
            pack_name (str): The name of the PromptPack to delete.
        """
        if pack_name not in self.get_prompt_packs():
            raise ValueError(f"PromptPack '{pack_name}' not found.")

        del self.prompt_packs[pack_name]
        self.save_user_space(self)

    def rename_prompt_pack(self, old_name: str, new_name: str):
        """Renames an PromptPack in the UserSpace.

        Args:
            old_name (str): The current name of the PromptPack.
            new_name (str): The new name for the PromptPack.
        """
        if old_name not in self.get_prompt_packs():
            raise ValueError(f"PromptPack '{old_name}' not found.")
        if new_name in self.get_prompt_packs():
            raise ValueError(f"PromptPack '{new_name}' already exists.")

        pack = self.prompt_packs[old_name]
        pack.name = new_name
        self.prompt_packs[new_name] = pack
        del self.prompt_packs[old_name]
        self.save_user_space(self)

    def save_prompt_pack(self, pack: PromptPack):
        """Saves an PromptPack.

        Args:
            pack (PromptPack): The PromptPackobject to save.
        """
        if not hasattr(self, 'prompt_packs'):
            self.prompt_packs = {}
        self.prompt_packs[pack.name] = pack
        self.save_user_space()

    def save_user_space(self):  # Add self as argument
        """Saves the UserSpace object to a pickle file.

        Args:
            user_space (UserSpace): The UserSpace object to save.
        """
        try:
            # Check if the pickle file already exists and its size
            file_path = f"user_space_{self.name}.pkl"
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                if file_size > MAX_PICKLE_SIZE:
                    print(f"Warning: Pickle file '{file_path}' is larger than {MAX_PICKLE_SIZE} bytes. Not saving.")
                    return

            # Save the UserSpace object to a pickle file
            with open(file_path, 'wb') as f:
                pickle.dump(self, f)  # Pass self to pickle.dump
        except Exception as e:
            print(f"Error saving UserSpace: {e}")
            st.error(traceback.format_exc())

    def load_user_space(name: str = "Default"):
        """Loads the UserSpace object from a pickle file.

        Args:
            name (str): The name of the UserSpace to load. Defaults to "Default".

        Returns:
            UserSpace: The loaded UserSpace object.
        """
        try:
            # Check if the pickle file exists and its size
            file_path = f"user_space_{name}.pkl"
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)

                if file_size > MAX_PICKLE_SIZE:
                    print(f"Warning: Pickle file '{file_path}' is larger than {MAX_PICKLE_SIZE} bytes. Not loading.")
                    return UserSpace(name)

                if file_size == 0:
                    print("Warning: Pickle file is empty. Returning a new UserSpace object.")
                    return UserSpace(name)

                # Load the UserSpace object from the pickle file
                with open(file_path, 'rb') as f:
                    loaded_object = pickle.load(f)

                    # Check if the loaded object is of the correct class
                    if isinstance(loaded_object, UserSpace):
                        return loaded_object
                    else:
                        print(f"Warning: Loaded object is not of type UserSpace. Returning a new UserSpace object.")
                        return UserSpace(name)
            else:  # create new userspace object
                return UserSpace(name)

        except FileNotFoundError:
            return UserSpace(name)
        except Exception as e:
            print(f"Error loading UserSpace: {e}")
            logging.error(f"Error loading UserSpace {traceback.format_exc()}")
            return UserSpace(name)


    def load_prompt_pack_from_json(self, pack_name):
        """Loads an PromptPack from a JSON file.

        Args:
            pack_name (str): The name of the PromptPack to load.

        Returns:
            PromptPack: The loaded PromptPackobject if found, otherwise None.
        """
        try:
            with open(f"user_data/{self.name}/prompt_pack_{pack_name}.json", "r") as f:
                pack_data = json.load(f)
            return PromptPack(**pack_data)
        except FileNotFoundError:
            return None
        except Exception as e:
            print(f"Error loading PromptPack from JSON: {e}")
            logging.error(f"Error loading PromptPack from JSON: {traceback.format_exc()}")
            return None


    def save_prompt_pack_to_json(self, pack):
        """Saves a PromptPack to a JSON file.

        Args:
            pack (PromptPack): The PromptPackobject to save.
        """
        # make sure user_data / self.name exists
        if not os.path.exists(f"user_data/{self.name}"):
            os.makedirs(f"user_data/{self.name}")

        try:
            with open(f"user_data/{self.name}/prompt_pack_{pack.name}.json", "w") as f:
                json.dump(pack.__dict__, f, indent=4)
        except Exception as e:
            print(f"Error saving PromptPack to JSON: {e}")
            logging.error(f"Error saving PromptPack to JSON: {traceback.format_exc()}")
