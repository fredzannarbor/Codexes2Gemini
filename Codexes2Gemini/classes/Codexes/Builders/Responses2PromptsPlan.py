import json
import logging
import traceback

from Codexes2Gemini.classes.Codexes.Builders.PromptsPlan import PromptsPlan


class Response2Prompts:
    def __init__(self, json_response, logger=logging.getLogger(__name__)):
        self.json_response = json_response
        self.logger = logger or logging.getLogger(__name__)
        # Initialize your Codexes2Parts instance

    def process_response(self):
        """
        Processes the JSON response, creates a PromptPlan, and runs it.
        """
        try:
            # Import Codexes2Parts here, when it's actually needed
            from Codexes2Gemini.classes.Codexes.Builders.Codexes2PartsOfTheBook import Codexes2Parts
            self.c2p = Codexes2Parts()  # Initialize your Codexes2Parts instance

            # 1. Parse the JSON response
            prompts_data = self._parse_json_response()

            # 2. Create a PromptPlan
            plan = self._create_prompt_plan(prompts_data)

            # 3. Run the PromptPlan
            results = self.c2p.process_codex_to_book_part(plan)
            return results

        except Exception as e:
            self.logger.error(f"Error processing response: {e}")
            self.logger.error(traceback.format_exc())
            return

    def _parse_json_response(self):
        """
        Parses the JSON response and extracts the prompts data.

        Returns:
            dict: A dictionary containing the parsed prompts data.
        """
        try:

            # Assuming your JSON response has a key like 'prompts'
            prompts_data = self.json_response
            return prompts_data
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON response: {e}")
            raise  # Re-raise the exception to be handled at a higher level

    def _create_prompt_plan(self, prompts_data):
        """
        Creates a PromptPlan instance from the parsed prompts data.

        Args:
            prompts_data (dict): The parsed prompts data.

        Returns:
            PromptsPlan: A PromptPlan instance.
        """
        # Extract necessary data from prompts_data
        print(prompts_data)
        name = prompts_data.get('name', 'Response2PromptsPlan')
        plan_type = prompts_data.get('plan_type', 'Spawned')
        additional_context = prompts_data.get('additional_context', '')
        selected_user_prompts_dict = prompts_data.get('selected_user_prompts_dict', {})
        complete_system_instructions = prompts_data.get('complete_system_instructions', '')

        # Create and return a PromptPlan instance
        plan = PromptsPlan(
            name=name,
            context=additional_context,
            selected_user_prompts_dict=selected_user_prompts_dict,
            complete_system_instruction=complete_system_instructions,
            selected_user_prompt_keys=selected_user_prompts_dict.keys()
            # ... (Pass other necessary parameters to PromptsPlan)
        )

        # Update the plan with other parameters
        for key, value in other_parameters.items():
            if hasattr(plan, key):
                setattr(plan, key, value)

        return plan
