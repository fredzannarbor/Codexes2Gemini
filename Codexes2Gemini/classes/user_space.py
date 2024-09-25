import os
import pickle
import time
from datetime import datetime
from typing import Dict, List, Optional

# Define a maximum size for the pickle file (in bytes)
MAX_PICKLE_SIZE = 100 * 1024 * 1024  # 100 MB

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


class InstructionPack:
    def __init__(self, name, system_instructions, user_prompts, custom_prompt, override):
        self.name = name
        self.system_instructions = system_instructions
        self.user_prompts = user_prompts
        self.custom_prompt = custom_prompt
        self.override = override

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

    def get_instruction_packs(self) -> Dict[str, InstructionPack]:
        """Returns a dictionary of saved instruction packs.

        Returns:
            Dict[str, InstructionPack]: A dictionary where keys are pack names and values are InstructionPack objects.
        """
        if not hasattr(self, 'instruction_packs'):
            self.instruction_packs = {}
        return self.instruction_packs

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

    def create_instruction_pack(self, pack_name: str, system_instructions: List[str],
                                user_prompts: Dict[str, str], custom_prompt: str, override: bool):
        """Creates a new InstructionPack and saves it to the UserSpace.

        Args:
            pack_name (str): The name of the new instruction pack.
            system_instructions (List[str]): A list of system instruction keys.
            user_prompts (Dict[str, str]): A dictionary of user prompt keys and their corresponding prompts.
            custom_prompt (str): A custom user prompt.
            override (bool): Whether the custom prompt should override other user prompts.
        """
        if pack_name in self.get_instruction_packs():
            raise ValueError(f"Instruction pack '{pack_name}' already exists.")

        pack = InstructionPack(pack_name, system_instructions, user_prompts, custom_prompt, override)
        self.save_instruction_pack(pack)

    def read_instruction_pack(self, pack_name: str) -> InstructionPack:
        """Reads an InstructionPack from the UserSpace.

        Args:
            pack_name (str): The name of the instruction pack to read.

        Returns:
            InstructionPack: The InstructionPack object if found, otherwise None.
        """
        return self.get_instruction_packs().get(pack_name)

    def update_instruction_pack(self, pack_name: str, system_instructions: Optional[List[str]] = None,
                                user_prompts: Optional[Dict[str, str]] = None,
                                custom_prompt: Optional[str] = None, override: Optional[bool] = None):
        """Updates an existing InstructionPack in the UserSpace.

        Args:
            pack_name (str): The name of the instruction pack to update.
            system_instructions (List[str], optional): The updated list of system instruction keys.
            user_prompts (Dict[str, str], optional): The updated dictionary of user prompt keys and prompts.
            custom_prompt (str, optional): The updated custom user prompt.
            override (bool, optional): Whether the custom prompt should override other user prompts.
        """
        pack = self.read_instruction_pack(pack_name)
        if not pack:
            raise ValueError(f"Instruction pack '{pack_name}' not found.")

        if system_instructions is not None:
            pack.system_instructions = system_instructions
        if user_prompts is not None:
            pack.user_prompts = user_prompts
        if custom_prompt is not None:
            pack.custom_prompt = custom_prompt
        if override is not None:
            pack.override = override

        self.save_instruction_pack(pack)

    def destroy_instruction_pack(self, pack_name: str):
        """Deletes an InstructionPack from the UserSpace.

        Args:
            pack_name (str): The name of the instruction pack to delete.
        """
        if pack_name not in self.get_instruction_packs():
            raise ValueError(f"Instruction pack '{pack_name}' not found.")

        del self.instruction_packs[pack_name]
        save_user_space(self)

    def rename_instruction_pack(self, old_name: str, new_name: str):
        """Renames an InstructionPack in the UserSpace.

        Args:
            old_name (str): The current name of the instruction pack.
            new_name (str): The new name for the instruction pack.
        """
        if old_name not in self.get_instruction_packs():
            raise ValueError(f"Instruction pack '{old_name}' not found.")
        if new_name in self.get_instruction_packs():
            raise ValueError(f"Instruction pack '{new_name}' already exists.")

        pack = self.instruction_packs[old_name]
        pack.name = new_name
        self.instruction_packs[new_name] = pack
        del self.instruction_packs[old_name]
        save_user_space(self)

    def save_instruction_pack(self, pack: InstructionPack):
        """Saves an instruction pack.

        Args:
            pack (InstructionPack): The InstructionPack object to save.
        """
        if not hasattr(self, 'instruction_packs'):
            self.instruction_packs = {}
        self.instruction_packs[pack.name] = pack
        save_user_space(self)
def save_user_space(user_space: UserSpace):
    """Saves the UserSpace object to a pickle file.

    Args:
        user_space (UserSpace): The UserSpace object to save.
    """
    try:
        # Check if the pickle file already exists and its size
        file_path = f"user_space_{user_space.name}.pkl"
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            if file_size > MAX_PICKLE_SIZE:
                print(f"Warning: Pickle file '{file_path}' is larger than {MAX_PICKLE_SIZE} bytes. Not saving.")
                return

        # Save the UserSpace object to a pickle file
        with open(file_path, 'wb') as f:
            pickle.dump(user_space, f)
    except Exception as e:
        print(f"Error saving UserSpace: {e}")


def load_user_space(name: str = "Default") -> UserSpace:
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

        # Load the UserSpace object from the pickle file
        with open(file_path, 'rb') as f:
            loaded_object = pickle.load(f)

            # Check if the loaded object is of the correct class
            if isinstance(loaded_object, UserSpace):
                return loaded_object
            else:
                print(f"Warning: Loaded object is not of type UserSpace. Returning a new UserSpace object.")
                return UserSpace(name)

    except FileNotFoundError:
        return UserSpace(name)
    except Exception as e:
        print(f"Error loading UserSpace: {e}")
        return UserSpace(name)
