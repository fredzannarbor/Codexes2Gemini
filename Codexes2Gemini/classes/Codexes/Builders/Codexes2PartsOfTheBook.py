import argparse
import datetime
import json
import logging
import os
import traceback
from importlib import resources
from time import sleep
from typing import List

import google.generativeai as genai
import pandas as pd
import streamlit as st
from google.generativeai import caching

from Codexes2Gemini.classes.Utilities.classes_utilities import configure_logger
from Codexes2Gemini.classes.Codexes.Builders.PromptsPlan import PromptsPlan
from Codexes2Gemini.ui.ui_utilities import load_json_file
from Codexes2Gemini.classes.Codexes.Builders.Responses2PromptsPlan import Response2Prompts

from ..Builders.PromptsPlan import PromptsPlan

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

    def process_codex_to_book_part(self, plan):
        st.info(
            f"Starting process_codex_to_book_part with plan: {plan} for {plan.textfilename} with prompts provided by {plan.plan_type}.")


        self.make_thisdoc_dir(plan)
        context = self.read_and_prepare_context(plan)
        self.logger.debug(f"Context prepared, length: {self.count_tokens(context)} tokens")


        cache = self.create_cache_from_context(context)

        model = self.create_model(self.model_name, self.safety_settings, plan.generation_config, cache)
        self.logger.debug("Model created")
        if plan.plan_type == "User":
            logging.info("Plan type is User")
            system_prompt = self.assemble_system_prompt(plan)
            self.logger.debug(f"System prompt assembled, length: {self.count_tokens(system_prompt)}")

            user_prompts = plan.get_prompts()

            if not isinstance(user_prompts, list):
                self.logger.error(f"Unexpected data type for prompts: {type(user_prompts)}")
                return self.results  # Return early to avoid errors
                self.logger.error(f"Unexpected data type for prompts: {type(user_prompts)}")
                return self.results  # Return early to avoid errors
        elif st.session_state.current_plan["plan_type"] == "Catalog":
            system_prompt, user_prompts = self.assemble_catalog_prompts(plan)

        elif st.session_state.current_plan["plan_type"] == "Spawned":
            system_prompt = self.assemble_system_prompt(plan)
            user_prompts = plan.get_prompts()
            context = st.session.state.current_plan["original_context"] + plan.additional_context
            self.logger.warning = f"length of spawned context is {len(context)}"


        elif plan.plan_type == "Chunking":  # New case for chunking prompts
            self.results = self.process_chunking_prompts(plan, context, model)

        self.results = []  # Reset self.results for each new book

        for user_prompt in user_prompts:

            self.logger.info(f"\nProcessing user prompt: {user_prompt}")

            full_output = ""
            retry_count = 0
            max_retries = 3
            response_to_measure = " "

            while self.count_tokens(
                    response_to_measure) < plan.minimum_required_output_tokens and retry_count < max_retries:

                # get a sufficiently long response to the current user prompt

                try:
                    response = self.gemini_get_response(plan, system_prompt, user_prompt, context, model)
                    response_to_measure = response.text
                    self.logger.info(f"\nResponse received, length: {self.count_tokens(response.text)} tokens")
                    self.logger.info(f"Retry count: {retry_count}")
                    if self.count_tokens(response.text) < plan.minimum_required_output_tokens:
                        self.logger.info(
                            f"Output length is less than desired length. Retrying.")
                        retry_count += 1
                    else:
                        self.logger.info(f"Output length is satisfactory.")
                except Exception as e:
                    self.logger.error(f"Error in gemini_get_response: {e}")
                    retry_count += 1
                    self.logger.info(f"Retrying due to error. Retry count: {retry_count}")

                self.logger.info(f"\nFinal output length for this response: {self.count_tokens(response.text)}")

                # now decide whether we should spawn new Plan from this final response

                if self.count_tokens(response.text) >= plan.minimum_required_output_tokens:
                    self.results.append(response.text)


        return self.results

    def check_if_response_contains_prompts(self, response):
        try:
            if "selected_user_prompts_dict" in response.text:
                logging.warning("prompts found in check_if_response_contains_prompts")
                return True
            else:
                print("prompts not found")
                logging.warning("prompts not found")
                return False
        except Exception as e:
            logging.error("response is not json serializable")
            return False

    def get_response_containing_prompts(self, response):
        try:
            # print(response)
            json_string = response.text
            print(json_string)
            json_string = json_string.replace("```json", "").replace("```", "")
        except Exception as e:
            print(traceback.format_exc())
            return Exception(f"response is not json serializable: {e}")

        try:
            prompt_payload = json.loads(json_string)
            print(prompt_payload)
            return prompt_payload
        except Exception as e:
            print(traceback.format_exc())
            return Exception(f"response is not json serializable: {e}")

    def process_single_context(self, context, row, plan=None):
        """Processes a single context and returns the results.

        Args:
            context (str): The text content of the context.
            row (list): The metadata row corresponding to the context.
            plan (PromptsPlan, optional): The PromptsPlan object to use.
                                          If None, it will use the current plan
                                          from the session state.

        Returns:
            list: A list of results from processing the context.
        """
        # Update the current plan in the session state with context and row
        st.session_state.current_plan.update({"context": context, "row": row})

        # Use the provided plan or create one from the session state
        if plan is None:
            plan = PromptsPlan(**st.session_state.current_plan)

        # Call process_codex_to_book_part from Codexes2Parts
        satisfactory_results = self.CODEXES2PARTS.process_codex_to_book_part(plan)
        return satisfactory_results

    def process_chunking_prompts(self, plan, context, model):
        total_tokens = self.count_tokens(context)
        desired_output_length = int(total_tokens * (plan.chunking_output_percentage / 100))
        max_tokens_per_chunk = plan.chunking_max_tokens_per_chunk
        num_chunks = -(-desired_output_length // max_tokens_per_chunk)  # Ceiling division
        chunks = self.split_into_semantic_chunks(context, num_chunks)
        all_chunk_results = []
        for i, chunk in enumerate(chunks):
            chunk_context = f"Here is chunk {i + 1} of the document. Context: {context}\n\nChunk: {chunk}"
            for prompt_key in plan.chunking_prompts:
                prompt = plan.selected_user_prompts_dict[prompt_key]
                plan.selected_user_prompts_dict = {prompt_key: prompt}  # Update the plan with the current prompt
                chunk_results = self.run_prompt_on_chunk(plan, chunk_context, model)
                all_chunk_results.extend(chunk_results)
        return all_chunk_results

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

    def process_plan_to_codex(self, plan: PromptsPlan):
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

    def process_plan_to_codex_chunked(self, plan: PromptsPlan):
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
        # st.write(context_content)

        if isinstance(context_content, list):
            # Convert list to strings

            context_content = "\n\n".join(context_content)

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
        self.logger.info(context_msg)
        st.toast(context_msg)
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

    def assemble_catalog_prompts(self, plan):
        system_prompt = ""
        catalog_user_prompts = []

        if plan.complete_system_instruction:
            system_prompt = plan.complete_system_instruction
        else:
            with open(self.system_instructions_dict_file_path, "r") as json_file:
                try:
                    system_instructions_dict = json.load(json_file)
                except Exception as e:
                    self.logger.error(f"Error loading system instructions: {e}")
                    st.error(traceback.format_exc())
                    return system_prompt, catalog_user_prompts

                for key in plan.selected_system_instruction_keys:
                    key = key.strip()
                    try:
                        system_prompt += system_instructions_dict[key]['prompt']
                    except KeyError as e:
                        self.logger.error(f"System instruction key {key} not found: {e}")
                if self.add_system_prompt:
                    system_prompt += self.add_system_prompt

        self.user_prompts_dict = load_json_file("standard_user_prompts.json")

        self.selected_catalog_prompt_keys = st.session_state.current_plan["selected_catalog_prompt_keys"]
        if self.user_prompts_dict:
            st.info("found user prompts dict")
            for k in self.selected_catalog_prompt_keys:  # Iterate through catalog prompt keys
                if k in self.user_prompts_dict:  # Check if the key exists in the user prompts dict
                    v = self.user_prompts_dict[k]
                    catalog_user_prompts.append(f"{k}: {v}")
        else:
            logging.error("No user prompts dict found")

        return system_prompt, catalog_user_prompts

    def generate_full_book(self, plans: List[PromptsPlan]):
        return [self.process_codex_to_book_part(plan) for plan in plans]

    def gemini_get_response(self, plan, system_prompt, user_prompt, context, model):
        self.configure_api()
        MODEL_GENERATION_ATTEMPTS = 15
        RETRY_DELAY_SECONDS = 10

        prompt = [system_prompt, user_prompt, context]

        prompt_stats = f"system prompt: {len(system_prompt)} char, user_prompt: {len(user_prompt)}. context: {len(context)}"
        self.logger.info(f"{prompt_stats}")
        prompt_df = pd.DataFrame(prompt)
        prompt_df.to_json(plan.thisdoc_dir + "/prompt.json", orient="records")

        for attempt_no in range(MODEL_GENERATION_ATTEMPTS):
            try:
                response = model.generate_content(prompt, request_options={"timeout": 600})
                # st.write(response.usage_metadata)
                self.logger.debug(response)
                # st.json(response, expanded=2)

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


if __name__ == "__main__":
    print(f"Generated book part.")
