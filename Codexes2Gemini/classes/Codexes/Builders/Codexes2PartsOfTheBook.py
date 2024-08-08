import argparse
import json
import logging
import os
import traceback
from importlib import resources
from time import sleep
from typing import List
import streamlit as st


from Codexes2Gemini.classes.Utilities.utilities import configure_logger

import google.generativeai as genai
import pandas as pd

from ..Builders.PromptPlan import PromptPlan

GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']

configure_logger("DEBUG")

class Codexes2Parts:
    """
    Class: Codexes2Parts

    The Codexes2Parts class is responsible for processing codexes and generating book parts based on a given plan. It provides methods for configuring the API, creating a model, processing the codex to book part, generating a full book, and more.

    Attributes:
    - logger: A logger object for logging messages and debugging information.
    - model_name: A string representing the name of the generative model.
    - generation_config: A dictionary representing the configuration for generation.
    - safety_settings: A list of dictionaries representing the safety settings.
    - system_instructions_dict_file_path: A string representing the file path of the system instructions dictionary.
    - continuation_instruction: A string representing the instruction for continuation prompts.
    - results: A list to store the final results.

    Methods:
    - configure_api(): Configures the API with the Google API key.
    - create_model(model_name, safety_settings, generation_config): Creates a generative model based on the given parameters.
    - process_codex_to_book_part(plan): Processes the codex to generate book parts based on the given plan.
    - read_and_prepare_context(plan): Reads and prepares the context for processing.
    - assemble_system_prompt(plan): Assembles the system prompt based on the plan and system instruction dictionary.
    - generate_full_book(plans): Generates a full book based on the given plans.
    - gemini_get_response(plan, system_prompt, user_prompt, context, model): Makes a request to the Gemini API to get a response.
    - make_thisdoc_dir(plan): Creates a directory to store the output file.

    Note: This class relies on external dependencies such as the `logging` module, `os` module, `genai` module, `json` module, `pd` module, `traceback` module, and `sleep` function.
    """
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
        self.system_instructions_dict_file_path = resources.files('Codexes2Gemini.resources.prompts').joinpath("system_instructions.json")
        self.continuation_instruction = "The context now includes a section called {Work So Far} which includes your work on this book project so far. Please refer to it along with the context document as you carry out the following task."
        self.results=[]
        self.add_system_prompt = ""
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
        self.logger.debug(f"Context prepared, length: {self.count_tokens(context)} tokens")

        model = self.create_model(self.model_name, self.safety_settings, plan.generation_config)
        self.logger.debug("Model created")

        system_prompt = self.assemble_system_prompt(plan)
        self.logger.debug(f"System prompt assembled, length: {self.count_tokens(system_prompt)}")

        user_prompts = plan.get_prompts()
        self.logger.debug(f"User prompts retrieved: {user_prompts}")

        satisfactory_results = []

        for i, user_prompt in enumerate(user_prompts):
            self.logger.info(f"Processing user prompt {i + 1}/{len(user_prompts)}")
            full_output = " "
            retry_count = 0
            max_retries = 3

            full_output_tokens = self.count_tokens(full_output)
            while full_output_tokens < plan.minimum_required_output_tokens and retry_count < max_retries:
                try:
                    response = self.gemini_get_response(plan, system_prompt, user_prompt, context, model)
                    self.logger.debug(f"Response received, length: {self.count_tokens(response.text)} tokens")
                    full_output += response.text
                    full_output_tokens = self.count_tokens(full_output)

                    if full_output_tokens < plan.minimum_required_output_tokens:
                        self.logger.info(
                            f"Output length ({full_output_tokens})  tokens is less than desired length ({plan.minimum_required_output_tokens}). Retrying.")
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

            self.logger.info(f"Final output length for prompt {i + 1}: {full_output_tokens}")
            st.write(f"full output tokens: {full_output_tokens}\n")
            st.write(f"plan.minimum_required_output: {plan.minimum_required_output}")
            st.write(f"plan.minimum_required_output_tokens: {plan.minimum_required_output_tokens}")



            if full_output_tokens >= plan.minimum_required_output_tokens:
                satisfactory_results.append(full_output)
                self.logger.info(f"Output for prompt {i + 1} meets desired length. Appending to results.")
            else:

                self.logger.warning(
                    f"Output for prompt {i + 1} does not meet desired length of {plan.minimum_required_output_tokens}. Discarding.")

            if satisfactory_results:
                    self.logger.info(f"Returning satisfactory results of {self.count_tokens(satisfactory_results)}")
            else:
                self.logger.warning("No satisfactory results were generated.")
            return "\n\n".join(satisfactory_results)  # Return only satisfactory results joined together



    def count_tokens(self, text, model='models/gemini-1.5-pro'):
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel(model)
        # if text is None or empty string
        if text is None or text == "":
            return 0
        response = model.count_tokens(text)
        return response.total_tokens


    def read_and_prepare_context(self, plan):
        context_content = plan.context or ""
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
        token_count = self.count_tokens(context_content)
        context_msg = f"Uploaded context of {token_count} tokens"
        self.logger.debug(context_msg)
        st.info(context_msg)
        return f"Context: {context_content.strip()}\n\n"



    def tokens_to_millions(tokens):
        return tokens / 1_000_000

    def assemble_system_prompt(self, plan):
        system_prompt = ''
        with open(self.system_instructions_dict_file_path, "r") as json_file:
            system_instruction_dict = json.load(json_file)
        list_of_system_keys = plan.list_of_system_keys if isinstance(plan.list_of_system_keys,
                                                                     list) else plan.list_of_system_keys.split(',')
        for key in list_of_system_keys:
            key = key.strip()  # Remove any leading/trailing whitespace
            print(system_instruction_dict[key]['prompt'])
            try:
                system_prompt += system_instruction_dict[key]['prompt']
            except KeyError as e:
                self.logger.error(f"System instruction key {key} not found: {e}")
        if self.add_system_prompt:
            system_prompt += self.add_system_prompt

        return system_prompt

    def generate_full_book(self, plans: List[PromptPlan]):
        return [self.process_codex_to_book_part(plan) for plan in plans]


    def gemini_get_response(self, plan, system_prompt, user_prompt, context, model):
        self.configure_api()
        MODEL_GENERATION_ATTEMPTS = 15
        RETRY_DELAY_SECONDS = 10

        prompt = [system_prompt, user_prompt, context]

        prompt_stats = f"system prompt: {self.count_tokens(system_prompt)} tokens {system_prompt[:64]}\nuser_prompt: {len(user_prompt)} {user_prompt[:64]}\ncontext: {len(context)} {context[:52]}"
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
        if not plan.thisdoc_dir:
            plan.thisdoc_dir = os.path.join(os.getcwd(), 'output')

        if not os.path.exists(plan.thisdoc_dir):
            os.makedirs(plan.thisdoc_dir)
        print(f"thisdoc_dir is {plan.thisdoc_dir}")

