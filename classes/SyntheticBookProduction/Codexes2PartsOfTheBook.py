import argparse
import datetime
import json
import logging
import os
import traceback
from pprint import pprint
from time import sleep
from typing import List

import google.generativeai as genai
import pandas as pd

from classes.SyntheticBookProduction.PromptPlan import PromptPlan

YOUR_API_KEY = os.environ['GOOGLE_API_KEY']

class Codexes2Parts:
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.model_name = 'gemini-1.5-flash-001'
        self.generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 0,
            "max_output_tokens": 8192,
            "response_mime_type": "application/json"
        }
        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        self.system_instructions_dict_file_path = "resources/json/gemini_prompts/gemini_system_instructions.json"
        self.continuation_instruction = "The context now includes a section called {Work So Far} which includes your work on this book project so far. Please refer to it along with the context document as you carry out the following task."
        self.results=[]
    def configure_api(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise EnvironmentError("GOOGLE_API_KEY environment variable is not set.")
        genai.configure(api_key=api_key)

    def create_model(self, model_name, safety_settings, generation_config):
        return genai.GenerativeModel(model_name, safety_settings=safety_settings, generation_config=generation_config)

    def process_codex_to_book_part(self, plan: PromptPlan):
        self.logger.debug(f"Starting process_codex_to_book_part with plan: {plan}")
        self.make_thisdoc_dir(plan)
        context = self.read_and_prepare_context(plan)
        self.logger.debug(f"Context prepared, length: {len(context)}")

        model = self.create_model(self.model_name, self.safety_settings, plan.generation_config)
        self.logger.debug("Model created")

        system_prompt = self.assemble_system_prompt(plan)
        self.logger.debug(f"System prompt assembled, length: {len(system_prompt)}")

        user_prompts = plan.get_prompts()
        self.logger.debug(f"User prompts retrieved, count: {len(user_prompts)}")

        satisfactory_results = []

        for i, user_prompt in enumerate(user_prompts):
            self.logger.info(f"Processing user prompt {i + 1}/{len(user_prompts)}")
            full_output = ""
            retry_count = 0
            max_retries = 3

            while len(full_output) < plan.desired_output_length and retry_count < max_retries:
                try:
                    response = self.gemini_get_response(plan, system_prompt, user_prompt, context, model)
                    self.logger.debug(f"Response received, length: {len(response.text)}")
                    full_output += response.text

                    if len(full_output) < plan.desired_output_length:
                        self.logger.info(
                            f"Output length ({len(full_output)}) is less than desired length ({plan.desired_output_length}). Retrying.")
                        retry_count += 1
                        if plan.continuation_prompts:
                            context += f"\n\n{{Work So Far}}:\n\n{full_output}"
                            user_prompt = self.continuation_instruction.format(Work_So_Far=full_output)
                            self.logger.debug("Continuation prompt prepared")
                        else:
                            break  # If continuation prompts are not enabled, we stop here
                except Exception as e:
                    self.logger.error(f"Error in gemini_get_response: {e}")
                    retry_count += 1
                    self.logger.info(f"Retrying due to error. Retry count: {retry_count}")

            self.logger.info(f"Final output length for prompt {i + 1}: {len(full_output)}")

            if len(full_output) >= plan.desired_output_length:
                satisfactory_results.append(full_output)
                self.logger.info(f"Output for prompt {i + 1} meets desired length. Appending to results.")
            else:
                self.logger.warning(f"Output for prompt {i + 1} does not meet desired length of {plan.desired_output_length}. Discarding.")

        if satisfactory_results:
            try:
                with open(plan.output_file_path, 'a') as f:  # Changed to 'a' for append mode
                    for result in satisfactory_results:
                        f.write(f"{result}\n\n")
                self.logger.info(f"Satisfactory results appended to: {plan.output_file_path}")
            except Exception as e:
                self.logger.error(f"Trouble appending responses to file {plan.output_file_path}: {e}")
        else:
            self.logger.warning("No satisfactory results were generated. Nothing appended to the output file.")

        return "\n\n".join(satisfactory_results)  # Return only satisfactory results joined together

    def read_and_prepare_context(self, plan):
        context_content = ""
        if plan.context_file_paths:
            for file_path in plan.context_file_paths:
                if not file_path.strip():  # Skip empty file paths
                    self.logger.warning("Empty file path found in context_file_paths. Skipping.")
                    continue
                try:
                    with open(file_path, "r", encoding='utf-8') as f:
                        context_content += f.read() + "\n\n"
                except Exception as e:
                    self.logger.error(f"Error reading context file {file_path}: {e}")
        elif plan.context:
            context_content = plan.context
        else:
            self.logger.warning("No context files or context string provided. Context will be empty.")

        context_msg = f"Context is type {type(context_content)}, length {len(context_content)}"
        self.logger.debug(context_msg)
        return f"Context: {context_content.strip()}\n\n"

    def assemble_system_prompt(self, plan):
        system_prompt = ''
        with open(self.system_instructions_dict_file_path, "r") as json_file:
            system_instruction_dict = json.load(json_file)
        list_of_system_keys = plan.list_of_system_keys if isinstance(plan.list_of_system_keys,
                                                                     list) else plan.list_of_system_keys.split(',')
        for key in list_of_system_keys:
            key = key.strip()  # Remove any leading/trailing whitespace
            try:
                system_prompt += system_instruction_dict[key]
            except KeyError as e:
                self.logger.error(f"System instruction key {key} not found: {e}")
        return system_prompt

    def generate_full_book(self, plans: List[PromptPlan]):
        return [self.process_codex_to_book_part(plan) for plan in plans]


    def gemini_get_response(self, plan, system_prompt, user_prompt, context, model):
        self.configure_api()
        MODEL_GENERATION_ATTEMPTS = 15
        RETRY_DELAY_SECONDS = 10

        prompt = [system_prompt, user_prompt, context]

        prompt_stats = f"system prompt: {len(system_prompt)} {system_prompt[:64]}\nuser_prompt: {len(user_prompt)} {user_prompt[:64]}\ncontext: {len(context)} {context[:52]}"
        print(f"{prompt_stats}")
        prompt_df = pd.DataFrame(prompt)
        prompt_df.to_json(plan.thisdoc_dir + "/prompt.json", orient="records")

        for attempt_no in range(MODEL_GENERATION_ATTEMPTS):
            try:
                response = model.generate_content(prompt, request_options={"timeout": 600})
                return response
            except Exception as e:
                errormsg = traceback.format_exc()
                self.logger.error(f"Error generating content on attempt {attempt_no + 1}: {errormsg}")
                if attempt_no < MODEL_GENERATION_ATTEMPTS - 1:
                    sleep(RETRY_DELAY_SECONDS)
                else:
                    print("Max retries exceeded. Exiting.")
                    exit()

    def make_thisdoc_dir(self, plan):
        if not os.path.exists(plan.thisdoc_dir):
            os.makedirs(plan.thisdoc_dir)
        print(f"thisdoc_dir is {plan.thisdoc_dir}")

def parse_arguments():
    parser = argparse.ArgumentParser(description="Run CodexesToBookParts with provided arguments")
    parser.add_argument('--model', default="gemini-1.5-flash-001", help="Model to use")
    parser.add_argument('--json_required', action='store_true', help="Require JSON output")
    parser.add_argument('--generation_config', type=str, default='{"temperature": 1, "top_p": 0.95, "top_k": 0, "max_output_tokens": 8192}', help="Generation config as a JSON string")
    parser.add_argument('--system_instructions_dict_file_path', default="resources/json/gemini_system_instructions.json", help="Path to system instructions dictionary file")
    parser.add_argument('--list_of_system_keys', default="nimble_books_editor,nimble_books_safety_scope,accurate_researcher,energetic_behavior,batch_intro", help="Comma-separated list of system keys")
    parser.add_argument('--user_prompt', default='', help="User prompt")
    parser.add_argument('--user_prompt_override', action='store_true', help="Override user prompts from dictionary")
    parser.add_argument('--user_prompts_dict_file_path', default="resources/json/gemini_prompts/user_prompts_dict.json", help="Path to user prompts dictionary file")
    parser.add_argument('--list_of_user_keys_to_use', default="semantic_analysis,core_audience_attributes", help="Comma-separated list of user keys to use")
    parser.add_argument('--continuation_prompts', action='store_true', help="Use continuation prompts")
    parser.add_argument('--context_file_paths', nargs='+', help="Paths to context files")
    parser.add_argument('--output_file_path', default="results.md", help="Path to output file")
    parser.add_argument('--thisdoc_dir', default="output/gemini/", help="Document directory")
    parser.add_argument('--log_level', default="INFO", help="Logging level")
    parser.add_argument('--number_to_run', type=int, default=3, help="Number of runs")
    parser.add_argument('--desired_output_length', "-do", type=int, default=10000, help="Desired output length in characters")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()

    c2b = Codexes2Parts()

    plan = PromptPlan(
        context_file_paths=args.context_file_paths,
        user_keys=[args.list_of_user_keys_to_use.split(',')[0]],
        thisdoc_dir=args.thisdoc_dir,
        model=args.model,
        json_required=args.json_required,
        generation_config=json.loads(args.generation_config),
        system_instructions_dict_file_path=args.system_instructions_dict_file_path,
        list_of_system_keys=args.list_of_system_keys,
        user_prompt=args.user_prompt,
        user_prompt_override=args.user_prompt_override,
        user_prompts_dict_file_path=args.user_prompts_dict_file_path,
        list_of_user_keys_to_use=args.list_of_user_keys_to_use,
        continuation_prompts=args.continuation_prompts,
        output_file_path=args.output_file_path,
        log_level=args.log_level,
        number_to_run=args.number_to_run,
        desired_output_length=args.desired_output_length
    )

    book_part = c2b.process_codex_to_book_part(plan)

    print(f"Generated book part.")