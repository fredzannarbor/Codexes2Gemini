import json
import logging
from typing import Dict

import google.generativeai as genai
import streamlit as st

from Codexes2Gemini.ui.ui_utilities import create_latex_preamble, clean_up_markdown, flatten_and_stringify
from ..Builders.Codexes2PartsOfTheBook import Codexes2Parts
from ..Builders.PromptGroups import PromptGroups


class CodexBuilder:
    """
    Class to build codexes from parts and plans.

    Attributes:
    - c2p: Codexes2Parts instance
    - logger: Logger instance
    - model: GenerativeModel instance

    Methods:
    - build_codex_from_parts: Build a codex from multiple parts.
    - build_codex_from_plan: Build a codex using a single PromptGroups.
    - build_codex_from_multiple_plans: Build a codex using multiple PromptPlans.
    - count_tokens: Count the number of tokens in a text.
    - truncate_to_token_limit: Truncate content to match the token limit.
    - use_continuation_prompt: Use continuation prompts to extend content to desired token count.
    """
    def __init__(self):
        self.c2p = Codexes2Parts()
        self.logger = logging.getLogger(__name__)
        self.model = genai.GenerativeModel('gemini-pro')

    def build_parts_from_codex(self, plan: PromptGroups) -> str:
        """Build parts of the book using a single PromptGroups."""
        return self.c2p.process_codex_to_book_part(plan)


    def assemble_parts_of_a_codex_per_cmos18(self, tagged_parts: Dict[str, str]):
        """
        function that uses CMOS rules to put the parts of the book in their proper order

        1) is this an easily recognized part? -- Foreword, Glodssary, Index, etc?
        2) Use lookup table of order rules to put it in the right slot
        3) if it's not an easily recognized part of the book -- something new or unusual -- ask the model to make an additional call and resolve the issue
        """
        # logic to create sorted_parts
        """

        Args:
            tagged_parts (object): 
        """
        return

    def build_codex_from_plan(self, plan: PromptGroups) -> str:
        """Build a codex using a single PromptGroups."""
        return self.c2p.process_plan_to_codex(plan)

    # def build_codex_from_multiple_plans(self, plans: List[PromptGroups]) -> str:
    #     """Build a codex using multiple PromptPlans."""
    #     results = self.c2p.generate_full_book(plans)
    #     return self.build_codex_from_parts(results)


    def count_tokens(self, text: str) -> int:
        try:
            return self.model.count_tokens(text).total_tokens
        except Exception as e:
            self.logger.error(f"Error counting tokens: {e}")
            # Fallback to character count if tokenization fails
            return len(text)

    def truncate_to_token_limit(self, content: str, limit: int) -> str:
        while self.count_tokens(content) > limit:
            content = content[:int(len(content) * 0.9)]  # Reduce by 10% each time
        return content

    def use_continuation_prompt(self, plan: PromptGroups, initial_content: str) -> str:
        """Use continuation prompts to extend content to desired token count."""
        full_content = initial_content
        while self.count_tokens(full_content) < plan.minimum_required_output_tokens:
            plan.context += f"\n\n{{Work So Far}}:\n\n{full_content}"
            additional_content = self.build_part(plan)
            full_content += additional_content
        return self.truncate_to_token_limit(full_content, plan.minimum_required_output_tokens)


def results2assembled_pandoc_markdown_with_latex(results):
    assembled_documents = []

    for item in results:

        item = flatten_and_stringify(item)


        assembled_pandoc_markdown_with_latex = ""

        cleaned_item = item.strip(' "')

        try:
            # Attempt to parse as JSON
            json_data = json.loads(cleaned_item)

            # Handle basic info result (check for keys anywhere in the object)
            if any(key in json_data for key in ["gemini_title", "gemini_authors"]):
                gemini_title = json_data.get("gemini_title", "TBD")
                gemini_subtitle = json_data.get("gemini_subtitle", "TBD")
                gemini_authors = json_data.get("gemini_authors", "TBD")
                gemini_summary = json_data.get("gemini_summary", "TBD")
                st.session_state.current_plan['gemini_title'] = gemini_title
                st.session_state.current_plan['gemini_subtitle'] = gemini_subtitle
                st.session_state.current_plan['gemini_authors'] = gemini_authors
                st.session_state.current_plan['gemini_summary'] = gemini_summary
                st.session_state.current_plan['gemini_authors_str'] = gemini_authors
                st.session_state.current_plan['gemini_authors_no_latex_str'] = gemini_authors

                # Create and prepend LaTeX preamble
                latex_preamble = create_latex_preamble(gemini_title, gemini_subtitle, gemini_authors)
                assembled_pandoc_markdown_with_latex += latex_preamble + "\n\n"
            else:
                # If it's valid JSON but not the expected format, treat as plain text
                assembled_pandoc_markdown_with_latex += cleaned_item + "\n\n"
                st.session_state.current_plan['gemini_authors_str'] = ""
                st.session_state.current_plan['gemini_authors_no_latex_str'] = ""
        except json.JSONDecodeError:
            # Handle non-JSON elements (e.g., append as plain text)
            #  st.write('list item is string:')
            # st.write(item)
            assembled_pandoc_markdown_with_latex += item + "\n\n"
        # add Publishing Information at position [1] in results

        assembled_pandoc_markdown_with_latex = clean_up_markdown(assembled_pandoc_markdown_with_latex)
        assembled_documents.append(assembled_pandoc_markdown_with_latex)

    return assembled_documents


def create_publishing_information_block(plan):
    # TODO insert isbn-fetchner
    # TODO insert year-fetcher
    # TODO insert copyright-holder
    publishing_info_block = f"""
    (c) 2024 Nimble Books LLC

    ISBN: "TK"

    Nimble Books LLC ~ NimbleBooks.com

    _Humans and models making books richer, more diverse, and more surprising._
    """
    return publishing_info_block
