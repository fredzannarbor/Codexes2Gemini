import json
import logging
import os
from typing import List, Dict, Any, Optional

import pymupdf as fitz  # PyMuPDF
import streamlit as st

from Codexes2Gemini.classes.Utilities.classes_utilities import configure_logger


# from classes.Utilities.utilities import configure_logger

class PromptGroups:

    def __init__(self, context: str = "", context_file_paths: List[str] = None, user_keys: List[str] = None,
                 thisdoc_dir: str = "", json_required: bool = False, generation_config: dict = None,
                 system_instructions_dict_file_path: str = None, list_of_system_keys: str = None,
                 user_prompt: str = "", user_prompt_override: bool = False,
                 user_prompts_dict: Dict[str, Any] = None,
                 user_prompts_dict_file_path: str = "user_prompts.json",
                 list_of_user_keys_to_use: List[str] = None,
                 continuation_prompts: bool = False,
                 output_file_base_name: str = "output",
                 log_level: str = "INFO",
                 number_to_run: int = 1,
                 minimum_required_output: bool = False,
                 minimum_required_output_tokens: int = 100,
                 maximum_output_tokens: int = 8000,
                 model_name: str = None, mode: str = "part",
                 complete_user_prompt: str = "",
                 complete_system_instruction: str = "",
                 selected_system_instruction_keys: List[str] = None,
                 selected_user_prompt_values: List[str] = None,
                 selected_user_prompts_dict: Dict[str, Any] = None,
                 selected_user_prompt_keys: List[str] = None,
                 config_file: str = None, use_all_user_keys: bool = False, add_system_prompt: str = "",
                 require_json_output=False, output_file: str = None) -> None:

        # st.info(type(selected_user_prompts_dict))
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)
        configure_logger(log_level)

        # Initialize attributes with default values
        self.context = context
        self.context_file_paths = context_file_paths or []
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
        self.list_of_system_keys = list_of_system_keys.split(',') if isinstance(list_of_system_keys,
                                                                                str) else list_of_system_keys or []
        self.user_prompt = user_prompt
        self.user_prompt_override = user_prompt_override
        self.user_prompts_dict = user_prompts_dict or {}
        self.user_prompts_dict_file_path = user_prompts_dict_file_path
        self.list_of_user_keys_to_use = list_of_user_keys_to_use or []
        self.continuation_prompts = continuation_prompts
        self.output_file_path = output_file_base_name
        self.output_file = output_file
        self.require_json_output = require_json_output
        self.number_to_run = number_to_run
        self.minimum_required_output = minimum_required_output
        self.minimum_required_output_tokens = minimum_required_output_tokens
        self.maximum_output_tokens = maximum_output_tokens
        self.model = model_name
        self.mode = mode
        self.complete_user_prompt = complete_user_prompt
        self.complete_system_instruction = complete_system_instruction
        self.selected_system_instruction_keys = selected_system_instruction_keys or []
        self.selected_user_prompt_values = selected_user_prompt_values or []
        self.selected_user_prompts_dict = selected_user_prompts_dict or {}
        self.selected_user_prompt_keys = selected_user_prompt_keys or []
        self.use_all_user_keys = use_all_user_keys
        self.add_system_prompt = add_system_prompt

        # If a config file is provided, load it
        if config_file:
            self.load_config(config_file)
        # st.info(type(self.selected_user_prompts_dict))
        # st.info(self.selected_user_prompts_dict)
        # st.info("at promptsgroup init^")
        # Prepare the final prompts
        self.final_prompts = self.prepare_final_user_prompts()

        # Log the initialization
        self.logger.info("PromptGroups initialized with the following attributes:")
        for attr, value in self.__dict__.items():
            self.logger.info(f"{attr}: {value}")

    def prepare_final_user_prompts(self) -> List[str]:
        self.logger.info("Preparing final user prompts.")

        final_prompts = []

        if self.selected_user_prompt_keys and self.selected_user_prompt_values:
            for key, value in zip(self.selected_user_prompt_keys, self.selected_user_prompt_values):
                final_prompts.append(f"{key}: {value}")

        if self.user_prompt_override:
            final_prompts = [self.custom_user_prompt]  # Override with custom prompt
        elif self.custom_user_prompt:
            final_prompts.append(self.custom_user_prompt)  # Append custom prompt

        return final_prompts

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


    def get_prompts(self) -> List[str]:
        """Return the final list of prompts."""
        return self.final_prompts

    def set_provider(self, provider: str, model: str) -> None:
        """Set the provider and model for the PromptGroups."""
        self.provider = provider
        self.model = model
        if "gpt" in model:
            self.max_output_tokens = 3800
        else:
            self.max_output_tokens = 8192

    def to_dict(self) -> Dict[str, Any]:
        """Convert the PromptGroups object to a dictionary."""
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
        """Update the PromptGroups object from a dictionary."""
        for key, value in config.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.final_prompts = self.prepare_final_user_prompts()

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
        """String representation of the PromptGroups object."""
        return f"PromptGroups(mode={self.mode}, model={self.model}, prompts={len(self.final_prompts)})"

    def __repr__(self) -> str:
        """Detailed string representation of the PromptGroups object."""
        return f"PromptGroups({self.to_dict()})"

    # def load_json_file(self, file_name):
    #     try:
    #         # Use the imported load_json function
    #         return load_json(os.path.join(resources.files('resources.prompts'), file_name))
    #     except Exception as e:
    #         st.error(f"Error loading JSON file: {e}")
    #         return {}