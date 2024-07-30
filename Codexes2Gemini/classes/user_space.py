# user_space.py

import pickle
from typing import Dict, List
from datetime import datetime

class UserSpace:
    def __init__(self):
        self.filters = {}
        self.prompts = {}  # Change this from selected_prompts to prompts
        self.context_files = {}
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

    def save_context_files(self, name: str, file_paths: List[str]):
        self.context_files[name] = file_paths

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