def parse_arguments():
    parser = argparse.ArgumentParser(description="Run CodexesToBookParts with provided arguments")
    parser.add_argument('--model', default="gemini-1.5-flash-001", help="Model to use")
    parser.add_argument('--json_required', action='store_true', help="Require JSON output")
    parser.add_argument('--generation_config', type=str, default='{"temperature": 1, "top_p": 0.95, "top_k": 0, "max_output_tokens": 8192}', help="Generation config as a JSON string")
    parser.add_argument('--system_instructions_dict_file_path', default="resources/prompts/system_instructions.json", help="Path to system instructions dictionary file")
    parser.add_argument('--list_of_system_keys', default="nimble_books_editor,nimble_books_safety_scope,accurate_researcher,energetic_behavior,batch_intro", help="Comma-separated list of system keys")
    parser.add_argument('--user_prompt', default='', help="User prompt")
    parser.add_argument('--user_prompt_override', action='store_true', help="Override user prompts from dictionary")
    parser.add_argument('--user_prompts_dict_file_path', default=resources.files('Codexes2Gemini.resources.prompts').joinpath("user_prompts_dict.json"), help="Path to user prompts dictionary file")
    parser.add_argument('--list_of_user_keys_to_use', default="semantic_analysis,core_audience_attributes", help="Comma-separated list of user keys to use")
    parser.add_argument('--continuation_prompts', action='store_true', help="Use continuation prompts")
    parser.add_argument('--context_file_paths', nargs='+', help="Paths to context files")
    parser.add_argument('--output_file_path', default="results.md", help="Path to output file")
    parser.add_argument('--thisdoc_dir', default="output/c2g/", help="Document directory")
    parser.add_argument('--log_level', default="INFO", help="Logging level")
    parser.add_argument('--number_to_run', type=int, default=3, help="Number of runs")
    parser.add_argument('--minimum_required_output_tokens', "-do", type=int, default=1000, help="Desired output length in characters")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()

    c2b = Codexes2Parts()

    plan = PromptPlan(
        context_file_paths=args.context_file_paths,
        user_keys=[args.list_of_user_keys_to_use.split(',')[0]],
        thisdoc_dir=args.thisdoc_dir,
        model_name=args.model,
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
        minimum_required_output_tokens=args.minimum_required_output_tokens
    )

    book_part = c2b.process_codex_to_book_part(plan)

    print(f"Generated book part.")