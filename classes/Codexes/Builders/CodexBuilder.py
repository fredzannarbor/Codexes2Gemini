import logging
from typing import List
from classes.Codexes.Builders.Codexes2PartsOfTheBook import Codexes2Parts
from classes.Codexes.Builders.PromptPlan import PromptPlan
import google.generativeai as genai

class CodexBuilder:
    def __init__(self):
        self.c2p = Codexes2Parts()
        self.logger = logging.getLogger(__name__)
        self.model = genai.GenerativeModel('gemini-pro')

    def build_codex_from_parts(self, parts: List[str]) -> str:
        """Build a codex from multiple parts."""
        return "\n\n".join(parts)

    def build_codex_from_plan(self, plan: PromptPlan) -> str:
        """Build a codex using a single PromptPlan."""
        return self.c2p.process_codex_to_book_part(plan)

    def build_codex_from_multiple_plans(self, plans: List[PromptPlan]) -> str:
        """Build a codex using multiple PromptPlans."""
        results = self.c2p.generate_full_book(plans)
        return self.build_codex_from_parts(results)


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

    def ensure_output_limit(self, content: str, limit: int) -> str:
        """Ensure the output is within the specified token limit."""
        if self.count_tokens(content) <= limit:
            return content
        return self.truncate_to_token_limit(content, limit)

    def use_continuation_prompt(self, plan: PromptPlan, initial_content: str) -> str:
        """Use continuation prompts to extend content to desired token count."""
        full_content = initial_content
        while self.count_tokens(full_content) < plan.desired_output_length:
            plan.context += f"\n\n{{Work So Far}}:\n\n{full_content}"
            additional_content = self.build_part(plan)
            full_content += additional_content
        return self.truncate_to_token_limit(full_content, plan.desired_output_length)

