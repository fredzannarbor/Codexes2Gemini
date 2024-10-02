import argparse
import datetime
import json
import logging
import os
import sys
import traceback
from pprint import pprint
from time import sleep

import google.generativeai as genai
import pandas as pd

from classes.Codexes.Builders.PromptPlan import PromptPlan

YOUR_API_KEY = os.environ['GOOGLE_API_KEY']


class Text2Gemini:
    """

    Class Text2Gemini

    Represents a text-to-gemini processor.

    Attributes:
        - user_prompt: str, the prompt to be given to the user
        - model: str, the name of the generative model to be used
        - logger: logging.Logger, the logger object used for logging
        - model_name: str, the name of the generative model
        - generation_config: dict, the configuration settings for generation
        - safety_settings: list, the safety settings for generating content
        - system_instruction: str, the system instruction for the gemini model
        - system_instructions_dict_file_path: str, the path to the system instruction dictionary file
        - continuation_instruction: str, the instruction for continuation of the task

    Methods:
        - __init__(): constructor method
        - configure_api(): configures the API key
        - create_model(model_name, safety_settings, generation_config, system_instruction): creates a generative model
        - create_cache(context, model_name, system_instruction, minutes): creates a cache for context
        - process_text(thisdoc_dir, model_name, safety_settings, generation_config, text, system_instruction, user_prompt): processes the given text using the generative model
        - configure_generation(args): configures the generation settings
        - assemble_system_prompt(args): assembles the system prompt based on the given arguments
        - filter_user_prompts(plan): filters the user prompts based on the given plan
        - get_user_prompt(plan, i): gets the user prompt at the given index i
        - gemini_get_response(args, system_prompt, user_prompt, context, model): gets the response from the generative model
        - process_semantic_analysis(response): processes the semantic analysis of the response
        - extract_values(json_data, task_name): extracts the values from the given JSON data based on the task name
        - parse_prompt_files(plan, context, model): parses the prompt files based on the given plan, context, and model

    """

    def __init__(self):
        super().__init__()
        self.user_prompt = "Summarize this document."
        self.model = None
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
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            },
        ]
        self.system_instruction = "You are an editor working for Nimble Books LLC.  You are thoroughly familiar with every aspect of book publishing and with every market and genre. You have outstanding skills at reading comprehension and are excellent at writing accurate, detailed, imaginative prose.  You are completely familiar with the 17th edition of the Chicago Manual of Style. In your communications with the user, you are professional. In your work product, you are accurate, meticulous, and consistent, but you also show wit and flair. \n\nNimble Books publishes books about military history, politics, and space, so it is ok for you to write about violence and politics.\n\n You are industrious, energetic, and proactive. You complete tasks without waiting for approval.\n\nAll responses should be plain text. Separate paragraphs by two returns.  Do not use bolding. Do not use underlining. Do not use header levels.\n\n- "  # default if dictionary file is not provided
        self.system_instructions_dict_file_path = "resources/prompts/system_instructions.json"
        self.continuation_instruction = "The context now includes a section called {Work So Far} which includes your work on this book project so far. Please refer to it along with the context document as you carry out the following task."

    def configure_api(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise EnvironmentError("GOOGLE_API_KEY environment variable is not set.")
        genai.configure(api_key=api_key)

    def create_model(self, model_name, safety_settings, generation_config, system_instruction):
        model = genai.GenerativeModel(model_name, safety_settings, generation_config, system_instruction)
        return model

    def create_cache(self, context, model_name, system_instruction, minutes=60):
        cache = genai.caching.CachedContent.create(
            model=model_name,
            display_name="book_analysis_cache",
            system_instruction=system_instruction,
            contents=[context],
            ttl=datetime.timedelta(minutes=minutes),
        )
        return cache

    def process_text(self, thisdoc_dir, model_name, safety_settings, generation_config, text, system_instruction,
                     user_prompt):
        self.configure_api()
        try:
            model = genai.GenerativeModel(model_name, safety_settings, generation_config)
        except Exception as e:
            logging.error(f"error creating model {e}")
            print(f"error creating model {e}")
        prompt = [system_instruction, user_prompt, text]

        try:
            response = model.generate_content(prompt)
        except Exception as e:
            errormsg = traceback.print_exc()
            logging.error(f"error generating content: {errormsg}")
            print(f"Gemini error message: {errormsg}")
            print("exiting")
            exit()

        logging.debug(response)

        return response

    def configure_generation(self, args):
        if not args.json_required:
            args.generation_config = {
                "temperature": 1,
                "top_p": 0.95,
                "top_k": 0,
                "max_output_tokens": 8192
            }
        else:
            return args.generation_config  # which includes json required mimetype

    def assemble_system_prompt(self, args):
        system_prompt = ''
        with open(self.system_instructions_dict_file_path, "r") as json_file:
            system_instruction_dict = json.load(json_file)
        list_of_system_keys = [item.strip() for item in args.list_of_system_keys.split(',')]
        for key in list_of_system_keys:
            try:
                system_prompt += system_instruction_dict[key]
            except KeyError as e:
                logging.error(f"system instruction key {key} not found: {e} ")
                break
        return system_prompt

    def filter_user_prompts(self, plan: PromptPlan):
        list_of_user_keys = [key.strip() for key in plan.list_of_user_keys_to_use.split(',')]
        pprint(list_of_user_keys)
        filtered_dict = {key: plan.user_prompts_dict[key] for key in list_of_user_keys
                         if key in plan.user_prompts_dict.keys()}
        list_of_user_prompts = list(filtered_dict.values())
        return list_of_user_prompts

    def get_user_prompt(self, plan: PromptPlan, i):
        list_of_user_keys = [key.strip() for key in plan.list_of_user_keys_to_use.split(',')]
        logging.debug(f"list of user keys: {list_of_user_keys}")
        filtered_dict = {key: plan.user_prompts_dict[key] for key in list_of_user_keys
                         if key in plan.user_prompts_dict.keys()}
        list_of_user_prompts = list(filtered_dict.values())
        try:
            user_prompt = list_of_user_prompts[i]
            logging.debug(f"user prompt {i}: {user_prompt}")
        except IndexError as e:
            logging.error(f"user prompt index {i} not found: {e}")
            user_prompt = ""
        return user_prompt

    def get_user_prompts(self, plan: PromptPlan):
        list_of_user_keys = [key.strip() for key in plan.list_of_user_keys_to_use.split(',')]
        logging.debug(f"list of user keys: {list_of_user_keys}")
        print(f"list of user keys: {list_of_user_keys}")
        filtered_dict = {key: plan.user_prompts_dict[key] for key in list_of_user_keys
                         if key in plan.user_prompts_dict.keys()}
        list_of_user_prompts = list(filtered_dict.values())
        return list_of_user_prompts

    def gemini_get_response(self, args, system_prompt, user_prompt, context, model):
        self.configure_api()
        MODEL_GENERATION_ATTEMPTS = 15
        RETRY_DELAY_SECONDS = 10

        prompt = [system_prompt, user_prompt, context]

        prompt_stats = f"system prompt: {len(system_prompt)} {system_prompt[:35]}\nuser_prompt: {len(user_prompt)} {user_prompt[:35]}\ncontext: {len(context)} {context[11:35]}"
        print(f"{prompt_stats}")
        prompt_df = pd.DataFrame(prompt)
        prompt_df.to_json(args.thisdoc_dir + "/prompt.json", orient="records")

        for attempt_no in range(MODEL_GENERATION_ATTEMPTS):
            try:
                response = model.generate_content(prompt, request_options={"timeout": 600})
                return response
            except Exception as e:
                errormsg = traceback.format_exc()
                self.logger.error(f"Error generating content on attempt {attempt_no + 1}: {errormsg}")
                if attempt_no < MODEL_GENERATION_ATTEMPTS - 1:  # don't delay on last attempt
                    sleep(RETRY_DELAY_SECONDS)
                else:
                    print("Max retries exceeded. Exiting.")
                    exit()

        self.logger.debug(response)
        return response

    def parse_prompt_files(self, plan: PromptPlan, context, model):
        system_prompt = self.assemble_system_prompt(plan)
        logging.debug(f"system_prompt is\n {system_prompt}")

        plan.list_of_user_prompts = self.filter_user_prompts(plan)
        for i in range(len(plan.list_of_user_prompts)):
            logging.debug(f"running user prompt {i}/{len(plan.list_of_user_prompts)}")
            if i >= plan.number_to_run:
                logging.info("breaking i>n")
                break
            user_prompt = self.get_user_prompt(plan, i)
            if plan.user_prompt:
                user_prompt += '\n\n' + plan.user_prompt
            logging.debug(f"assembled user prompt with any optional additions is: \n{user_prompt}")

            try:
                response = self.gemini_get_response(plan, system_prompt, user_prompt, context, model)

                logging.debug(response)
            except Exception as e:
                logging.error(traceback.format_exc())
                continue

            if plan.continuation_prompts:
                if i == 0:
                    context += "\n\n{Work So Far}:\n\n"
                context += response.text

            with open(plan.output_file_path, 'a') as f:
                f.write(f"{response.text}\n\n")

        return context, response.text

    def submit_to_gemini(self, plan: PromptPlan, cache=None):
        self.make_thisdoc_dir(plan)
        varslog = str(vars(plan))
        print(f"length of context is {len(plan.context)}")
        logging.debug(varslog)

        if len(plan.context) > 0:
            context_content = plan.context
        else:
            try:
                with open(plan.context_file_path, "r", encoding='ISO-8859-1', errors='ignore') as f:
                    context_content = f.read()
            except Exception as e:
                traceback.print_exc()
                context_file_error = traceback.format_exc()
                logging.warning("No context file found.")
                logging.error(context_file_error)
                context_content = ""
        context_msg = f"context is type {type(context_content)}, length {len(context_content)}"
        logging.debug(context_msg)
        print(context_msg)
        context = f"\nContext: {context_content}\n\n"

        if cache:
            model = genai.GenerativeModel.from_cached_content(cached_content=cache)
        else:
            model = genai.GenerativeModel(self.model_name, self.safety_settings, plan.generation_config)

        system_prompt = self.assemble_system_prompt(plan)
        user_prompt = self.get_user_prompt(plan, 0)  # Assuming we want the first prompt

        response = self.gemini_get_response(plan, system_prompt, user_prompt, context, model)

        try:
            with open(plan.output_file_path, 'a') as f:
                f.write(f"{response.text}\n\n")
        except Exception as e:
            logging.error(f"trouble saving response to file {plan.output_file_path}")
            logging.error(traceback.format_exc())

        print(f"Results saved to: {plan.output_file_path}")
        return response.text

    # Modify other methods to use 'plan' instead of 'args'
    def make_thisdoc_dir(self, plan):
        if not os.path.exists(plan.thisdoc_dir):
            os.makedirs(plan.thisdoc_dir)
        print(f"thisdoc_dir is {plan.thisdoc_dir}")
        return


def parse_arguments():
    parser = argparse.ArgumentParser(description="Run Text2Gemini with provided arguments")
    parser.add_argument('--model', default="gemini-1.5-flash-001", help="Model to use")
    parser.add_argument('--json_required', action='store_true', help="Require JSON output")
    parser.add_argument('--generation_config', type=str,
                        default='{"temperature": 1, "top_p": 0.95, "top_k": 0, "max_output_tokens": 8192}',
                        help="Generation config as a JSON string")
    parser.add_argument('--system_prompts_file_path', default=None, help="Path to system prompts file")
    parser.add_argument('--system_instructions_dict_file_path',
                        default="resources/json/system_instructions.json",
                        help="Path to system instructions dictionary file")
    parser.add_argument('--list_of_system_keys',
                        default="nimble_books_editor, nimble_books_safety_scope, accurate_researcher, energetic_behavior, batch_intro",
                        help="Comma-separated list of system keys")
    parser.add_argument('--user_prompt', default='', help="User prompt")
    parser.add_argument('--user_prompts_dict_file_path', default="resources/prompts/user_prompts_dict.json",
                        help="Path to user prompts dictionary file")
    parser.add_argument('--list_of_user_keys_to_use', default="semantic_analysis, core_audience_attributes",
                        help="Comma-separated list of user keys to use")
    parser.add_argument('--continuation_prompts', action='store_true', help="Use continuation prompts")
    parser.add_argument('--task_package', help="Task package")
    parser.add_argument('--context_file_path', default="test/text/agfw.txt", help="Path to context file")
    parser.add_argument('--cache_this_context', action='store_true', help="Cache this context")
    parser.add_argument('--output_file_base_name', default="results.md", help="Path to output file")
    parser.add_argument('--thisdoc_dir', default="output/gemini/", help="Document directory")
    parser.add_argument('--log_level', default="INFO", help="Logging level")
    parser.add_argument('--number_to_run', type=int, default=3, help="Number of runs")
    return parser.parse_args()


if __name__ == "__main__":

    if len(sys.argv) > 1:
        args = parse_arguments()
        plan = PromptPlan(
            model=args.model,
            json_required=args.json_required,
            generation_config=json.loads(args.generation_config),
            system_prompts_file_path=args.system_prompts_file_path,
            system_instructions_dict_file_path=args.system_instructions_dict_file_path,
            list_of_system_keys=args.list_of_system_keys,
            user_prompt=args.user_prompt,
            user_prompts_dict_file_path=args.user_prompts_dict_file_path,
            list_of_user_keys_to_use=args.list_of_user_keys_to_use,
            continuation_prompts=args.continuation_prompts,
            task_package=args.task_package,
            context_file_path=args.context_file_path,
            cache_this_context=args.cache_this_context,
            output_file_path=args.output_file_path,
            thisdoc_dir=args.thisdoc_dir,
            log_level=args.log_level,
            number_to_run=args.number_to_run
        )
    else:
        plan = PromptPlan()

    t2g = Text2Gemini()
    t2g.submit_to_gemini(plan)
