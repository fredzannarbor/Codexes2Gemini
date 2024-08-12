import argparse
import json
import logging
import os
import uuid
from importlib import resources
from typing import Dict

import google.generativeai as genai
import pypandoc
import streamlit as st

from Codexes2Gemini.classes.Codexes.Builders.PromptPlan import PromptPlan
from ..Builders.CodexBuilder import CodexBuilder
from ..Builders.PartsBuilder import PartsBuilder
from ...Utilities.utilities import configure_logger

GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']
class BuildLauncher:
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
                with resources.files('Codexes2Gemini.resources.prompts').joinpath(file_name).open('r') as file:
                    return json.load(file)
            except Exception as e:
                logging.error(f"Error loading JSON file {file_name}: {e}")
                return {}

    def create_prompt_plan(self, config: Dict) -> PromptPlan:
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
            'user_prompts_dict': config.get('user_prompts_dict', {})  # Add this line
        }
        # Remove None values to avoid passing unnecessary keyword arguments
        prompt_plan_params = {k: v for k, v in prompt_plan_params.items() if v is not None}
        return PromptPlan(**prompt_plan_params)
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

        # Set up logging
        log_level = args.get('log_level', 'INFO') if isinstance(args, dict) else args.log_level
        self.logger = configure_logger(log_level)

        # Create plans
        plans = self.create_plans(args)

        self.logger.debug(f"Number of plans created: {len(plans)}")
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
            result = self.process_plan(plan)
            if result is not None:
                results.append(result)
                self.save_result(plan, result)

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
        elif plan.mode == 'multi_part':
            return self.parts_builder.build_multi_part(plan)
        elif plan.mode == 'codex':
            return self.codex_builder.build_codex_from_plan(plan)
        elif plan.mode == 'full_codex':
            return self.codex_builder.build_codex_from_multiple_plans([plan])
        else:
            self.logger.error(f"Invalid mode specified for plan: {plan.mode}")
            return None

    def save_result(self, plan, result):
        if plan.minimum_required_output:
            st.info(f"Ensuring that output is at least minimum length {plan.minimum_required_output_tokens}")
            result = self.parts_builder.ensure_output_limit(result, plan.minimum_required_output_tokens)
        else:
            logging.info("Any output length OK.")

        unique_filename = f"{plan.thisdoc_dir}/{plan.output_file_path}_{str(uuid.uuid4())[:6]}"
        with open(unique_filename + ".md", 'w') as f:
            f.write(result)
        with open(unique_filename + '.json', 'w') as f:
            json.dump(result, f, indent=4)
        self.logger.info(f"Output written to {unique_filename}.md and {unique_filename}.json")
        mainfont = 'Skolar PE'
        extra_args = ['--toc', '--toc-depth=2', '--pdf-engine=xelatex', '-V', f'mainfont={mainfont}',
                      '--pdf-engine=xelatex']
        try:
            pypandoc.convert_text(result, 'pdf', format='markdown', outputfile=unique_filename + ".pdf",
                                  extra_args=extra_args)
            self.logger.info(f"PDF saved to {unique_filename}.pdf")
        except FileNotFoundError:
            self.logger.error("Pyandoc not found. Please install the pypandoc library to generate PDF.")


if __name__ == "__main__":
    launcher = BuildLauncher()
    launcher.main()