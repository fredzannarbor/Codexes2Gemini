import json
import logging
import os
from collections import OrderedDict
from typing import List, Dict, Any

import pymupdf as fitz  # PyMuPDF

from Codexes2Gemini.classes.Utilities.utilities import configure_logger


class PromptPlan(OrderedDict):
    """
    Represents a plan for generating text using a language model.

    This class encapsulates all the necessary parameters and configurations for a single text generation task.
    It includes information about the context, prompts, model, generation settings, and output options.

    Parameters:
        context (str, optional): The initial context for the generation task. Defaults to "".
        context_file_paths (List[str], optional): A list of paths to files containing context. Defaults to None.
        user_keys (List[str], optional): A list of user-defined keys for selecting prompts. Defaults to None.
        thisdoc_dir (str, optional): The directory to store output files. Defaults to "".
        json_required (bool, optional): Whether to require JSON output. Defaults to False.
        generation_config (dict, optional): Configuration for the generation process. Defaults to None.
        system_instructions_dict_file_path (str, optional): Path to the system instructions dictionary file. Defaults to None.
        list_of_system_keys (str, optional): A comma-separated list of system keys to use. Defaults to None.
        user_prompt (str, optional): A user-provided prompt. Defaults to "".
        user_prompt_override (bool, optional): Whether to override prompts from the dictionary. Defaults to False.
        user_prompts_dict (Dict[str, Any], optional): A dictionary of user-defined prompts. Defaults to None.
        user_prompts_dict_file_path (str, optional): Path to the user prompts dictionary file. Defaults to "user_prompts.json".
        list_of_user_keys_to_use (List[str], optional): A list of user keys to use for selecting prompts. Defaults to None.
        continuation_prompts (bool, optional): Whether to use continuation prompts. Defaults to False.
        output_file_base_name (str, optional): The base name for output files. Defaults to "output".
        log_level (str, optional): The logging level. Defaults to "INFO".
        number_to_run (int, optional): The number of times to run the generation task. Defaults to 1.
        minimum_required_output (bool, optional): Whether to enforce a minimum output length. Defaults to False.
        minimum_required_output_tokens (int, optional): The minimum desired output length in tokens. Defaults to 100.
        maximum_output_tokens (int, optional): The maximum desired output length in tokens. Defaults to 8000.
        model_name (str, optional): The name of the language model to use. Defaults to None.
        mode (str, optional): The mode of operation. Defaults to "part".
        config_file (str, optional): Path to a JSON configuration file. Defaults to None.
        use_all_user_keys (bool, optional): Whether to use all user keys from the dictionary. Defaults to False.
        add_system_prompt (str, optional): Additional system prompt to append. Defaults to "".

    Methods:
        load_config(config_file: str) -> None:
            Loads configuration from a JSON file.
        read_contexts() -> str:
            Reads context from files and combines them into a single string.
        prepare_final_prompts() -> List[str]:
            Prepares the final list of prompts based on user keys and overrides.
        get_prompts() -> List[str]:
            Returns the final list of prompts.
        set_provider(provider: str, model: str) -> None:
            Sets the provider and model for the PromptPlan.
        to_dict() -> Dict[str, Any]:
            Converts the PromptPlan object to a dictionary.
        save_config(file_path: str) -> None:
            Saves the current configuration to a JSON file.
        update_from_dict(config: Dict[str, Any]) -> None:
            Updates the PromptPlan object from a dictionary.
        add_context(new_context: str) -> None:
            Adds new context to the existing context.
        add_prompt(new_prompt: str) -> None:
            Adds a new prompt to the list of final prompts.
        clear_prompts() -> None:
            Clears all prompts.
        __str__(self) -> str:
            Returns a string representation of the PromptPlan object.
        __repr__(self) -> str:
            Returns a detailed string representation of the PromptPlan object.
    """

    def __init__(self, context: str = "", context_file_paths: List[str] = None, user_keys: List[str] = None,
                 thisdoc_dir: str = "", json_required: bool = False, generation_config: dict = None,
                 system_instructions_dict_file_path: str = None, list_of_system_keys: str = None,
                 user_prompt: str = "", user_prompt_override: bool = False,
                 user_prompts_dict: Dict[str, Any] = None,  #
                 user_prompts_dict_file_path="user_prompts.json",  # Change this line
                 list_of_user_keys_to_use: List[str] = None,
                 continuation_prompts: bool = False,
                 output_file_base_name: str = "output",
                 log_level: str = "INFO",
                 number_to_run: int = 1,
                 minimum_required_output=False,
                 minimum_required_output_tokens: int = 100,
                 maximum_output_tokens=8000,
                 model_name: str = None, mode: str = "part",
                 config_file: str = None, use_all_user_keys: bool = False, add_system_prompt: str = "") -> None:

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)
        configure_logger(log_level)
        # If a config file is provided, load it first
        if config_file:
            self.load_config(config_file)

        # Now set or override values with explicitly passed parameters
        self.context_file_paths = context_file_paths or []
        if not self.context_file_paths and not context:
            self.logger.warning("No context file paths provided and no context string. Context will be empty.")
        self.context = self.read_contexts() if self.context_file_paths else context
        self.user_keys = user_keys or []
        self.thisdoc_dir = thisdoc_dir
        self.json_required = json_required
        self.generation_config = generation_config or {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 0,
            "max_output_tokens": 8192,
        }
        self.system_instructions_dict_file_path = system_instructions_dict_file_path
        self.list_of_system_keys = list_of_system_keys if isinstance(list_of_system_keys,
                                                                     list) else list_of_system_keys.split(
            ',') if list_of_system_keys else []
        self.user_prompt = user_prompt
        self.user_prompt_override = user_prompt_override
        self.user_prompts_dict_file_path = user_prompts_dict_file_path
        self.list_of_user_keys_to_use = list_of_user_keys_to_use or []  # Initialize as an empty list
        self.continuation_prompts = continuation_prompts
        self.output_file_path = output_file_base_name
        self.number_to_run = number_to_run
        self.minimum_required_output = minimum_required_output
        self.minimum_required_output_tokens = minimum_required_output_tokens
        self.maximum_output_tokens = maximum_output_tokens
        self.model = model_name
        self.mode = mode
        self.use_all_user_keys = use_all_user_keys
        self.user_prompts_dict = user_prompts_dict or {}  # Change this line
        self.final_prompts = self.prepare_final_prompts()
        self.add_system_prompt = add_system_prompt

    def load_config(self, config_file: str) -> None:
        """Load configuration from a JSON file."""

        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            self.__dict__.update(config)
        except Exception as e:
            self.logger.error(f"Error loading config file: {e}")

    def read_contexts(self) -> str:
        if not self.context_file_paths:
            return ""

        combined_context = ""
        for file_path in self.context_file_paths:
            file_extension = os.path.splitext(file_path)[1].lower()

            try:
                if file_extension == '.txt':
                    with open(file_path, 'r', encoding='utf-8') as file:
                        combined_context += file.read() + "\n\n"
                elif file_extension in ['.pdf', '.epub', '.mobi']:
                    doc = fitz.open(file_path)
                    for page in doc:
                        combined_context += page.get_text() + "\n"
                    doc.close()
                else:
                    self.logger.warning(f"Unsupported file type: {file_extension} for file: {file_path}")
            except Exception as e:
                self.logger.error(f"Error reading context file {file_path}: {e}")

        return combined_context.strip()

    def prepare_final_prompts(self) -> List[str]:
        self.logger.info(f"Preparing final prompts. User prompt: {self.user_prompt}")
        self.logger.info(f"List of user keys to use: {self.list_of_user_keys_to_use}")

        final_prompts = []

        if self.list_of_user_keys_to_use and self.user_prompts_dict:
            self.logger.info(f"Selecting prompts based on list_of_user_keys_to_use: {self.list_of_user_keys_to_use}")
            for key in self.list_of_user_keys_to_use:
                if key in self.user_prompts_dict:
                    final_prompts.append(self.user_prompts_dict[key]['prompt'])
                else:
                    self.logger.warning(f"Key '{key}' not found in user_prompts_dict")

        if self.user_prompt:
            self.logger.info("Appending user_prompt to final_prompts")
            final_prompts.append(self.user_prompt)

        if not final_prompts:
            self.logger.warning("No prompts available. Using default prompt.")
            final_prompts = ["Please provide output based on the given context."]

        self.logger.debug(f"Final prompts: {final_prompts}")
        return final_prompts

    def get_prompts(self) -> List[str]:
        """Return the final list of prompts."""
        return self.final_prompts

    def set_provider(self, provider: str, model: str) -> None:
        """Set the provider and model for the PromptPlan."""
        self.provider = provider
        self.model = model
        if "gpt" in model:
            self.max_output_tokens = 3800
        else:
            self.max_output_tokens = 8192

    def to_dict(self) -> Dict[str, Any]:
        """Convert the PromptPlan object to a dictionary."""
        return {
            "context": self.context,
            "context_file_paths": self.context_file_paths,
            "user_keys": self.user_keys,
            "model": self.model,
            "json_required": self.json_required,
            "generation_config": self.generation_config,
            "system_instructions_dict_file_path": self.system_instructions_dict_file_path,
            "list_of_system_keys": self.list_of_system_keys,
            "user_prompt": self.user_prompt,
            "user_prompt_override": self.user_prompt_override,
            "user_prompts_dict_file_path": self.user_prompts_dict_file_path,
            "list_of_user_keys_to_use": self.list_of_user_keys_to_use,
            "user_prompts_dict": self.user_prompts_dict,
            "continuation_prompts": self.continuation_prompts,
            "output_file_base_name": self.output_file_path,
            "thisdoc_dir": self.thisdoc_dir,
            "log_level": self.logger.level,
            "number_to_run": self.number_to_run,
            "minimum_required_output_tokens": self.minimum_required_output_tokens,
            "provider": getattr(self, 'provider', None),
            "model": self.model,
            "final_prompts": self.final_prompts,
            "mode": self.mode,
            "use_all_user_keys": self.use_all_user_keys
        }

    def save_config(self, file_path: str) -> None:
        """Save the current configuration to a JSON file."""
        try:
            with open(file_path, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
            self.logger.info(f"Configuration saved to {file_path}")
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")

    def update_from_dict(self, config: Dict[str, Any]) -> None:
        """Update the PromptPlan object from a dictionary."""
        for key, value in config.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.final_prompts = self.prepare_final_prompts()

    def add_context(self, new_context: str) -> None:
        """Add new context to the existing context."""
        self.context += f"\n\n{new_context}"

    def add_prompt(self, new_prompt: str) -> None:
        """Add a new prompt to the list of final prompts."""
        self.final_prompts.append(new_prompt)

    def clear_prompts(self) -> None:
        """Clear all prompts."""
        self.final_prompts = []

    def __str__(self) -> str:
        """String representation of the PromptPlan object."""
        return f"PromptPlan(mode={self.mode}, model={self.model}, prompts={len(self.final_prompts)})"

    def __repr__(self) -> str:
        """Detailed string representation of the PromptPlan object."""
        return f"PromptPlan({self.to_dict()})"

    # def load_json_file(self, file_name):
    #     try:
    #         # Use the imported load_json function
    #         return load_json(os.path.join(resources.files('Codexes2Gemini.resources.prompts'), file_name))
    #     except Exception as e:
    #         st.error(f"Error loading JSON file: {e}")
    #         return {}