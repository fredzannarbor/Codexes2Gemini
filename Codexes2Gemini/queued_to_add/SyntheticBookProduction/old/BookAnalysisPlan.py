import logging
import os
import traceback
from typing import List

import openai
from google.generativeai import GenerativeModel
from openai import OpenAI
from classes.Codexes.Builders.PromptPlan import PromptPlan

class BookAnalysisPlan:
    """

    This class represents a book analysis plan.

    Attributes:
    - context (str): The context of the book analysis.
    - prompt_plans (List[PromptPlan]): List of prompt plans for the analysis.
    - cache: Cache for storing intermediate results.
    - logger: Logger for logging messages.
    - thisdoc_dir (str): Directory for storing outputs.
    - list_of_user_keys_to_use (List[str]): List of user keys to be used.

    Methods:
    - __init__(self, context: str, user_keys_list: List[str] = None): Initializes a new instance of the class.
    - set_attribute(self, attribute_name: str, value): Sets an attribute of the class.
    - add_prompt_plan(self, user_keys: List[str]) -> None: Adds a prompt plan to the analysis.
    - update_user_keys(self, new_user_keys: List[str]): Updates the list of user keys.
    - execute_plans(self, t2g, metadatas): Executes the analysis plans.
    - configure_logger(): Configures the logger for logging messages.

    """
    def __init__(self, context: str, user_keys_list: List[str] = None):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.context = context
        self.prompt_plans: List[PromptPlan] = []
        self.cache = None
        self.logger = self.configure_logger()
        self.thisdoc_dir = "output/gemini/"  # default
        self.list_of_user_keys_to_use = user_keys_list if user_keys_list else ["core_audience_attributes"]
        self.system_instructions_dict_file_path = "resources/json/gemini_prompts/gemini_system_instructions.json"
        self.list_of_system_keys = "nimble_books_editor, nimble_books_safety_scope, accurate_researcher, energetic_behavior, batch_intro"

    def set_attribute(self, attribute_name: str, value):
        setattr(self, attribute_name, value)
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

    def add_prompt_plan(self, user_keys: List[str], provider: str = "gemini",
                        model: str = "gemini-1.5-flash-001") -> None:
        try:
            prompt_plan = PromptPlan(context=self.context, user_keys=user_keys, thisdoc_dir=self.thisdoc_dir)
            prompt_plan.set_provider(provider, model)
            self.prompt_plans.append(prompt_plan)
        except Exception as e:
            self.logger.error(f"Error adding prompt plan: {e}")

    def execute_plans(self, t2g, metadatas):
        results = {}
        for prompt_plan in self.prompt_plans:
            print(prompt_plan.to_dict())
            try:
                if prompt_plan.provider == "gemini":
                    result = self._execute_gemini_plan(prompt_plan, t2g)
                elif prompt_plan.provider == "openai":
                    result = self._execute_openai_plan(prompt_plan, t2g)
                else:
                    raise ValueError(f"Unsupported provider: {prompt_plan.provider}")
                print(result)
                for key in prompt_plan.user_keys.split(','):
                    results[key] = result
                    metadatas[key] = results[key]
                    self.logger.info(f"Set metadata attribute {key}: {result[:100]}...")
            except Exception as e:
                self.logger.error(f"Error processing prompt plan: {traceback.format_exc()}")
        return results, metadatas

    def _execute_gemini_plan(self, prompt_plan: PromptPlan, t2g) -> str:
        if self.cache is None:
            system_instruction = "You are an AI assistant analyzing a book."
            model = GenerativeModel(prompt_plan.model)
            context_tokens = model.count_tokens(self.context).total_tokens
            if context_tokens >= 32768:
                self.cache = t2g.create_cache(self.context, prompt_plan.model, system_instruction)
            else:
                raise ValueError(f"The context provided is too small: {context_tokens}")
        return t2g.submit_to_gemini(prompt_plan, self.cache)

    def _execute_openai_plan(self, prompt_plan: PromptPlan, t2g) -> str:
        if not self.openai_api_key:
            raise ValueError("OpenAI API key not set. Use set_openai_api_key() method to set it.")
        client = OpenAI()
        openai.api_key = os.getenv("OPENAI_API_KEY")

        system_message = "You are the Dark Baron, an anonymous young conservative writer, influencer, and pundit.  You are very tall, love DUNE books and movies, and are highly up to date on youth language, culture, memes, and media. You are writing a book explaining to young people ages 18-29 how Project 2025 will benefit them under a second Trump administration.  The context is the text of Project 2025. Refer to it to ensure that all your claims are accurate and truthful. Follow the user prompt and write the full text of the described chapter.  Each chapter should be at least eight full paragraphs long. Do not include any conversation with the user. Proceed without pausing to complete the full text."
        user_prompts = t2g.get_user_prompts(prompt_plan)
        print(f"user prompts are {user_prompts}")
        exit()
        results = []
        for u in user_prompts:
            print(u)
            user_message = f"{self.context}\n\n{u}"
            print(user_message)

            prompt_plan.generation_config["max_output_tokens"] = 3800
            response = client.chat.completions.create(
                model=prompt_plan.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=prompt_plan.generation_config.get("temperature", 0.85),
                max_tokens=prompt_plan.generation_config.get("max_output_tokens", 3800),
                top_p=prompt_plan.generation_config.get("top_p", 1.0),
            )
            results = results.append(response.choices[0].message.content)
        return results

    def to_dict(self):
        return (self.__dict__)

    @staticmethod
    def configure_logger():
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger