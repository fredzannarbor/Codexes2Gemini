import argparse
import json
import logging
import os
import uuid
from importlib import resources
from typing import Dict

import google.generativeai as genai
import streamlit as st

from Codexes2Gemini.classes.Codexes.Builders.PromptGroups import PromptGroups
# from classes.Codexes.Fetchers.pg19Fetcher_v2 import save_markdown_results_with_latex_to_pdf
from ..Builders.CodexBuilder import CodexBuilder
from ..Builders.PartsBuilder import PartsBuilder
from ...Utilities.classes_utilities import configure_logger

GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']
class BuildLauncher:
    """
    Class representing the BuildLauncher.

    Attributes:
        parts_builder (PartsBuilder): An instance of the PartsBuilder class.
        codex_builder (CodexBuilder): An instance of the CodexBuilder class.
        logger (logging.Logger): A logger instance.
        user_prompts_dict (dict): A dictionary containing user prompts.
        system_instructions_dict (dict): A dictionary containing system instructions.

    Methods:
        parse_arguments() -> argparse.Namespace:
            Parses the command line arguments and returns a Namespace object.

        load_prompt_dictionaries() -> dict:
            Loads the user prompts and system instructions dictionaries from JSON files.

        create_prompt_plan(config: Dict) -> PromptGroups:
            Creates a PromptGroups object based on the provided configuration.

        load_plans_from_json(json_data) -> List[PromptGroups]:
            Loads PromptGroups objects from a JSON file or dictionary.

        main(args=None) -> List:
            The main entry point of the BuildLauncher class. Executes the provided plans and returns the results.

        create_plans(args) -> List[PromptGroups]:
            Creates a list of PromptGroups objects based on the provided arguments.

        create_plans_from_multiplan(args) -> List[PromptGroups]:
            Creates PromptGroups objects from a multiplan configuration.

        create_plans_from_json(plans_data) -> List[PromptGroups]:
            Creates PromptGroups objects from a JSON data structure.

        process_plan(plan: PromptGroups) -> Any:
            Processes a PromptGroups and returns the result based on the mode.

        save_result(plan: PromptGroups, result: Any) -> None:
            Saves the result to files and logs the output paths.
    """
    def __init__(self):
        self.parts_builder = PartsBuilder()
        self.codex_builder = CodexBuilder()
        self.logger = logging.getLogger(__name__)
        genai.configure(api_key=GOOGLE_API_KEY)  # Replace with your actual API key
        self.user_prompts_dict = {}
        self.system_instructions_dict = {}

    def parse_arguments(self):
        parser = argparse.ArgumentParser(description="Book Part and Codex Generator Launcher")
        parser.add_argument('--config', type=str, help='Path to JSON configuration file')
        parser.add_argument('--mode', choices=['part', 'multi_part', 'codex', 'full_codex'],
                            help='Mode of operation: part, multi_part, codex, or full_codex')
        parser.add_argument('--context_file_paths', nargs='+',
                            help='List of paths to context files (txt, pdf, epub, mobi)')
        parser.add_argument('--output', type=str, help='Output file path')
        parser.add_argument('--limit', type=int, default=10000, help='Output size limit in tokens')
        parser.add_argument('--user_prompt', type=str, help='User prompt')
        parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                            default='INFO', help='Set the logging level')
        parser.add_argument('--use-all-user-keys', action='store_true',
                            help='Use all user keys from the user prompts dictionary file')
        parser.add_argument('--minimum_required_output_tokens', '-do', type=int, default=5000, help='Desired output length')
        parser.add_argument('--plans_json', type=str, help='Path to JSON file containing multiple plans')
        return parser.parse_args()

    def load_prompt_dictionaries(self):
        dictionaries = ['user_prompts_dict.json', 'system_instructions_dict.json']
        for file_name in dictionaries:
            try:
                with resources.files('resources.prompts').joinpath(file_name).open('r') as file:
                    return json.load(file)
            except Exception as e:
                logging.error(f"Error loading JSON file {file_name}: {e}")
                return {}

    def create_prompt_plan(self, config: Dict) -> PromptGroups:
        # st.info(type(config['selected_user_prompts_dict']))
        prompt_plan_params = {
            'context': config.get('context', ''),
            'user_keys': config.get('user_keys', []),
            'thisdoc_dir': config.get('thisdoc_dir') or os.path.join(os.getcwd(), 'output'),
            'json_required': config.get('json_required', False),
            'generation_config': config.get('generation_config'),
            'system_instructions_dict_file_path': config.get('system_instructions_dict_file_path'),
            'user_prompt': config.get('user_prompt', ''),
            'list_of_system_keys': config.get('list_of_system_keys', []),
            'list_of_user_keys_to_use': config.get('list_of_user_keys_to_use', []),
            'user_prompt_override': config.get('user_prompt_override', False),
            'continuation_prompts': config.get('continuation_prompts', False),
            'output_file_base_name': config.get('output_file_base_name'),
            'log_level': config.get('log_level', 'INFO'),
            'number_to_run': config.get('number_to_run', 1),
            'minimum_required_output_tokens': config.get('minimum_required_output_tokens'),
            'model_name': config.get('model_name'),
            'mode': config.get('mode'),
            'use_all_user_keys': config.get('use_all_user_keys', False),
            'add_system_prompt': config.get('add_system_prompt', ''),
            'user_prompts_dict': config.get('user_prompts_dict', {}),
            'complete_user_prompt': config.get('complete_user_prompt', ""),
            'selected_system_instruction_keys': config.get('selected_system_instruction_keys', []),
            'selected_user_prompts_dict': config.get('selected_user_prompts_dict', {})
        }
        # Remove None values to avoid passing unnecessary keyword arguments
        prompt_plan_params = {k: v for k, v in prompt_plan_params.items() if v is not None}
        st.info(prompt_plan_params['selected_user_prompts_dict'])
        return PromptGroups(**prompt_plan_params)

    def load_plans_from_json(self, json_data):
        if isinstance(json_data, dict):
            # If json_data is already a dictionary, use it directly
            data = json_data
        elif isinstance(json_data, str):
            # If json_data is a file path
            with open(json_data, 'r') as f:
                data = json.load(f)
        elif hasattr(json_data, 'read'):
            # If json_data is a file-like object (e.g., StringIO or file object)
            data = json.load(json_data)
        else:
            raise TypeError("Expected a dict, str (file path), or file-like object")

        return [self.create_prompt_plan(plan_config) for plan_config in data['plans']]

    def main(self, args=None):
        if args is None:
            args = self.parse_arguments()
        elif not isinstance(args, (dict, argparse.Namespace)):
            raise TypeError("args must be either a dictionary or an argparse.Namespace object")
        # st.write(args)
        # Set up logging
        log_level = args.get('log_level', 'INFO') if isinstance(args, dict) else args.log_level
        self.logger = configure_logger(log_level)

        # Create plans
        plans = self.create_plans(args)

        self.logger.debug(f"Number of plans created: {len(plans)}")
        st.info(f"Number of plans created: {len(plans)}")
        for i, plan in enumerate(plans):
            self.logger.debug(f"Plan {i + 1}: {plan}")

        # Check for empty contexts
        for plan in plans:
            if not plan.context_file_paths and not plan.context:
                self.logger.warning(f"Plan {plan.mode} has no context. This may affect the output quality.")

        # Process plans
        results = []
        for plan in plans:
            #st.write(plan)
            plan_result = self.process_plan(plan)
            # st.write(plan_result)
            # st.write("plan result ^")
            if plan_result is not None:
                results.append(plan_result)
                self.save_result_to_file_system(plan, plan_result)

            return results

    def create_plans(self, args):
        if isinstance(args, dict) and 'multiplan' in args:
            return self.create_plans_from_multiplan(args)
        elif isinstance(args, dict) and 'plans_json' in args:
            return self.create_plans_from_json(args['plans_json'])
        elif hasattr(args, 'plans_json') and args.plans_json:
            with open(args.plans_json, 'r') as f:
                plans_data = json.load(f)
            return self.create_plans_from_json(plans_data)
        else:
            config = args if isinstance(args, dict) else vars(args)

            # st.write(config)
            # st.write("config ^")
            return [self.create_prompt_plan(config)]

    def create_plans_from_multiplan(self, args):
        plans = []
        for plan_config in args['multiplan']:
            plan_config['context'] = plan_config.get('context', '')
            if 'context_files' in plan_config:
                plan_config['context'] += "\n".join(plan_config['context_files'].values())
            plan_config['minimum_required_output_tokens'] = plan_config.get('minimum_required_output_tokens', 1000)
            plan_config['user_prompts_dict'] = args.get('user_prompts_dict', {})
            plans.append(self.create_prompt_plan(plan_config))
        return plans

    def create_plans_from_json(self, plans_data):
        return [self.create_prompt_plan(plan_config) for plan_config in plans_data['plans']]

    def process_plan(self, plan):
        if plan.mode == 'part':
            return self.parts_builder.build_part(plan)
        # elif plan.mode == 'multi_part':
        #     return self.parts_builder.build_multi_part(plan)
        elif plan.mode == 'codex':
            return self.codex_builder.build_codex_from_plan(plan)
        # elif plan.mode == 'full_codex':
        #     return self.codex_builder.build_codex_from_multiple_plans([plan])
        else:
            self.logger.error(f"Invalid mode specified for plan: {plan.mode}")
            return None

    def save_result_to_file_system(self, plan, result):
        if plan.minimum_required_output:
            st.info(f"Ensuring that output is at least minimum length {plan.minimum_required_output_tokens}")
            result = self.parts_builder.ensure_output_limit(result, plan.minimum_required_output_tokens)
        else:
            logging.info("Any output length OK.")

        unique_filename = f"{plan.thisdoc_dir}/{plan.output_file}_{str(uuid.uuid4())[:6]}"

        # convert markdown list to string
        md_result = "\n".join(result)
        with open(unique_filename + ".md", 'w') as f:
            f.write(md_result)
        with open(unique_filename + '.json', 'w') as f:
            json.dump(result, f, indent=4)
        self.logger.info(f"Output written to {unique_filename}.md and {unique_filename}.json")
        save_markdown_results_with_latex_to_pdf(self.logger, md_result, unique_filename)


if __name__ == "__main__":
    launcher = BuildLauncher()
    launcher.main()