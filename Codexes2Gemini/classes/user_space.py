# user_space.py

import pickle
from typing import Dict, List, Optional
from datetime import datetime

class SavedContext:
    def __init__(self, name: str, content: str, tags: Optional[List[str]] = None):
        self.name = name
        self.content = content
        self.tags = tags or []

class UserSpace:
    def __init__(self):
        self.filters = {}
        self.prompts = {}
        self.saved_contexts = {}
        self.results = []
        self.prompt_plans = []

    def save_filter(self, name: str, filter_data: Dict):
        if not name:
            name = f"Filter_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.filters[name] = filter_data

    def save_prompt(self, name: str, prompt: str):
        if not name:
            name = f"Prompt_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.prompts[name] = prompt

    def save_context(self, name: str, content: str, tags: Optional[List[str]] = None):
        if not name:
            name = f"Context_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.saved_contexts[name] = SavedContext(name, content, tags)

    def get_filtered_contexts(self, filter_text: str) -> Dict[str, SavedContext]:
        return {
            name: context for name, context in self.saved_contexts.items()
            if filter_text.lower() in name.lower() or
            any(filter_text.lower() in tag.lower() for tag in context.tags)
        }

    def save_result(self, result: str):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.results.append({"timestamp": timestamp, "result": result})

    def save_prompt_plan(self, prompt_plan: Dict):
        self.prompt_plans.append(prompt_plan)

def save_user_space(user_space: UserSpace):
    with open('user_space.pkl', 'wb') as f:
        pickle.dump(user_space, f)

def load_user_space() -> UserSpace:
    try:
        with open('user_space.pkl', 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        return UserSpace()