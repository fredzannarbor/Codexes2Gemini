import logging
from typing import List

import google.generativeai as genai

from ..Builders.Codexes2PartsOfTheBook import Codexes2Parts
from ..Builders.PromptGroups import PromptGroups


class PartsBuilder:
    """
    Class representing a PartsBuilder.

    Methods:
    - __init__(self)
    - count_tokens(self, text: str) -> int
    - truncate_to_token_limit(self, content: str, maximum_output_tokens: int) -> str
    - ensure_maximum_output_enforced(self, content: str, maximum_output_tokens: int) -> str
    - use_continuation_prompt(self, plan: PromptGroups, initial_content: str) -> str
    - build_part(self, plan: PromptGroups) -> str
    - build_multi_part(self, plan: PromptGroups) -> str
    - build_parts_from_codex(self, codex: str, plans: List[PromptGroups]) -> List[str]
    """
    def __init__(self):
        self.c2p = Codexes2Parts()
        self.logger = logging.getLogger(__name__)
        self.model = genai.GenerativeModel('gemini-pro')

    def count_tokens(self, text: str) -> int:
        try:
            return self.model.count_tokens(text).total_tokens
        except Exception as e:
            self.logger.error(f"Error counting tokens: {e}")
            # Fallback to character count if tokenization fails
            return len(text)

    def truncate_to_token_limit(self, content: str, maximum_output_tokens: int) -> str:
        while self.count_tokens(content) > maximum_output_tokens:
            content = content[:int(len(content) * 0.9)]  # Reduce by 10% each time
        return content

    def ensure_maximum_output_enforced(self, content: str, maximum_output_tokens: int) -> str:
        """Ensure the output is within the specified token limit."""
        if self.count_tokens(content) <= maximum_output_tokens:
            return content
        return self.truncate_to_token_limit(content, maximum_output_tokens)

    def use_continuation_prompt(self, plan: PromptGroups, initial_content: str) -> str:
        """Use continuation prompts to extend content to desired token count."""
        full_content = initial_content
        while self.count_tokens(full_content) < plan.minimum_required_output_tokens:
            plan.context += f"\n\n{{Work So Far}}:\n\n{full_content}"
            additional_content = self.build_part(plan)
            full_content += additional_content
        return self.truncate_to_token_limit(full_content, plan.minimum_required_output_tokens)

        # ... (rest of the class remains the same)

    def build_part(self, plan: PromptGroups) -> str:
        """Build a single part based on the given PromptGroups."""

        return self.c2p.process_codex_to_book_part(plan)

    def build_multi_part(self, plan: PromptGroups) -> str:
        """Build multiple parts within a single PromptGroups."""
        self.logger.info(f"Total prompts to process: {len(plan.get_prompts())}")

        result = self.c2p.process_codex_to_book_part(plan)

        self.logger.info(f"Completed processing all prompts")
        return result

    def build_parts_from_codex(self, codex: str, plans: List[PromptGroups]) -> List[str]:
        """Build multiple parts from a single codex using multiple PromptPlans."""
        results = []
        for plan in plans:
            plan.context = codex
            results.append(self.build_part(plan))
        return results



