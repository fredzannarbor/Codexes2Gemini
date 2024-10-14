import json
import logging
import os
import pickle
import time
import traceback
from datetime import datetime
from typing import Dict, List, Optional
import streamlit as st

# Define a maximum size for the pickle file (in bytes)
MAX_PICKLE_SIZE = 100 * 1024 * 1024  # 100 MB


# TO DO Warning: Pickle file is empty. Returning a new UserSpace object.
# TO DO seems to be running selected doc #1 multiple times

class SavedContext:
    """
    Represents a saved context with its name, content, and optional tags.

    Attributes:
        name (str): The name of the saved context.
        content (str): The content of the saved context.
        tags (List[str], optional): A list of tags associated with the context. Defaults to an empty list.
    """

    def __init__(self, name: str, content: str, tags: Optional[List[str]] = None):
        self.name = name
        self.content = content
        self.tags = tags or []


class PromptPack:
    def __init__(self, name, system_instructions, user_prompts, custom_prompt, override):
        self.name = name
        self.system_instructions = system_instructions
        self.user_prompts = user_prompts
        self.custom_prompt = custom_prompt
        self.override = override


class UserSpace:
    """
    A class to manage user-specific data, including filters, prompts, saved contexts, results, and prompt plans.

    Attributes:
        filters (Dict): A dictionary to store user-defined filters.
        prompts (Dict): A dictionary to store user-defined prompts.
        saved_contexts (Dict): A dictionary to store saved contexts.
        results (List): A list to store generated results.
        prompt_plans (List): A list to store prompt plans.
        name (str): The name of the UserSpace.

    Methods:
        save_filter(name: str, filter_data: Dict): Saves a filter with the given name and data.
        save_prompt(name: str, prompt: str): Saves a prompt with the given name and text.
        save_context(name: str, content: str, tags: Optional[List[str]] = None): Saves a context with the given name, content, and optional tags.
        get_filtered_contexts(filter_text: str) -> Dict[str, SavedContext]: Returns a dictionary of contexts that match the given filter text.
        save_result(result: str): Saves a generated result to the results list.
        save_prompt_plan(prompt_plan: Dict): Saves a prompt plan to the prompt plans list.
        add_result(key, result): Adds a result to the UserSpace object under the specified key.
        get_unique_name(name: str) -> str: Returns a unique name based on the given name, avoiding collisions with existing names.
    """

    def __init__(self, name: str = "Default"):
        self.filters = {}
        self.prompts = {}
        self.saved_contexts = {}
        self.results = []
        self.prompt_plans = []
        self.name = self.get_unique_name(name)
        self.prompt_packs = {
            "test123": PromptPack(
                "test123",
                [
                    "markdown"
                ],
                {
                    "gemini_get_basic_info": "Please review the entire document provided in the context from beginning to end. Allocate your time equally throughout the document.  Carry out the following tasks in batch mode.\n1. Do your best to identify the official title, subtitle, and author(s) of the document. \n2. Do your best to identify the publisher, place of publication, and year of actual publication. \n3. Summarize the content of the document. Your goal is to create a summary that accurately describes all the most important elements of the document in a way that is flexible enough to be used by many prompts.\n4. Return valid JSON output that contains keys 'gemini_title','gemini_subtitle', 'gemini_authors', 'gemini_publisher', 'gemini_place_of_publication', 'gemini_year_of_actual_publication', and 'gemini_summary'. Single and double quotation marks within the JSON output MUST be escaped. Do NOT enclose the json in triple backticks.",
                    "about_the_author_classic": "Your task is to write an \"About the Author\" section for the front matter of this document. \nFirst, review the document carefully to be certain that you have correctly identified its author.\nNow provide a summary of the author's life, emphasizing:\n- capsule biography\n- significant connections with contemporary figures who are still well known\n- motivation for writing the document, situation while doing so, post-publication impact\n- aspects of identity and experience that are particularly relevant to modern readers, for good or ill\n- modern figures who might be considered similar or analogous\n- very concise summation of achievements as an author"
                },
                "",
                False
            ),
            "collapsar-core-style-enhanced": PromptPack(
                "collapsar-core-style-enhanced",
                [
                    "nimble_editor",
                    "accurate",
                    "proactive"
                ],
                {
                    "gemini_get_basic_info": "Please review the entire document provided in the context from beginning to end. Allocate your time equally throughout the document.  Carry out the following tasks in batch mode.\n1. Do your best to identify the official title, subtitle, and author(s) of the document. \n2. Do your best to identify the publisher, place of publication, and year of actual publication. \n3. Summarize the content of the document. Your goal is to create a summary that accurately describes all the most important elements of the document in a way that is flexible enough to be used by many prompts.\n4. Return valid JSON output that contains keys 'gemini_title','gemini_subtitle', 'gemini_authors', 'gemini_publisher', 'gemini_place_of_publication', 'gemini_year_of_actual_publication', and 'gemini_summary'. Single and double quotation marks within the JSON output MUST be escaped. Do NOT enclose the json in triple backticks.",
                    "bibliographic key phrases": "Please generate ten to twelve unique bibliographic key phrases for this document. Each phrase should be two to three words long. Separate each phrase by a semicolon. Output begins: '# Bibliographic Key Phrases' followed by two new-line characters. Do NOT repeat key phrases. Stop if you begin to repeat.",
                    "Collapsar Modern Day Motivation": "Create a \"motivation\" paragraph providing the reader with the benefits of reading this book. \nThe motivation should start with a first sentence that directly addresses a well-known issue or major topic of current importance to many people.  Use pointed, vivid langauge to illustrate why the document is relevant to this topic. \nBriefly describe the main focus or subject of the document, highlighting its content and the specific area it addresses, while linking it back to the issue.  \nProvide additional context for the document by linking it to current events, societal needs, technological trends, challenges,or ongoing debates in its field.  \nSpecifically mention any important methodologies, technologies, topics, or sources that are uniquely available in this document.\nClearly state why the document is a must-read for its intended audience, whether they are researchers, practitioners, policymakers, or the general public interested in the topic. \nEmphasize the benefits the reader will gain from engaging with the document, such as understanding cutting-edge developments, enhancing their knowledge on crucial issues, or applying the document's findings to real-world problems. \nMake sure to appeal to the curiosity and interests of potential readers. \nYour goal is to convincingly present the document's significance and articulate why it deserves their attention, starting from the very first sentence.  Output begins with heading level 1 '# Publisher's Note' followed by two new-line characters. Text continues in body text format. No further headings.",
                    "about_the_author_classic": "Your task is to write an \"About the Author\" section for the front matter of this document. \nFirst, review the document carefully to be certain that you have correctly identified its author.\nNow provide a summary of the author's life, emphasizing:\n- capsule biography\n- significant connections with contemporary figures who are still well known\n- motivation for writing the document, situation while doing so, post-publication impact\n- aspects of identity and experience that are particularly relevant to modern readers, for good or ill\n- modern figures who might be considered similar or analogous\n- very concise summation of achievements as an author",
                    "Collapsar abstracts 1": "Please review this book manuscript. As you do the following tasks, remember to refer to the entire context.\n\n0. This is the beginning of the Abstracts section of the front matter. Output should begin with '#Abstracts' followed by two new-line characters.\n1. write a tldr in three words or less. Output begins with \"## TLDR (three words)\" followed by two new line characters and then the three words. ONLY provide three words, do not explain your thinking.\n2. Explain this document to me like I am five years old. Output begins with \"## ELI5\" followed by two new line characters.\n3. Write a scientific-style abstract. Output begins with \"## Scientific-Style Abstract\" followed by two new line characters.\n4. Do not include excerpts beginning 'Context'.",
                    "ELI complete idiot - abstract": "Explain this in terms suitable for someone who is both painfully stupid and willfully ignorant. Do not describe the reader; provide only the explanation.  Use no more than 50 words. Output begins with second level heading '## For Complete Idiots Only' followed by two new lines.",
                    "mnemonics - abstract": " For all the following tasks, your goal is summarizing the key learnings from the full text of the book provided in the context.\n 1. This will be the \"Learning Aids\" secion of the Front Matter. Output should begin with heading level 1 '# Learning Aids' followed by two new line characters.\n 2. Create an acronymic mnemonic. Continue the output with heading level 2 '## Mnemonic (acronym)' followed by two lines and your response in body text format.. This section should end with two new lines.\n3. Create a mnemonic using a progression of related words. Example: My Dear Aunt Sally. Continue the output with '## Mnemonic (speakable)' followed by two new lines and your response. This section should end with two new lines.\n4. Create a singable mnemonic in the form of a ditty to a popular tune. Continue the output with '## Mnemonic (singable)' followed by the lyrics in pandoc markdown poetry lazy block format. Start each block of verses with a single > character. Each lyric line must be followed by two new line characters. .\nIf there are verses, choruses, or other sections, they should be separated by blank lines for better readability. This section should end with two new lines.\n",
                    "most important passages - reasoning": "Select the seven most important passages of between one and three paragraphs long from took. Concisely explain why you selected each passage. Include the exact full text of each passage with a reference by chapter or section. Use Pandoc markdown lazy block quotes, which only require the > character on the first line of the block quote. Output begins with heading level 1, '# Most Important Passages'.",
                    "Collapsar Create Condensed Matter": "Backstory:\n\nCollapsar Classics was launched to bring 19th and early 20th century books to modern audiences in a fresh and convenient way. Each book is approximately 15,000 words and is presented in a phone-sized 4 x 6\" paperback format. Each Collapsar Classic includes a section called \"Condensed Matter\" (a play on front matter). Much like the Reader's Digest Condensed Books that were popular many decades ago, the Condensed Matters is meant to give you the best parts of the original in a much smaller space.\n\nYour Task:\n\nWrite the Condensed Matter section for the document in the context. The document in the context is permissioned public domain so you have complete freedom to quote from it.\nWork only on the Condensed Matter section. Do not refer to the backstory.\nYour goal is to write a highly readable condensed version of the original. \nYou must cover the entire scope of the original within your output window. Thus, your condensed prose should begin at or near the beginning of the original and end at or near the end of it.\nYou should use the exact words of the context frequently.\nYou may use transitional devices such as ellipses, dingbats, or bracketed comments.\nYou may make sparing use of framing devices in your own words.\nRemember, your overriding goal is to give modern readers the benefit of reading this document in as original a form as possible, but as much condensed as possible.\nOutput must begin '# Condensed Matter' followed immediately by two new-line characters.",
                    "glossary-browsable": "Your task is to create a browsable glossary of old-fashioned, foreign-language, or technical terms. Unlike a normal (boring) glossary, your discussion should sometimes go beyond definitions and may include remarks that are opinionated, pointed, skeptical, or insightful. \n\nOutput begins with heading level 1: '# Browsable Glossary'.  \n\nEach glossary entry is body text, flush left, and is NOT a heading.  \n\nEach glossary entry MUST be on its own line followed by two new-line characters.",
                    "Place in historical context": "Your task is to place this work in its historical context. Please explain its significance at the time of publication; its role in discourse in subsequent years; why it may be of interest now, especially to any specific, pertinent, recent events or trends; and how it may be important as future decades unroll.\n\nYour work should be accurate and your factual assertions grounded in accurate citations to real works.  Output begins with heading level one '# Historical Context' followed by two new-line characters.  Do not include the title of the work in the heading.",
                    "timeline-major": "Create a timeline of twenty to forty major events in the book in ascending chronological order. While respecting that some events are more major than others, try to draw the events from throughout the book and cover the timespan fairly. \n\nOutput begins with heading level 1: '# Timeline'. \n\nEach event entry MUST be on its own line followed by TWO new line characters. \n\nIf you begin to repeat yourself, STOP.",
                    "Truth in Publishing - abstract": "Your task is to write a light-hearted \"Truth in Publishing\" abstract of the context. You are to candidly disclose any issues that might materially impair the reader's ability to enjoy reading the document. Emphasize both strengths and weaknesses. Don't hesitate to poke fun at the style, tone, or content, highlighting clich\u00e9s, repetitive language, or overused tropes. But do be fair in explaining what is good about the book. And if a book is great, or terrible, you can just say so.  You do not need to be obsessed with balance.  Your goal is to be both informative and amusing. Output begins '# Truth in Publishing (Disclosures)' followed by two new lines.",

                },
                "",
                "Add at end of other user prompts",

            ),
        }

    def get_filtered_contexts(self, filter_text: str) -> Dict[str, SavedContext]:
        """Returns a dictionary of contexts that match the given filter text.

        Args:
            filter_text (str): The text to filter by.

        Returns:
            Dict[str, SavedContext]: A dictionary of contexts that match the filter.
        """
        return {
            name: context for name, context in self.saved_contexts.items()
            if filter_text.lower() in name.lower() or
               any(filter_text.lower() in tag.lower() for tag in context.tags)
        }

    def get_prompt_packs(self) -> Dict[str, PromptPack]:
        """Returns a dictionary of saved PromptPacks.

        Returns:
            Dict[str, PromptPack]: A dictionary where keys are pack names and values are PromptPackobjects.
        """
        if not hasattr(self, 'prompt_packs'):
            self.prompt_packs = {}
        return self.prompt_packs

    def get_unique_name(self, name: str) -> str:
        """Returns a unique name based on the given name, avoiding collisions with existing names.

        Args:
            name (str): The desired name.

        Returns:
            str: A unique name.
        """
        existing_names = [f.replace("user_space_", "").replace(".pkl", "") for f in os.listdir() if
                          f.startswith("user_space_")]
        if name not in existing_names:
            return name
        else:
            counter = 1
            while f"{name}_{counter}" in existing_names:
                counter += 1
            return f"{name}_{counter}"

    def save_result(self, result: str):
        """Saves a generated result to the results list.

        Args:
            result (str): The generated result.
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.results.append({"timestamp": timestamp, "result": result})

    def save_prompt_plan(self, prompt_plan: Dict):
        """Saves a prompt plan to the prompt plans list.

        Args:
            prompt_plan (Dict): The prompt plan data.
        """
        self.prompt_plans.append(prompt_plan)

    def save_filter(self, name: str, filter_data: Dict):
        """Saves a filter with the given name and data.

        Args:
            name (str): The name of the filter.
            filter_data (Dict): The data associated with the filter.
        """
        if not name:
            name = f"Filter_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.filters[name] = filter_data

    def save_prompt(self, name: str, prompt: str):
        """Saves a prompt with the given name and text.

        Args:
            name (str): The name of the prompt.
            prompt (str): The text of the prompt.
        """
        if not name:
            name = f"Prompt_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.prompts[name] = prompt

    def save_context(self, name: str, content: str, tags: Optional[List[str]] = None):
        """Saves a context with the given name, content, and optional tags.

        Args:
            name (str): The name of the context.
            content (str): The content of the context.
            tags (List[str], optional): A list of tags associated with the context. Defaults to None.
        """
        if not name:
            name = f"Context_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.saved_contexts[name] = SavedContext(name, content, tags)

    def add_result(self, key, result):
        """Adds a result to the UserSpace object under the specified key.

        Args:
            key (str): The key to store the result under.
            result (Any): The result to store.
        """
        timestamp = time.time()  # this gives a timestamp
        self.__dict__[key] = {"result": result, "time": timestamp}

    def create_prompt_pack(self, pack_name: str, system_instructions: List[str],
                           user_prompts: Dict[str, str], custom_prompt: str, override: bool):
        """Creates a new PromptPack and saves it to the UserSpace.

        Args:
            pack_name (str): The name of the new PromptPack.
            system_instructions (List[str]): A list of system instruction keys.
            user_prompts (Dict[str, str]): A dictionary of user prompt keys and their corresponding prompts.
            custom_prompt (str): A custom user prompt.
            override (bool): Whether the custom prompt should override other user prompts.
        """
        if pack_name in self.get_prompt_packs():
            raise ValueError(f"PromptPack '{pack_name}' already exists.")

        pack = PromptPack(pack_name, system_instructions, user_prompts, custom_prompt, override)
        self.save_instruction_pack(pack)

    def read_prompt_pack(self, pack_name: str) -> PromptPack:
        """Reads an PromptPackfrom the UserSpace.

        Args:
            pack_name (str): The name of the PromptPack to read.

        Returns:
            PromptPack: The PromptPackobject if found, otherwise None.
        """
        return self.get_prompt_packs().get(pack_name)

    def update_prompt_pack(self, pack_name: str, system_instructions: Optional[List[str]] = None,
                           user_prompts: Optional[Dict[str, str]] = None,
                           custom_prompt: Optional[str] = None, override: Optional[bool] = None):
        """Updates an existing PromptPack in the UserSpace.

        Args:
            pack_name (str): The name of the PromptPack to update.
            system_instructions (List[str], optional): The updated list of system instruction keys.
            user_prompts (Dict[str, str], optional): The updated dictionary of user prompt keys and prompts.
            custom_prompt (str, optional): The updated custom user prompt.
            override (bool, optional): Whether the custom prompt should override other user prompts.
        """
        pack = self.read_prompt_pack(pack_name)
        if not pack:
            raise ValueError(f"PromptPack '{pack_name}' not found.")

        if system_instructions is not None:
            pack.system_instructions = system_instructions
        if user_prompts is not None:
            pack.user_prompts = user_prompts
        if custom_prompt is not None:
            pack.custom_prompt = custom_prompt
        if override is not None:
            pack.override = override

        self.save_instruction_pack(pack)

    def destroy_prompt_pack(self, pack_name: str):
        """Deletes an PromptPack from the UserSpace.

        Args:
            pack_name (str): The name of the PromptPack to delete.
        """
        if pack_name not in self.get_prompt_packs():
            raise ValueError(f"PromptPack '{pack_name}' not found.")

        del self.prompt_packs[pack_name]
        self.save_user_space(self)

    def rename_prompt_pack(self, old_name: str, new_name: str):
        """Renames an PromptPack in the UserSpace.

        Args:
            old_name (str): The current name of the PromptPack.
            new_name (str): The new name for the PromptPack.
        """
        if old_name not in self.get_prompt_packs():
            raise ValueError(f"PromptPack '{old_name}' not found.")
        if new_name in self.get_prompt_packs():
            raise ValueError(f"PromptPack '{new_name}' already exists.")

        pack = self.prompt_packs[old_name]
        pack.name = new_name
        self.prompt_packs[new_name] = pack
        del self.prompt_packs[old_name]
        self.save_user_space(self)

    def save_prompt_pack(self, pack: PromptPack):
        """Saves an PromptPack.

        Args:
            pack (PromptPack): The PromptPackobject to save.
        """
        if not hasattr(self, 'prompt_packs'):
            self.prompt_packs = {}
        self.prompt_packs[pack.name] = pack
        self.save_user_space()

    def save_user_space(self):  # Add self as argument
        """Saves the UserSpace object to a pickle file.

        Args:
            user_space (UserSpace): The UserSpace object to save.
        """
        try:
            # Check if the pickle file already exists and its size
            file_path = f"user_space_{self.name}.pkl"
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                if file_size > MAX_PICKLE_SIZE:
                    print(f"Warning: Pickle file '{file_path}' is larger than {MAX_PICKLE_SIZE} bytes. Not saving.")
                    return

            # Save the UserSpace object to a pickle file
            with open(file_path, 'wb') as f:
                pickle.dump(self, f)  # Pass self to pickle.dump
        except Exception as e:
            print(f"Error saving UserSpace: {e}")
            st.error(traceback.format_exc())

    def load_user_space(name: str = "Default"):
        """Loads the UserSpace object from a pickle file.

        Args:
            name (str): The name of the UserSpace to load. Defaults to "Default".

        Returns:
            UserSpace: The loaded UserSpace object.
        """
        try:
            # Check if the pickle file exists and its size
            file_path = f"user_space_{name}.pkl"
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)

                if file_size > MAX_PICKLE_SIZE:
                    print(f"Warning: Pickle file '{file_path}' is larger than {MAX_PICKLE_SIZE} bytes. Not loading.")
                    return UserSpace(name)

                if file_size == 0:
                    print("Warning: Pickle file is empty. Returning a new UserSpace object.")
                    return UserSpace(name)

                # Load the UserSpace object from the pickle file
                with open(file_path, 'rb') as f:
                    loaded_object = pickle.load(f)

                    # Check if the loaded object is of the correct class
                    if isinstance(loaded_object, UserSpace):
                        return loaded_object
                    else:
                        print(f"Warning: Loaded object is not of type UserSpace. Returning a new UserSpace object.")
                        return UserSpace(name)
            else:  # create new userspace object
                return UserSpace(name)

        except FileNotFoundError:
            return UserSpace(name)
        except Exception as e:
            print(f"Error loading UserSpace: {e}")
            logging.error(f"Error loading UserSpace {traceback.format_exc()}")
            return UserSpace(name)


    def load_prompt_pack_from_json(self, pack_name):
        """Loads an PromptPack from a JSON file.

        Args:
            pack_name (str): The name of the PromptPack to load.

        Returns:
            PromptPack: The loaded PromptPackobject if found, otherwise None.
        """
        try:
            with open(f"user_data/{self.name}/prompt_pack_{pack_name}.json", "r") as f:
                pack_data = json.load(f)
            return PromptPack(**pack_data)
        except FileNotFoundError:
            return None
        except Exception as e:
            print(f"Error loading PromptPack from JSON: {e}")
            logging.error(f"Error loading PromptPack from JSON: {traceback.format_exc()}")
            return None


    def save_prompt_pack_to_json(self, pack):
        """Saves a PromptPack to a JSON file.

        Args:
            pack (PromptPack): The PromptPackobject to save.
        """
        # make sure user_data / self.name exists
        if not os.path.exists(f"user_data/{self.name}"):
            os.makedirs(f"user_data/{self.name}")

        try:
            with open(f"user_data/{self.name}/prompt_pack_{pack.name}.json", "w") as f:
                json.dump(pack.__dict__, f, indent=4)
        except Exception as e:
            print(f"Error saving PromptPack to JSON: {e}")
            logging.error(f"Error saving PromptPack to JSON: {traceback.format_exc()}")
