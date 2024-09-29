import argparse
import datetime
import json
import logging
import os
import traceback
import uuid
from importlib import resources
from time import sleep
from typing import List

import google.generativeai as genai
import pandas as pd
import streamlit as st
from google.generativeai import caching

from Codexes2Gemini.classes.Utilities.classes_utilities import configure_logger
from ..Builders.PromptGroups import PromptGroups

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
        self.system_instructions_dict_file_name = "system_instructions.json"
        self.continuation_instruction = "The context now includes a section beginning {Work So Far} which includes your work on this book project so far. Your task is to continue where you left off and write the next part of the project. You are not expected to finish the whole project now. Your writing for this task should be at the same level of detail as each individul section of the context. Try to write AT MINIMUM 2000 WORDS in this response.  Remember, do NOT try to complete the entire project all at once. Your priority is doing a thorough job on the current section. However, only once the project as a whole is COMPLETELY finished, with all requirements satisfied, write IAMDONE."
        self.results = []
        self.add_system_prompt = ""
        self.complete_system_instruction = ""

        self.system_instructions_dict_file_path = resources.files('resources.prompts').joinpath(
            self.system_instructions_dict_file_name)

        if not self.system_instructions_dict_file_path.exists():
            self.system_instructions_dict_file_path = "resources/prompts"

    def configure_api(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise EnvironmentError("GOOGLE_API_KEY environment variable is not set.")
        genai.configure(api_key=api_key)

    def create_model(self, model_name, safety_settings, generation_config, cache=None):
        if cache is not None:
            return genai.GenerativeModel.from_cached_content(
                cached_content=cache,
                generation_config=generation_config,
                safety_settings=safety_settings)
        else:
            return genai.GenerativeModel(
                model_name=model_name,
                safety_settings=safety_settings,
                generation_config=generation_config)

    def create_response_dict(self, response):

        response_dict = {
            "text": response.text,
            "prompt_feedback": response.prompt_feedback,
            "usage_metadata": response.usage_metadata,
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

    def process_codex_to_book_part(self, plan: PromptGroups):

        self.logger.debug(f"Starting process_codex_to_book_part with plan: {plan}")
        self.make_thisdoc_dir(plan)
        context = self.read_and_prepare_context(plan)
        self.logger.debug(f"Context prepared, length: {self.count_tokens(context)} tokens")
        # TODO: make sure this is available for all builder functions
        cache = self.create_cache_from_context(context)

        model = self.create_model(self.model_name, self.safety_settings, plan.generation_config, cache)
        self.logger.debug("Model created")

        system_prompt = self.assemble_system_prompt(plan)
        self.logger.debug(f"System prompt assembled, length: {self.count_tokens(system_prompt)}")

        user_prompts = plan.get_prompts()
        self.logger.info(f"\nUser prompts retrieved: {user_prompts}")

        satisfactory_results = []

        for i, user_prompt in enumerate(user_prompts):
            self.logger.info(f"Processing user prompt {i + 1}/{len(user_prompts)}")

            full_output = ""
            retry_count = 0
            max_retries = 3

            full_output_tokens = self.count_tokens(full_output)

            while full_output_tokens < plan.minimum_required_output_tokens and retry_count < max_retries:
                try:

                    response = self.gemini_get_response(plan, system_prompt, user_prompt, context, model)
                    if "The `response.text` quick accessor requires the response to contain a valid `Part`, but none were returned." in response:
                        for candidate in response.candidates:
                            for rating in candidate.safety_ratings:
                                print(f"Category: {rating.category}, Probability: {rating.probability}")
                                st.warning(f"Category: {rating.category}, Probability: {rating.probability}")
                    self.logger.info(f"Response received, length: {self.count_tokens(response.text)} tokens")
                    json_response = self.create_response_dict(response)
                    # st.json(json_response, expanded=False)
                    logging.warning(json_response["usage_metadata"])
                    full_output += response.text

                    full_output_tokens = self.count_tokens(full_output)

                    if full_output_tokens < plan.minimum_required_output_tokens:
                        self.logger.info(
                            f"Output length ({full_output_tokens})  tokens is less than desired length ({plan.minimum_required_output_tokens}). Retrying.")
                        retry_count += 1
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
                safety_feedback = {}
                if plan.require_json_output:
                    if response.candidates[0].finish_reason == "SAFETY":

                        for candidate in response.candidates:
                            for rating in candidate.safety_ratings:
                                safety_feedback.update({rating.category: rating.probability})

                    output_data = {
                        "text": response.text,
                        "prompt_feedback": safety_feedback,
                    }
                    json_output_path = f"{plan.thisdoc_dir}/{plan.output_file_path}_{str(uuid.uuid4())[:6]}.json"
                    with open(json_output_path, 'w') as json_file:
                        json.dump(output_data, json_file, indent=4)
                    self.logger.info(f"JSON output saved to {json_output_path}")
                    st.info(f"JSON output saved to {json_output_path}")
            else:
                self.logger.warning("No satisfactory results were generated.")
                satisfactory_results = ["No satisfactory results were generated."]
                st.warning("No satisfactory results were generated.")
            st.toast(f"processed prompt {i + 1}")
        return satisfactory_results

    def create_cache_from_context(self, context):
        if self.count_tokens(context) > 32768:
            # create a cache
            cache = caching.CachedContent.create(
                model='models/gemini-1.5-flash-001',
                display_name='text cache',  # used to identify the cache
                contents=[context],
                ttl=datetime.timedelta(minutes=60),
            )
        else:
            cache = None
        return cache

    import google.generativeai as genai

    def delete_current_cache(model_name='models/gemini-1.5-flash-001', display_name='text cache'):
        """Deletes the current cache based on model name and display name.

        Args:
            model_name (str): The name of the model associated with the cache.
            display_name (str): The display name of the cache.
        """
        genai.configure(api_key=GOOGLE_API_KEY)  # Make sure your API key is configured

        client = genai.client.get_default_cache_client()
        request = genai.protos.ListCachedContentsRequest(parent=model_name)
        response = client.list_cached_contents(request)

        for cached_content in response.cached_contents:
            if cached_content.display_name == display_name:
                delete_request = genai.protos.DeleteCachedContentRequest(name=cached_content.name)
                client.delete_cached_content(delete_request)
                logging.warning("Cache deleted successfully.")
                return

        logging.info(f"Cache with display name '{display_name}' not found for model '{model_name}'.")

    def process_plan_to_codex(self, plan: PromptGroups):
        """
        Handler for mode == "codex"
        Assumes normal plan object, only difference is mode
        Can have multiple prompts
        Custom user prompt should describe the output codex
        """
        self.logger.debug(f"Starting to create a codex using plan: {plan}")
        self.make_thisdoc_dir(plan)
        context = self.read_and_prepare_context(plan)
        self.logger.debug(f"Context prepared, length: {self.count_tokens(context)} tokens")

        model = self.create_model(self.model_name, self.safety_settings, plan.generation_config)
        self.logger.debug("Model created")

        system_prompt = self.assemble_system_prompt(plan)
        self.logger.debug(f"System prompt assembled, length: {self.count_tokens(system_prompt)}")

        user_prompts = plan.get_prompts()
        self.logger.info(f"\nUser prompts retrieved: {user_prompts}")
        # adding continuation prompt to user prompts
        # user_prompts.append(self.continuation_instruction)
        st.json([user_prompts])

        full_output = []
        repsmax = 5
        while 'IAMDONE' not in full_output:

            for i, user_prompt in enumerate(user_prompts):
                self.logger.info(f"Processing user prompt {i + 1}/{len(user_prompts)}")
                retry_count = 0
                max_retries = 3
                st.json([context[:250]])
                st.write(f"User prompt just prior to submission is: {user_prompt[0:250]}")
                response = self.gemini_get_response(plan, system_prompt, user_prompt, context, model)

                self.logger.debug(f"Response received, length: {self.count_tokens(response.text)} tokens")
                json_response = self.create_response_dict(response)
                #   st.json(json_response, expanded=False)
                full_output += response.text
                full_output_tokens = self.count_tokens(full_output)
                context += response.text

            st.info(f"processed prompt {i + 1}")
            if 'IAMDONE' in full_output:
                break
        st.info("found IAMDONE")
        st.write(full_output)

        return full_output

    def process_plan_to_codex_chunked(self, plan: PromptGroups):
        """
        Handler for mode == "codex"
        Assumes normal plan object, only difference is mode
        Can have multiple prompts
        Custom user prompt should describe the output codex
        """
        self.logger.debug(f"Starting to create a codex using plan: {plan}")
        self.make_thisdoc_dir(plan)
        context = self.read_and_prepare_context(plan)
        self.logger.debug(f"Context prepared, length: {self.count_tokens(context)} tokens")

        model = self.create_model(self.model_name, self.safety_settings, plan.generation_config)
        self.logger.debug("Model created")

        system_prompt = self.assemble_system_prompt(plan)
        self.logger.debug(f"System prompt assembled, length: {self.count_tokens(system_prompt)}")

        user_prompts = plan.get_prompts()
        self.logger.info(f"\nUser prompts retrieved: {user_prompts}")
        # adding continuation prompt to user prompts
        user_prompts.append(self.continuation_instruction)

        full_output = []
        max_chunk_size = plan.maximum_output_tokens // 2  # Aim for half the max output per chunk
        current_chunk = ""

        while 'IAMDONE' not in current_chunk:
            for i, user_prompt in enumerate(user_prompts):
                self.logger.info(f"Processing user prompt {i + 1}/{len(user_prompts)}")
                retry_count = 0
                max_retries = 3

                while retry_count < max_retries:
                    try:
                        response = self.gemini_get_response(plan, system_prompt, user_prompt, context, model)
                        self.logger.debug(f"Response received, length: {self.count_tokens(response.text)} tokens")

                        # Append response to current chunk
                        current_chunk += response.text

                        # Check if chunk size limit is reached
                        if self.count_tokens(current_chunk) >= max_chunk_size:
                            full_output.append(current_chunk)
                            current_chunk = ""  # Reset current chunk
                            context = ""  # Reset context for new chunk

                        break  # Exit retry loop if successful
                    except Exception as e:
                        self.logger.error(f"Error in gemini_get_response: {e}")
                        retry_count += 1
                        self.logger.info(f"Retrying due to error. Retry count: {retry_count}")

                if 'IAMDONE' in current_chunk:
                    break  # Exit outer loop if IAMDONE is found

            # Append any remaining text in current_chunk
            if current_chunk:
                full_output.append(current_chunk)

        return full_output

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
        system_prompt = ""
        if plan.complete_system_instruction:
            system_prompt = plan.complete_system_instruction
        else:
            with open(self.system_instructions_dict_file_path, "r") as json_file:
                system_instruction_dict = json.load(json_file)

            for key in plan.selected_system_instruction_keys:
                key = key.strip()
                try:
                    system_prompt += system_instruction_dict[key]['prompt']
                except KeyError as e:
                    self.logger.error(f"System instruction key {key} not found: {e}")
            if self.add_system_prompt:
                system_prompt += self.add_system_prompt

        return system_prompt

    def generate_full_book(self, plans: List[PromptGroups]):
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
                # st.write(response.usage_metadata)
                logging.warning(response.usage_metadata)
                return response
            except Exception as e:
                errormsg = traceback.format_exc()
                self.logger.error(f"Error generating content on attempt {attempt_no + 1}: {errormsg}")
                if attempt_no < MODEL_GENERATION_ATTEMPTS - 1:
                    sleep(RETRY_DELAY_SECONDS)
                else:
                    print("Max retries exceeded. Breaking and moving on to next book.")
                    break
        # delete the cache
        self.delete_current_cache(model_name=plan.model_name, display_name='text cache')

        return response

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
    parser.add_argument('--generation_config', type=str,
                        default='{"temperature": 1, "top_p": 0.95, "top_k": 0, "max_output_tokens": 8192}',
                        help="Generation config as a JSON string")
    parser.add_argument('--system_instructions_dict_file_path', default="resources/prompts/system_instructions.json",
                        help="Path to system instructions dictionary file")
    parser.add_argument('--list_of_system_keys',
                        default="nimble_books_editor,nimble_books_safety_scope,accurate_researcher,energetic_behavior,batch_intro",
                        help="Comma-separated list of system keys")
    parser.add_argument('--user_prompt', default='', help="User prompt")
    parser.add_argument('--user_prompt_override', action='store_true', help="Override user prompts from dictionary")
    parser.add_argument('--user_prompts_dict_file_path',
                        default=resources.files('Codexes2Gemini.resources.prompts').joinpath("user_prompts_dict.json"),
                        help="Path to user prompts dictionary file")
    parser.add_argument('--list_of_user_keys_to_use', default="semantic_analysis,core_audience_attributes",
                        help="Comma-separated list of user keys to use")
    parser.add_argument('--continuation_prompts', action='store_true', help="Use continuation prompts")
    parser.add_argument('--context_file_paths', nargs='+', help="Paths to context files")
    parser.add_argument('--output_file_base_name', default="results.md", help="Path to output file")
    parser.add_argument('--thisdoc_dir', default="output/c2g/", help="Document directory")
    parser.add_argument('--log_level', default="INFO", help="Logging level")
    parser.add_argument('--number_to_run', type=int, default=3, help="Number of runs")
    parser.add_argument('--minimum_required_output_tokens', "-do", type=int, default=1000,
                        help="Desired output length in characters")
    return parser.parse_args()


class Codex2Codex(Codexes2Parts):
    """
    Class for processing Codex to create another Codex.

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

    def process_codex_to_codex(self, plan: PromptGroups):
        return


if __name__ == "__main__":
    args = parse_arguments()

    c2b = Codexes2Parts()

    plan = PromptGroups(
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
