import json
import logging
import os
from collections import OrderedDict
import streamlit as st
import pymupdf as fitz  # PyMuPDF
from typing import List, Dict, Any, Union


class PromptPlan(OrderedDict):
    def __init__(self, context: str = "", context_file_paths: List[str] = None, user_keys: List[str] = None,
                 thisdoc_dir: str = "", json_required: bool = False, generation_config: dict = None,
                 system_instructions_dict_file_path: str = None, list_of_system_keys: str = None,
                 user_prompt: str = "", user_prompt_override: bool = False,
                 user_prompts_dict_file_path: str = None,
                 list_of_user_keys_to_use: List[str] = None,  # Changed to List[str]
                 continuation_prompts: bool = False,
                 output_file_path: str = None, log_level: str = "INFO", number_to_run: int = 1,
                 minimum_required_output_tokens: int = 1, ensure_output_limit = False,
                 model_name: str = None, mode: str = "part",
                 config_file: str = None, use_all_user_keys: bool = False, add_system_prompt: str = "") -> None:


        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)

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
        self.output_file_path = output_file_path
        self.number_to_run = number_to_run
        self.ensure_output_limit = ensure_output_limit
        self.minimum_required_output_tokens = minimum_required_output_tokens
        self.model = model_name
        self.mode = mode
        self.use_all_user_keys = use_all_user_keys
        self.user_prompts_dict = self.load_user_prompts_dict()
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

    def load_user_prompts_dict(self) -> Dict[str, Dict[str, Union[str, List[str]]]]:
        """Load user prompts from a JSON file."""
        if self.user_prompts_dict_file_path:
            try:
                with open(self.user_prompts_dict_file_path, 'r') as f:
                    data = json.load(f)
                    return data
            except Exception as e:
                self.logger.error(f"Error loading user prompts dict {self.user_prompts_dict_file_path}: {e}")
        return {}

    def prepare_final_prompts(self) -> List[str]:

       # print(f"{self.user_prompt_override},{self.user_prompt}, {self.use_all_user_keys},{self.list_of_user_keys_to_use}, {self.user_prompts_dict}")
        """Prepare the final list of prompts to be used."""
        self.logger.info(
            f"Preparing final prompts. User prompt override: {self.user_prompt_override}, User prompt: {self.user_prompt}")
        self.logger.info(
            f"Use all user keys: {self.use_all_user_keys}, List of user keys to use: {self.list_of_user_keys_to_use}")

        if self.user_prompt_override == "Override other user prompts" and self.user_prompt:
            self.logger.info("Overriding selected users prompts in favor of input box")
            return [self.user_prompt]

        final_prompts = []
        if self.use_all_user_keys and self.user_prompts_dict:
            self.logger.debug("Using all prompts from user_prompts_dict")
            final_prompts = list(self.user_prompts_dict.values())
        elif self.list_of_user_keys_to_use and self.user_prompts_dict:
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
            "output_file_path": self.output_file_path,
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