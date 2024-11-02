import argparse
import json
from typing import List
import streamlit as st

from Codexes2Gemini.classes.Codexes.Builders.PromptsPlan import PromptsPlan

from Codexes2Gemini.classes.Codexes.Builders import Codexes2Parts, PromptGroups
from Codexes2Gemini.classes.Codexes.Builders.Codexes2PartsOfTheBook import parse_arguments

from Codexes2Gemini.classes.Utilities.classes_utilities import configure_logger

configure_logger("DEBUG")

class Codex2Plan2Codex(Codexes2Parts):

    def __init__(self):
        super().__init__()

    def run_plan(self, plan: PromptsPlan) -> List[str]:
        # Initialize Codexes2PartsOfTheBook
        codex_processor = Codexes2Parts()

        # Process the plan and get results
        results = codex_processor.process_codex_to_book_part(plan)

        return results

    def create_condenserPlan(self, filepath, context):
        condenserPlan = PromptsPlan(
            name="condenserPlan",
            textfilename=filepath,
            require_json_output=True,
            context=context,
            selected_user_prompts_dict={
                "condenser_intructions":
                    """Backstory:
            
            Collapsar Classics was launched to bring 19th and early 20th century books to modern audiences in a fresh and convenient way. Each book is presented in a phone-sized 4 x 6" paperback format. Each Collapsar Classic includes a section called "Condensed Matter" (a play on front matter). Much like the Reader's Digest Condensed Books that were popular many decades ago, the Condensed Matters is meant to give you the best parts of the original in a much smaller space.
            
            Your Task:
            
            Your goal is to write a highly readable condensed matter version of this document that is 30% of the length of the full original found in the context cache.  You will accomplish this by providing system instructions and prompts in JSON formats that the system will then "spawn" to create the components of the condensed version.
            
            Silently create Analytic Table of Contents and use it to create a series of prompts that will accomplish this task.  The series of prompts must cover the entire text in semantically reasonable chunks (e.g. scenes, chapters, or parts).
            
            You must use the following JSON schema:
             
             {
             "name": str,
             "plan_type": str,
             "selected_user_prompts_dict": {
             "user_prompt_name": str,
             "user_prompt_text": str,
             "user_prompt_additional_context": str,
             "requested_word_count": int}
             "complete_system_instructions": str,
            }
           
            Your complete_system_instructions MUST:

            - direct the system to use the exact words of the context wherever possible.
            - allow transitional devices such as ellipses, dingbats, or bracketed comments.
            - mallow the system to use  sparing use of framing devices.
            - remind the system to use the current context, which is the full text of the original document and remains available in cache
            
           The system will read this data and loop through selected_user_prompts_dict one prompt at a time to assemble the results.
            
            Remember, your overriding goal is to give modern readers the benefit of reading this document in as original a form as possible, with as much meaning as possible, but in a substantially compressed timeframe."""},
            complete_system_instruction="You are industrious, energetic, and proactive. You complete tasks without waiting for approval.  You focus on the requested work product without adding conversational chit-chat.",
            minimum_required_output_tokens=300,
        )
        return condenserPlan

    def run_condenser_prompts(self, condenser_prompts):
        # extract Plan vaues from condenser_prompts
        print(type(condenser_prompts))
        condenser_prompts_string = condenser_prompts[0]
        condenser_prompts_string = condenser_prompts_string.replace("```json", "").replace("```", "")
        condenser_prompts_dict = json.loads(condenser_prompts_string)
        complete_system_instruction = condenser_prompts_dict["complete_system_instructions"]
        selected_user_prompts_dict = condenser_prompts_dict["selected_user_prompts_dict"]
        name = condenser_prompts_dict["name"]
        c2c = Codex2Plan2Codex()
        condenser_results = []
        idx = 0
        original_context = st.session_state.current_plan["context"]
        self.logger.info(f"original_context: {len(original_context)}")

        for this_prompt in condenser_prompts:
            self.logger.info(f"running prompt index {idx} of {len(condenser_prompts)}")
            this_plan = PromptsPlan(name=f"condenserPlan_{idx}", selected_user_prompts_dict=selected_user_prompts_dict,
                                    complete_system_instruction=complete_system_instruction, context=original_context)
            self.logger.info(f"Processing plan: {this_plan}")
            c2p = Codexes2Parts()
            this_result = c2p.process_codex_to_book_part(this_plan)
            idx += 1
            self.logger.info(f"this_result: {this_result}")
            condenser_results.append(this_result)
        self.logger.info(type(condenser_results))
        self.logger.info(len(condenser_results))
        return condenser_results


def main():
    pass

if __name__ == "__main__":
    c2c = Codex2Plan2Codex()
    c2c.main()
    condenserPlan = c2c.create_condenserPlan()
    c2c.run_plan(condenserPlan)
