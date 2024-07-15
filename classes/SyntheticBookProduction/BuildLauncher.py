import os
import argparse
import json
import logging
from typing import List, Dict
import google.generativeai as genai
from PartsBuilder import PartsBuilder
from CodexBuilder import CodexBuilder
from classes.SyntheticBookProduction.PromptPlan import PromptPlan
import uuid

class BuildLauncher:
    def __init__(self):
        self.parts_builder = PartsBuilder()
        self.codex_builder = CodexBuilder()
        self.logger = logging.getLogger(__name__)
        genai.configure(api_key="YOUR_API_KEY_HERE")  # Replace with your actual API key

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
        parser.add_argument('--desired_output_length', '-do', type=int, default=5000, help='Desired output length')
        parser.add_argument('--plans_json', type=str, help='Path to JSON file containing multiple plans')
        return parser.parse_args()

    def load_config(self, config_path: str) -> Dict:
        with open(config_path, 'r') as f:
            return json.load(f)

    def create_prompt_plan(self, config: Dict) -> PromptPlan:
        prompt_plan_params = {
            'context': config.get('context', ''),
            'context_file_paths': config.get('context_file_paths'),
            'user_keys': config.get('user_keys', []),
            'thisdoc_dir': config.get('thisdoc_dir', ''),
            'json_required': config.get('json_required', False),
            'generation_config': config.get('generation_config'),
            'system_instructions_dict_file_path': config.get('system_instructions_dict_file_path'),
            'list_of_system_keys': config.get('list_of_system_keys'),
            'user_prompt': config.get('user_prompt', ''),
            'user_prompt_override': config.get('user_prompt_override', False),
            'user_prompts_dict_file_path': config.get('user_prompts_dict_file_path'),
            'list_of_user_keys_to_use': config.get('list_of_user_keys_to_use'),
            'continuation_prompts': config.get('continuation_prompts', False),
            'output_file_path': config.get('output_file_path'),
            'log_level': config.get('log_level', 'INFO'),
            'number_to_run': config.get('number_to_run', 1),
            'desired_output_length': config.get('desired_output_length'),
            'model_name': config.get('model'),
            'mode': config.get('mode'),
            'use_all_user_keys': config.get('use_all_user_keys', False)
        }
        # Remove None values to avoid passing unnecessary keyword arguments
        prompt_plan_params = {k: v for k, v in prompt_plan_params.items() if v is not None}
        return PromptPlan(**prompt_plan_params)

    def load_plans_from_json(self, json_file_path):
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        return [self.create_prompt_plan(plan_config) for plan_config in data['plans']]

    def main(self):
        args = self.parse_arguments()

        if args.plans_json:
            plans = self.load_plans_from_json(args.plans_json)
        else:
            # Use single plan as before
            config = self.load_config(args.config) if args.config else vars(args)
            plans = [self.create_prompt_plan(config)]

        for plan in plans:
            if not plan.context_file_paths and not plan.context:
                self.logger.warning(f"Plan {plan.mode} has no context. This may affect the output quality.")

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
                self.logger.error(f"Invalid mode specified for plan: {plan.mode}")
                continue

            result = self.parts_builder.ensure_output_limit(result, plan.desired_output_length)
            results.append(result)

            # Generate a unique filename for each plan
            unique_filename = f"{plan.output_file_path}_{str(uuid.uuid4())[:6]}"
            with open(unique_filename, 'w') as f:
                f.write(result)
            self.logger.info(f"Output written to {unique_filename}")

        return results

if __name__ == "__main__":
    launcher = BuildLauncher()
    launcher.main()