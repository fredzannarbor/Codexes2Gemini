import argparse
import os
import json
import logging
from importlib import resources
from typing import Dict
import uuid
import google.generativeai as genai

from ..Builders.PartsBuilder import PartsBuilder
from ..Builders.CodexBuilder import CodexBuilder
from ..Builders.PromptPlan import PromptPlan
from ...Utilities.utilities import configure_logger


class BuildLauncher:
    def __init__(self):
        self.parts_builder = PartsBuilder()
        self.codex_builder = CodexBuilder()
        self.logger = logging.getLogger(__name__)
        genai.configure(api_key="YOUR_API_KEY_HERE")  # Replace with your actual API key
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
            'context_file_paths': config.get('context_file_paths'),
            'user_keys': config.get('user_keys', []),
            'thisdoc_dir': config.get('thisdoc_dir') or os.path.join(os.getcwd(), 'output'),
            'json_required': config.get('json_required', False),
            'generation_config': config.get('generation_config'),
            'system_instructions_dict_file_path': config.get('system_instructions_dict_file_path'),
            'list_of_system_keys': config.get('list_of_system_keys'),
            'user_prompt': config.get('user_prompt', ''),
            'user_prompt_override': config.get('user_prompt_override', False),
            'user_prompts_dict_file_path': config.get('user_prompts_dict_file_path'),
            'list_of_user_keys_to_use': config.get('list_of_user_keys_to_use', []),
            'continuation_prompts': config.get('continuation_prompts', False),
            'output_file_path': config.get('output_file_path'),
            'log_level': config.get('log_level', 'INFO'),
            'number_to_run': config.get('number_to_run', 1),
            'minimum_required_output_tokens': config.get('minimum_required_output_tokens'),
            'model_name': config.get('model_name'),
            'mode': config.get('mode'),
            'use_all_user_keys': config.get('use_all_user_keys', False),
            'add_system_prompt': config.get('add_system_prompt', '')
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
        elif isinstance(args, dict):
            # If args is a dictionary, we'll use it as is
            pass
        elif not isinstance(args, argparse.Namespace):
            raise TypeError("args must be either a dictionary or an argparse.Namespace object")

        # Set up logging based on the provided log level
        log_level = args.get('log_level', 'INFO') if isinstance(args, dict) else args.log_level
        logger = configure_logger(log_level)

        # Load prompt dictionaries
        self.load_prompt_dictionaries()

        if isinstance(args, dict) and 'multiplan' in args:
            plans = []
            for plan_config in args['multiplan']:
                plan_config['context'] = plan_config.get('context', '')
                if 'context_files' in plan_config:
                    plan_config['context'] += "\n".join(plan_config['context_files'].values())
                plan_config['minimum_required_output_tokens'] = plan_config.get('minimum_required_output_tokens', 1000)
                plans.append(self.create_prompt_plan(plan_config))
        elif isinstance(args, dict) and 'plans_json' in args:
            plans_data = args['plans_json']
            plans = [self.create_prompt_plan(plan_config) for plan_config in plans_data['plans']]
        elif hasattr(args, 'plans_json') and args.plans_json:
            with open(args.plans_json, 'r') as f:
                plans_data = json.load(f)
            plans = [self.create_prompt_plan(plan_config) for plan_config in plans_data['plans']]
        else:
            # Use single plan
            config = args if isinstance(args, dict) else vars(args)
            plans = [self.create_prompt_plan(config)]

        for i, plan in enumerate(plans):
            self.logger.debug(f"Plan {i + 1}: {plan}")

        for plan in plans:
            if not plan.context_file_paths and not plan.context:
                logger.warning(f"Plan {plan.mode} has no context. This may affect the output quality.")

        results = []
        for plan in plans:
            if plan.mode == 'part':
                result = self.parts_builder.build_part(plan)
            elif plan.mode == 'multi_part':
                result = self.parts_builder.build_multi_part(plan)
            elif plan.mode == 'codex':
                result = self.codex_builder.build_codex_from_plan(plan)
            elif plan.mode == 'full_codex':
                result = self.codex_builder.build_codex_from_multiple_plans(plans)
                break  # Only need to run once for full_codex mode
            else:
                logger.error(f"Invalid mode specified for plan: {plan.mode}")
                continue
            if plan.ensure_output_limit:
                result = self.parts_builder.ensure_output_limit(result, plan.minimum_required_output_tokens)

            results.append(result)

            # Generate a unique filename for each plan
            unique_filename = f"{plan.output_file_path}_{str(uuid.uuid4())[:6]}"
            with open(unique_filename + ".md", 'w') as f:
                f.write(result)
                logger.info(f"Output written to {unique_filename}.md")
            with open(unique_filename + '.json', 'w') as f:
                f.write(json.dumps(result, indent=4))
                logger.info(f"Output written to {unique_filename}.json")
            logger.info(f"Output length {len(result)}")

        return results

if __name__ == "__main__":
    launcher = BuildLauncher()
    launcher.main()