import argparse
import json
import logging
import os
import traceback
from importlib import resources
from time import sleep

import google.generativeai as genai
import pandas as pd
import streamlit as st

from Codexes2Gemini.classes.Utilities.utilities import configure_logger
from ..Builders.PromptPlan import PromptPlan

GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']

configure_logger("DEBUG")

class Codexes2Parts:
    """
    Class for processing Codexes to create book parts.

    Attributes:
        logger (Logger): Logger instance for logging information.
        model_name (str): Name of the generative model to use.
        generation_config (dict): Configuration for generation process.
        safety_settings (list): List of safety settings for blocking harmful content.
        system_instructions_dict_file_path (str): Path to the system instructions dictionary file.
        continuation_instruction (str): Instruction for continuation prompts.
        results (list): List to store the generated book parts.
        add_system_prompt (str): Additional system prompt.

    Methods:
        configure_api(): Configures the API key.
        create_model(model_name, safety_settings, generation_config): Creates a generative model.
        process_codex_to_book_part(plan): Processes the Codex to generate a book part.
        count_tokens(text, model): Counts the number of tokens in a text.
        read_and_prepare_context(plan): Reads and prepares the context for generation.
        tokens_to_millions(tokens): Converts the number of tokens to millions.
        assemble_system_prompt(plan): Assembles the system prompt for generation.
        generate_full_book(plans): Generates the full book from a list of plans.
        gemini_get_response(plan, system_prompt, user_prompt, context, model): Calls the Gemini API to get the response.
        make_thisdoc_dir(plan): Creates the directory for the book part output.
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
        self.complete_system_instruction = ""

    def configure_api(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise EnvironmentError("GOOGLE_API_KEY environment variable is not set.")
        genai.configure(api_key=api_key)

    def create_model(self, model_name, safety_settings, generation_config):
        return genai.GenerativeModel(model_name, safety_settings=safety_settings, generation_config=generation_config)

    def create_response_dict(self, response):

        response_dict = {
            "text": response.text,
            "prompt_feedback": response.prompt_feedback,
            "candidates": [
                {
                    "content": candidate.content,
                    "finish_reason": candidate.finish_reason,
                    "safety_ratings": [
                        {
                            "category": rating.category,
                            "probability": rating.probability
                        } for rating in candidate.safety_ratings
                    ]
                } for candidate in response.candidates
            ]
        }

        return response_dict

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
        self.logger.info(f"\nUser prompts retrieved: {user_prompts}")

        satisfactory_results = []
        #st.info('here')

        for i, user_prompt in enumerate(user_prompts):
            self.logger.info(f"Processing user prompt {i + 1}/{len(user_prompts)}")
            # st.info(f"Processing user prompt {i + 1}/{len(user_prompts)}")
            # st.info(f"This user prompt is {user_prompt}")
            full_output = " "
            retry_count = 0
            max_retries = 3

            full_output_tokens = self.count_tokens(full_output)
            while full_output_tokens < plan.minimum_required_output_tokens and retry_count < max_retries:
                try:
                    response = self.gemini_get_response(plan, system_prompt, user_prompt, context, model)
                    #st.info(user_prompt)
                    self.logger.debug(f"Response received, length: {self.count_tokens(response.text)} tokens")
                    json_response = self.create_response_dict(response)
                    st.json(json_response, expanded=False)
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
            self.logger.info(f"full output tokens: {full_output_tokens}\n")
            self.logger.info(f"plan.minimum_required_output: {plan.minimum_required_output}")
            self.logger.info(f"plan.minimum_required_output_tokens: {plan.minimum_required_output_tokens}")

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
            st.info(f"processed prompt {i + 1}")


return satisfactory_results
#"\n\n".join(satisfactory_results)  # Return only satisfactory results joined together



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
        if plan.complete_system_instruction:
            system_prompt = plan.complete_system_instruction
        else:
            with open(self.system_instructions_dict_file_path, "r") as json_file:
                system_instruction_dict = json.load(json_file)
            system_prompt = ""
            for key in plan.selected_system_instruction_keys:
                key = key.strip()
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
    parser.add_argument('--output_file_base_name', default="results.md", help="Path to output file")
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
        output_file_base_name=args.output_file_path,
        log_level=args.log_level,
        number_to_run=args.number_to_run,
        minimum_required_output_tokens=args.minimum_required_output_tokens
    )

    book_part = c2b.process_codex_to_book_part(plan)

    print(f"Generated book part.")