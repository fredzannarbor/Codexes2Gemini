
#  Copyright (c) 2023-2024. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com
import argparse
import json
import logging
import os
import re
import traceback
import uuid
from pathlib import Path
from random import choice

import pandas as pd

import DefoeHelpers as dh
from Codexes2Gemini.classes.Utilities.gpt3complete import chatcomplete
from classes.Utilities.classes_utilities import select_dataframe_rows_from_string, safely_add_empty_column, \
    create_safe_file_name

'''
THis is a class that takes a set of specifications for a codex book then generates a draft of the book in docx format.

The specifications include the following inputs as json, csv, xlsx, files or objects.

1.  Selected book idea.
2.  Selected author voice.
3.  Selected protagonist with description.
4.  Selected antagonist with description.
5.  Selected cast of characters with descriptions.
6.  Selected settings with descriptions.
7.  Selected plot points with descriptions.
8.  Selected themes with descriptions.
9.  Selected revelations with descriptions.
10. Selected character arcs with descriptions.
11. Specified number of chapters and number of scenes per chapter.
12. Specified number of words for complete document.
13. Special instructions for creating outline.
14. Fine tuning parameter for book.
15. Text of the book so far.

Desired outputs are:
1.  Chapter outline of book
2.  Scene outline for each chapter
3.  LLM draft of each scene assembled into a single book draft.
'''

from classes.Utilities.classes_utilities import set_logging_level

set_logging_level("INFO")

class CodexSpecs2Book:

    def __init__(self, book_idea=None, author_voice=None, protagonist=None, antagonist=None, cast_of_characters=None,
                 locations=None, plot_points=None, themes=None, revelations=None, character_arcs=None, num_chapters=12,
                 num_scenes_per_chapter=7, num_words=80000, special_instructions=None, book_so_far=None,
                 factual_stipulations=None):
        """

        Initializes a Book object with the provided parameters.

        Parameters:
        - book_idea (str, optional): The idea or concept of the book. Defaults to None.
        - author_voice (str, optional): The desired writing style or voice of the author. Defaults to None.
        - protagonist (str, optional): The main character or protagonist of the book. Defaults to None.
        - antagonist (str, optional): The opposing character or antagonist of the book. Defaults to None.
        - cast_of_characters (list, optional): A list of characters involved in the book. Defaults to None.
        - locations (list, optional): A list of locations or settings in the book. Defaults to None.
        - plot_points (list, optional): A list of major"""
        self.book_idea = book_idea
        self.author_voice = author_voice
        self.protagonist = protagonist
        self.antagonist = antagonist
        self.cast_of_characters = cast_of_characters
        self.locations = locations
        self.plot_points = plot_points
        self.themes = themes
        self.revelations = revelations
        self.character_arcs = character_arcs
        self.factual_stipulations = None

        self.num_chapters = num_chapters
        self.num_scenes_per_chapter = num_scenes_per_chapter
        self.num_words = num_words
        self.special_instructions = special_instructions
        self.book_so_far = book_so_far
        self.book_outline = None
        self.scene_outlines = None
        self.book_draft = None
        self.book_draft_path = None
        self.book_draft_name = None


    def get_attribute(self, attribute):
        return getattr(self, attribute)

    def set_attribute(self, attribute, value):
        setattr(self, attribute, value)

    def get_all_attributes(self):
        return self.__dict__.keys()

    def extract_scenes(chapter_plan):
        # split string into list at every occurrence of "Scene "
        chapter_scenes = re.split(r'Scene\s', chapter_plan)[1:]
        # verify that returning a list
        if isinstance(chapter_scenes, str):
            raise ValueError('Could not transform chapter_plan into scenes')
        return (chapter_scenes)

    def spec_df_row2variables(self, spec_df):
        """

        Method Name: spec_df_row2variables

        Description:
        This method takes a DataFrame, 'spec_df', as input and extracts various variable values from specific rows of the DataFrame. It assigns these values to corresponding variables and returns
        * them as a tuple.

        Parameters:
        - self: The class instance (implicitly passed).
        - spec_df: The DataFrame from which variable values will be extracted.

        Returns:
        A tuple containing the following variable values extracted from the 'spec_df' DataFrame:
        - title: The value from the 'title' row of 'spec_df'.
        - idea: The value from the 'Idea' row of 'spec_df'.
        - author_voice: The value from the 'author_voice' row of 'spec_df'.
        - protagonist: The value from the 'protagonist' row of 'spec_df'.
        - antagonist: The value from the 'antagonist' row of 'spec_df'.
        - good_guys: The value from the 'good_guys' row of 'spec_df'.
        - bad_guys: The value from the 'bad_guys' row of 'spec_df'.
        - locations: The value from the 'locations' row of 'spec_df'.
        - mcguffins: The value from the 'mcguffins' row of 'spec_df'.
        - plot_twists: The value from the 'plot_twists' row of 'spec_df'.
        - themes: The value from the 'themes' row of 'spec_df'.
        - revelations: The value from the 'revelations' row of 'spec_df'.
        - character_arcs: The value from the 'character_arcs' row of 'spec_df'.
        - num_chapters: The value from the 'num_chapters' row of 'spec_df', converted to an integer.
        - num_scenes_per_chapter: The value from the 'num_scenes_per_chapter' row of 'spec_df', converted to an integer.
        - num_tokens_total: The value from the 'num_tokens_total' row of 'spec_df', converted to an integer.
        - special_instructions: The value from the 'special_instructions' row of 'spec_df'.
        - thisbookplan: The value from the 'thisbookplan' row of 'spec_df'.
        - thischapterplan: Empty string (initially) for further usage (not extracted from 'spec_df').
        - thissceneplan: Empty string (initially) for further usage (not extracted from 'spec_df').

        Example Usage:
        df = pd.DataFrame({
            'Column A': ['value1', 'value2', 'value3'],
            'Column B': ['value4', 'value5', 'value6'],
            'Column C': ['value7', 'value8', 'value9']
        })
        result = spec_df_row2variables(df)
        print(result)
        # Output: ('value1', 'value2', 'value4', 'value5', 'value7', 'value8', 'value9')

        """
        # get variable values from index of spec_df
        # logging.info(spec_df)
        title = spec_df.loc['title', spec_df.columns[0]]
        idea = spec_df.loc['Idea', spec_df.columns[0]]
        author_voice = spec_df.loc['author_voice', spec_df.columns[0]]
        protagonist = spec_df.loc['protagonist', spec_df.columns[0]]
        antagonist = spec_df.loc['antagonist', spec_df.columns[0]]
        good_guys = spec_df.loc['good_guys', spec_df.columns[0]]
        bad_guys = spec_df.loc['bad_guys', spec_df.columns[0]]
        locations = spec_df.loc['locations', spec_df.columns[0]]
        mcguffins = spec_df.loc['mcguffins', spec_df.columns[0]]
        plot_twists = spec_df.loc['plot_twists', spec_df.columns[0]]
        themes = spec_df.loc['themes', spec_df.columns[0]]
        revelations = spec_df.loc['revelations', spec_df.columns[0]]
        character_arcs = spec_df.loc['character_arcs', spec_df.columns[0]]
        num_chapters = spec_df.loc['num_chapters', spec_df.columns[0]]
        num_chapters = int(num_chapters)
        num_scenes_per_chapter = spec_df.loc['num_scenes_per_chapter', spec_df.columns[0]]
        num_scenes_per_chapter = int(num_scenes_per_chapter)
        num_tokens_total = spec_df.loc['num_tokens_total', spec_df.columns[0]]
        num_tokens_total = int(num_tokens_total)
        special_instructions = spec_df.loc['special_instructions', spec_df.columns[0]]
        thisbookplan = spec_df.loc['thisbookplan', spec_df.columns[0]]
        thischapterplan = ''
        thissceneplan = ''
        return title, idea, author_voice, protagonist, antagonist, good_guys, bad_guys, locations, mcguffins, plot_twists, themes, revelations, character_arcs, num_chapters, num_scenes_per_chapter, num_tokens_total, special_instructions, thisbookplan, thischapterplan, thissceneplan



    def create_chapter_plans(self, spec_df, model, max_tokens):
        # Check if spec_df is a Series and convert to DataFrame for processing
        if isinstance(spec_df, pd.Series):
            spec_df = spec_df.to_frame().T

        # Ensure the DataFrame has a meaningful index (if needed) and columns
        spec_df.reset_index(drop=True, inplace=True)

        # Create the context prompt for this chapter plan
        context_prompt = ''
        for idx, row in spec_df.iterrows():
            # Assuming the first column contains key specification details for each book
            book_details = '\n'.join([f"{col}: {val}" for col, val in row.items() if pd.notna(val)])
            context_prompt += book_details + "\n\n"

        chapter_plans = []
        num_chapters = spec_df['num_chapters'].iloc[0]
        num_chapters = int(num_chapters)  # Convert to int if not already, no need for else

        for chapter_number in range(1, num_chapters + 1):  # Including num_chapters in loop
            prompt = f"Given the context and book plan provided below, create a detailed scene-by-scene plan for chapter {chapter_number}. Each scene should be an element in a Python list.\n\n Context:  {context_prompt}.\n\nChapter {chapter_number}"
            # prompt = "foo"
            chapter_plans_text = chatcomplete("CreateChapterPlan", prompt=prompt, engine=model, max_tokens=max_tokens)
            logging.info(f"submitting prompt {prompt}")
            logging.info(chapter_plans_text)
            chapter_plans.append(chapter_plans_text)

        return chapter_plans

    def get_missing_valid_text(self, prompt, model):
        response_text = chatcomplete("GetMissingValid", prompt, model, max_tokens)

        return response_text

    def get_missing_valid_integer(self, prompt, model):
        response_string = chatcomplete("GetMissingValidInteger", prompt, model, max_tokens)
        response_int = int(response_string)
        return response_int

    def fill_missing_values_updated(self, spec_df, model):
        # Ensure spec_df is a DataFrame
        was_series = False
        if isinstance(spec_df, pd.Series):
            spec_df = spec_df.to_frame().T
            was_series = True

        # Iterate over the DataFrame to fill missing values
        for idx, row in spec_df.iterrows():
            for missing_name, value in row.items():
                if pd.isna(value) or value == '':
                    # Build a context prompt that includes all other column values for the current row
                    context_parts = [f"{col}: {val}" for col, val in row.items() if
                                     col != missing_name and pd.notna(val)]
                    context_prompt = "\n".join(context_parts)

                    # Add the missing field notice to the context prompt
                    context_prompt += f'\nMissing field: {missing_name}'
                    logging.info(f"Context prompt is: {context_prompt}")

                    # Determine the replacement value based on the field
                    if "num_chapters" in missing_name or "num_scenes_" in missing_name or "num_tokens_" in missing_name:
                        new_value = self.get_missing_valid_integer(context_prompt, model)
                    else:
                        new_value = self.get_missing_valid_text(context_prompt, model)

                    logging.info(f"New value for {missing_name} is {new_value}")
                    # Directly update the DataFrame
                    spec_df.at[idx, missing_name] = new_value

        # Convert back to a Series if the original input was a Series
        if was_series:
            return spec_df.squeeze()  # Converts back to Series if only one row
        return spec_df

    def specs2prompt(self, spec_df):
        ''' takes a spec_df and returns a context prompt '''
        context = spec_df.to_json()
        context_as_string = str(context)
        return context_as_string

    def random_scene_specs(self, bad_guys, good_guys, locations):
        # Randomly choosing a setting and location for each scene
        scene_location = choice(locations)
        scene_side_characters = choice(good_guys) + choice(bad_guys)
        # 75% chance of protagonist being present
        protagonist_present = choice([True, True, True, False])
        antagonist_present = choice([True, True, False, False])
        return antagonist_present, protagonist_present, scene_location, scene_side_characters




    def modify_scene_attributes(self, chapter, scene_num):
        """
        Modifies the attributes of a scene based on the chapter plan and potentially previous scene plans.

        Parameters:
            chapter (dict): The chapter dictionary containing at least 'thischapterplan' and possibly previous scene plans.
            scene_num (int): The scene number to generate or modify attributes for.

        Returns:
            dict: The updated scene attributes.
        """
        # Extract necessary details from the chapter dictionary
        thischapterplan = chapter.get('thischapterplan', '')
        # Initialize previoussceneplan if you have logic to fetch previous scene plans
        previoussceneplan = chapter.get('previoussceneplan',
                                        '')  # This would need logic to fetch the actual previous scene plan

        # Create the prompt based on whether a previous scene plan exists
        if previoussceneplan:
            prompt = f"Chapter plan:\n\n{thischapterplan}\n\nPrevious scene plan was: {previoussceneplan}. Plan for this scene # {scene_num}: \n\n"
        else:
            prompt = f"Chapter plan:\n\n{thischapterplan}\n\nPlan for this scene # {scene_num}: \n\n"

        logging.info(f"Submitting prompt: {prompt}")
        try:
            # Assuming `chatcomplete` function or method exists and is accessible
            thissceneplan_response_text = chatcomplete("EnhanceSceneAttributes", prompt=prompt, model=self.model,
                                                       max_tokens=self.max_tokens)
            scene_attributes = {'thissceneplan': thissceneplan_response_text}
        except Exception as e:
            logging.error(f"Error generating scene attributes: {e}")
            scene_attributes = {'thissceneplan': str(e)}

        return scene_attributes

    # Define a function to create a flat list of all scenes along with their attributes

    def add_scene_texts(self, spec_df, num_scenes_this_run, job_id, model, max_tokens):
        """
        Adds or updates scene text for each scene in each chapter of a single book's specification.

        Parameters:
            spec_df (pandas.DataFrame): DataFrame containing the specifications for a single book.
            num_scenes_this_run (int): The number of scenes to process in this run.
            job_id (str): An identifier for the job, used in naming output files.
            model (str): The model identifier for generating scene text.
            max_tokens (int): The maximum number of tokens to generate.

        Returns:
            pandas.DataFrame: Updated DataFrame with scene texts added to each scene.
        """
        # Extract chapters from the book's specifications
        chapters = spec_df.at[0, 'chapters']  # Adjust the row index as needed

        # Loop through each chapter to process its scenes
        for chapter in chapters:
            thischapterplan = chapter.get('thischapterplan', '')
            scenes = chapter.get('List of Scenes', [])

            # Process each scene up to the specified limit
            for scene_num, scene in enumerate(scenes[:num_scenes_this_run], start=1):
                # Call to modify or add text to the scene attributes
                updated_scene = self.add_text_to_scene_attributes({
                    'thischapterplan': thischapterplan,
                    'thissceneplan': scene.get('thissceneplan', ''),
                }, scene_num, job_id, model, max_tokens)

                # Update the scene in the chapter's scene list
                scenes[scene_num - 1] = updated_scene

            # Update the chapter with the modified scenes
            chapter['List of Scenes'] = scenes

        # Update the 'chapters' column in the DataFrame with the updated chapters
        spec_df.at[0, 'chapters'] = chapters

        return spec_df

    def add_text_to_scene_attributes(self, scene_attributes, scene_num, job_id, model, max_tokens):
        """
        Generates or updates text for a specific scene based on the chapter plan and scene attributes.

        Parameters:
            scene_attributes (dict): The current attributes of the scene including the chapter plan.
            scene_num (int): The scene number within its chapter.
            job_id (str): An identifier for the current processing job, used in file naming.
            model (str): The model identifier for generating scene text.
            max_tokens (int): The maximum number of tokens for the generation request.

        Returns:
            dict: Updated scene attributes including the generated or updated scene text.
        """
        # Construct the prompt for scene text generation
        prompt = f"Chapter plan:\n\n{scene_attributes['thischapterplan']}\n\nPlan for this scene # {scene_num}: \n\n{scene_attributes.get('thissceneplan', '')}"

        logging.info(f"Submitting prompt: {prompt}")
        try:
            # Assuming `chatcomplete` is a function you've defined to interact with a text generation API
            scene_text_response = chatcomplete(prompt=prompt, model=model, max_tokens=max_tokens)
            logging.info(scene_text_response)
            # Update the scene_attributes with the response text
            scene_attributes['scene text'] = scene_text_response
        except Exception as e:
            logging.error(f"Error generating text for scene {scene_num}: {e}")
            scene_attributes['scene text'] = 'Error generating scene text'

        # Write the generated scene text to a file for logging or review
        with open(f'output/{job_id}_scene_text_results.txt', 'a') as file:
            file.write(f"Scene #{scene_num}: {scene_attributes['scene text']}\n")

        return scene_attributes



    def get_short_title(self, title):
        short_title = title.split()
        # get last three items in short_title
        short_title = short_title[-3:]
        # logging.info(short_title)
        short_title = '_'.join(short_title)
        short_title = re.sub(r'\W+', '_', short_title)
        logging.info(f"short_title is {short_title}")
        return short_title

    def complete_book_specs_df(self, specs_df, num_books_this_run, model):
        """
        Completes the book specifications for each book in the DataFrame.

        Parameters:
            specs_df (pandas.DataFrame): The DataFrame containing book specifications.
            num_books_this_run (int): The number of books to process in this run.

        Returns:
            pandas.DataFrame: The DataFrame with completed book specifications.
        """
        revised_book_specs_df = pd.DataFrame()
        num_books_processed = 0

        for index, row in specs_df.iterrows():
            if num_books_processed >= num_books_this_run:
                break
            spec_complete_df = pd.DataFrame([row])  # Convert the Series to a DataFrame for processing
            spec_complete_df = self.fill_missing_values_updated(spec_complete_df, model)

            # Append the processed book specs to the revised_book_specs_df
            revised_book_specs_df = revised_book_specs_df.append(spec_complete_df, ignore_index=True)
            num_books_processed += 1

        return revised_book_specs_df

    def read_book_specs_df(self, specs_file_path):
        """
        Reads the book specifications from a CSV or XLSX file.
        Assumes each book's specifications are stored as a row.

        Parameters:
            specs_file_path (str): The file path to the specifications file.

        Returns:
            pandas.DataFrame: A DataFrame where each row contains the specifications for one book.
        """
        # Determine the file type and read the file accordingly
        specs_file = Path(specs_file_path)
        if specs_file.suffix == '.csv':
            specs_df = pd.read_csv(specs_file_path)
        elif specs_file.suffix == '.xlsx':
            specs_df = pd.read_excel(specs_file_path)
        else:
            raise ValueError(f"Unsupported file type: {specs_file.suffix}")

        # Check if the DataFrame is empty
        if specs_df.empty:
            raise ValueError("The specifications file is empty or could not be read properly.")

        # add an index
        specs_df.reset_index(drop=True, inplace=True)


        return specs_df





    def update_specs_df(self, specs_df, updated_book_row, index):
        """
        Update the specs DataFrame or Series with the updated book row.
        """
        if isinstance(specs_df, pd.DataFrame):
            specs_df.loc[index] = updated_book_row
        elif isinstance(specs_df, pd.Series):
            specs_df = updated_book_row
        else:
            raise ValueError("specs_df must be either a DataFrame or a Series")
        return specs_df

    def save_processed_data(self, data_df, job_id, output_dir, stage_name):
        """
        Generalizes the saving of processed data for different stages (book specs, book plans, etc.).

        Parameters:
            data_df (pandas.DataFrame): The DataFrame containing the processed data.
            job_id (str): An identifier for the job.
            output_dir (str): The base directory for saving output files.
            stage_name (str): The processing stage name (e.g., 'bookplans', 'specs').

        Returns:
            str: The path to the saved JSON file for verification or further use.
        """
        # Create a safe filename based on the stage name and job ID
        safefilename = f"{stage_name}_{job_id}"

        # Ensure the output directory for the stage exists
        stage_dir = os.path.join(output_dir, stage_name)
        if not os.path.exists(stage_dir):
            os.makedirs(stage_dir)

        # Define file paths
        json_output_path = os.path.join(stage_dir, f"{safefilename}.json")
        csv_output_path = os.path.join(stage_dir, f"{safefilename}.csv")

        # Save data to files
        data_df.to_json(json_output_path)
        data_df.to_csv(csv_output_path)

        logging.info(f"Saved {stage_name} data to {json_output_path} and {csv_output_path}")
        return json_output_path

    def write_rows_to_files(self, specs_df, output_dir):
        """
        Writes each row of the specs DataFrame to a file within its own directory in output/editing.

        Parameters:
            specs_df (pandas.DataFrame): The DataFrame containing book specifications.
            output_dir (str): The base output directory.
        """
        for index, row in specs_df.iterrows():
            # Use a unique identifier from the row for the directory name, e.g., short_title
            dir_name = create_safe_file_name(row.get('short_title', 'default_title'))
            row_dir = os.path.join(output_dir, dir_name)

            # Create the directory if it doesn't exist
            os.makedirs(row_dir, exist_ok=True)

            # Define the file path
            file_path = os.path.join(row_dir, f"{dir_name}_specs.json")

            # Convert the row to a dictionary and save it to a JSON file
            row_dict = row.to_dict()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(row_dict, f, ensure_ascii=False, indent=4)

                # get list of keys from row_dict
                keys = row_dict.keys()
                if "drafts" in keys:

                    a = row['drafts']
                    markdown_file_path = os.path.join(row_dir, f"{dir_name}_draft.md")
                    # save joined markdown as file
                    with open(markdown_file_path, 'w', encoding='utf-8') as fmd:
                        fmd.write(a[3])
                    print(f"Saved specs and draft for {dir_name} to {file_path}")
                else:
                    print(f"Saved specs only to {file_path}")
                return

    def initialize_folder_spaces(self, output_dir):
        revised_book_specs_dir = os.path.join(output_dir, "revised_book_specs")
        bookplan_dir = os.path.join(output_dir, "bookplans")
        chapterplans_dir = os.path.join(output_dir, "chapterplans")
        sceneplans_dir = os.path.join(output_dir, "sceneplans")
        scenetext_dir = os.path.join(output_dir, "scenetext")
        for d in [revised_book_specs_dir, bookplan_dir, chapterplans_dir, sceneplans_dir, scenetext_dir]:
            if not os.path.exists(d):
                os.makedirs(d)
        return revised_book_specs_dir, bookplan_dir, chapterplans_dir, sceneplans_dir, scenetext_dir

    def handle_partial_completion(self, book_row, job_id, output_dir):

        pass

    def create_scene_plans(self, book_row, model, max_tokens):
        """
        Generates scene plans for each scene within each chapter of a book.

        Parameters:
            book_row (pandas.Series or dict): The book row containing chapter plans and other details.
            model (str): The model identifier for generating scene text.
            max_tokens (int): The maximum number of tokens for the generation request.

        Returns:
            None: This function returns a list of the scene plans for all scenes and all chapters.
        """
        # Check if chapter_plans exists in the book_row
        if 'chapter_plans' not in book_row or not book_row['chapter_plans']:
            logging.error("No chapter plans found for this book.")
            return

        chapter_plans = book_row['chapter_plans']

        # Initialize a list to hold all scene plans for the book
        all_scene_plans = []
        num_scenes_per_chapter = book_row['num_scenes_per_chapter']
        num_scenes_per_chapter = int(num_scenes_per_chapter)
        thisbook_short_title = book_row['short_title'][0]
        for chapter_index, chapter_plan in enumerate(chapter_plans):
            logging.info(f"Beginning chapter plan: {chapter_plan[:40]}")

            chapter_scene_plans = []

            for scene_index in range(num_scenes_per_chapter):
                prompt = f"Generate a detailed plan for scene {scene_index + 1} based on the relevant portions of the chapter plan: {chapter_plan}"
                print(
                    f"Creating plan for scene {scene_index + 1} of {num_scenes_per_chapter} in chapter {chapter_index + 1} of .")
                scene_plan = chatcomplete("CreateScenePlan", prompt=prompt, engine=model, max_tokens=max_tokens)

                prefixed_scene_plan = f"{chapter_index + 1}:{scene_index + 1} {scene_plan}"
                chapter_scene_plans.append(prefixed_scene_plan)

            all_scene_plans.append(chapter_scene_plans)

        # flatten scene plans to list
        flat_scene_plans = [scene for chapter in all_scene_plans for scene in chapter]
        with open(f"{output_dir}/scene_plans.json", "w") as f:
            json.dump(flat_scene_plans, f)

        return flat_scene_plans, all_scene_plans

    def generate_draft(self, spec_df, model, max_tokens, num_scenes_this_run):
        """
        Generates the draft of the complete book in three formats:
        - Flat text file
        - Markdown with chapter headings and scene dividers
        - JSON with chapter headings and scene titles
        """
        chapters = spec_df['thisbookplan']
        book_text = []
        markdown_text = []
        json_structure = {"title": self.book_idea, "chapters": []}
        print(f"Total number of chapter plans: {len(spec_df['chapter_plans'])}")
        for chapter_index in range(len(spec_df['chapter_plans'])):
            # get the chapter plan from spec_df
            if chapter_index < len(spec_df['chapter_plans']):
                chapter_plan = spec_df['chapter_plans'][chapter_index]
                chapter_title = chapter_plan.split('\n')[0]
            else:
                raise IndexError("The chapter index exceeds the total number of chapters")
                chapter_title = ''
            chapter_text = []
            chapter_markdown = [f'# {chapter_title}\n\n']
            chapter_json = {"title": chapter_title, "scenes": []}
            scenes = spec_df['scene_plans'][chapter_index]
            if num_scenes_this_run < len(scenes):
                run_this_many_scenes = num_scenes_this_run
            elif num_scenes_this_run == len(scenes):
                run_this_many_scenes = len(scenes)
            else:
                logging.info(
                    f"number of scenes per chapter requested {num_scenes_this_run} was greater than the number defined in the chapter plan, so running only that number {len(scenes)}")
                run_this_many_scenes = len(scenes)

            for scene_index in range(run_this_many_scenes):
                # get the section plan from spec_df
                scene_plan = scenes[scene_index]
                logging.info(
                    f"Writing scene {scene_index} in chapter {chapter_index}")
                scene_text = self.generate_scene_text(chapter_plan, scene_plan, model, max_tokens)
                scene_title = f"Scene {scene_index + 1}"
                chapter_text.append(scene_text)
                chapter_markdown.append(f'## {scene_title}\n\n{scene_text}\n')
                chapter_json["scenes"].append({"title": scene_title, "text": scene_text})
            # Compile chapter texts
            book_text.extend(chapter_text)
            markdown_text.extend(chapter_markdown)
            json_structure["chapters"].append(chapter_json)
            joined_markdown = "\n".join(markdown_text)

        return (book_text, markdown_text, json_structure, joined_markdown)

    def save_text(self, text, filename):
        """
        Saves the given text to a file.
        """
        with open(filename, 'w') as file:
            file.write(text)

    def generate_scene_text(self, chapter_plan, scene_plan, model, max_tokens):
        """
        Generates text for a given scene using the scene plan and chapter plan.

        Parameters:
            scene_plan (dict): A dictionary containing details about the scene, including the scene's plan.
            model (str): The model identifier for generating scene text.
            max_tokens (int): The maximum number of tokens for the generation request.

        Returns:
            str: The generated text for the scene.
        """
        # Construct the prompt for generating the scene text, incorporating the scene plan and chapter context
        # print(len(scene_plan))
        prompt = f"Write the scene described by the current scene and chapter plan. Make sure to include all significant details mentioned in the plans. \n\nChapter plan: {chapter_plan}\n\nScene plan: {scene_plan}\n\nScene text:\n\n"
        str = scene_plan[:40]
        second_colon_match = re.search(":", str[str.find(":") + 1:])

        if second_colon_match:  # only proceed if a second colon was found
            second_colon_index = str.find(":") + second_colon_match.start() + 1

            # Split the string into two: before and after the second colon
            str_before_second_colon = str[:second_colon_index + 1]
            str_after_second_colon = str[second_colon_index + 1:]

            # Remove newline characters from the second part of the string
            str_after_second_colon = str_after_second_colon.replace('\n', ' ')

            # Combine the before and after strings
            scene_plan_snapshot = str_before_second_colon + str_after_second_colon

            print(f"Writing {scene_plan_snapshot} ...")
        scene_text = chatcomplete("CreateSceneText", prompt=prompt, engine=model, max_tokens=max_tokens)

        return scene_text

    def create_book_plan(self, spec_df, model, max_tokens):
        """

        Create a book plan based on the given specifications.

        Parameters:
            spec_df (pd.Series or pd.DataFrame): The specifications of the books. If spec_df is a pd.Series, it will be converted to a pd.DataFrame for processing.
            model (str): The engine model to use for generating the book plan.
            max_tokens (int): The maximum number of tokens to generate for the book plan.

        Returns:
            book_plan_response (str): The generated book plan.

        Raises:
            Exception: If there is an error generating the book plan.

        Example usage:
            spec_df = pd.read_csv('book_specifications.csv')
            model = 'gpt-3.5-turbo'
            max_tokens = 1000
            book_plan = create_book_plan(spec_df, model, max_tokens)
        """
        # Check if spec_df is a Series and convert to DataFrame for processing
        if isinstance(spec_df, pd.Series):
            spec_df = spec_df.to_frame().T

        # Ensure the DataFrame has a meaningful index (if needed) and columns
        spec_df.reset_index(drop=True, inplace=True)

        # Create the context prompt for this scene plan
        context_prompt = ""
        for idx, row in spec_df.iterrows():
            # Assuming the first column contains key specification details for each book
            book_details = '\n'.join([f"{col}: {val}" for col, val in row.items() if pd.notna(val)])
            context_prompt += book_details + "\n\n"

        # Construct the prompt for creating a book plan
        prompt = "Given the book specs provided below, create a chapter-by-chapter outline for the book.\n\n" + context_prompt.strip()
        logging.info(f"Submitting prompt: {prompt}")

        # Call the chatcomplete function to generate the book plan
        try:
            book_plan_response = chatcomplete("CreateBookPlan", prompt=prompt, engine=model, max_tokens=max_tokens)
            logging.info(book_plan_response)  # Use info to log successful responses
        except Exception as e:
            logging.error(f"Error generating book plan: {e}")
            book_plan_response = "Error generating book plan."

        return book_plan_response

    def main(self, specs_file_path, model, max_tokens, num_scenes_this_run, num_books_this_run, job_id,
             stop_after_specs, stop_after_bookplans, stop_after_chapterplans, stop_after_sceneplans, output_dir,
             select_these_rows, log_level):
        # Read book specs from the file

        specs_df = self.read_book_specs_df(specs_file_path)
        logging.info(f"Successfully read specs_df from {specs_file_path}")

        specs_df = dh.ensure_unique_short_titles(specs_df)
        # cols = [""]
        # safely_add_empty_column(specs_df, cols)

        specs_df = select_dataframe_rows_from_string(specs_df, select_these_rows)
        logging.info(f"shape of row-selected specs_df is {specs_df.shape}")
        # logging.info(f"modified specs_df: {specs_df}")
        # Process each book up to the specified number of books
        for index, book_row in specs_df.iterrows():
            # print(type(index), print(type(num_books_this_run)))
            logging.info(f"Index is {index}")
            if index > num_books_this_run:
                logging.info("breaking because index exceeds number of books")
                break

            # Fill in missing values in specs row for current book and update the df
            updated_book_row_with_specs = self.fill_missing_values_updated(book_row, model)
            specs_df = self.update_specs_df(specs_df, updated_book_row_with_specs, index)
            print(specs_df.loc[index].T)
            specs_df['model'] = model
            jsonoutputpath = cdx.save_processed_data(specs_df, job_id=job_id, output_dir=output_dir,
                                                     stage_name="specs_enhanced")
            logging.info(f"stop after specs is {stop_after_specs}")
            if stop_after_specs:
                print(f"Updated book specs table is available at {jsonoutputpath}")
                self.write_rows_to_files(specs_df, output_dir)
                continue  # Continue to the next book if stopping after specs
            else:
                logging.info(f"Updated book specs table and continuing to create book plans.")

                # Generate book plan text
                specs_df = safely_add_empty_column(specs_df, col="book_plan")
                book_plan = self.create_book_plan(book_row, model, max_tokens)
                logging.info(book_plan)
                # add bookplan to book_row
                updated_book_row_with_specs['book_plan'] = book_plan
                # print(f"specs_df before updating")
                # print(f"{specs_df.T}")
                specs_df = self.update_specs_df(specs_df, updated_book_row_with_specs, index)
                logging.info(f"specs_df with book_plan: {specs_df.T}")
                cdx.save_processed_data(specs_df, job_id=job_id, output_dir=output_dir, stage_name="book_plans")
                logging.info(f"stop_after_bookplans: {stop_after_bookplans}")
                if stop_after_bookplans:
                    logging.info("Created book plans and exiting.")
                    logging.info(f"{specs_df}")
                    logging.info(f"{specs_df.T}")
                    self.write_rows_to_files(specs_df, output_dir)
                    continue  # Continue to the next book if stopping after book pla
                else:
                    logging.info("Created book plans and continuing.")

                    # Add plans for each chapter specified in book plan

                    chapter_plans = self.create_chapter_plans(book_row, model, max_tokens)
                    updated_book_row_with_specs['chapter_plans'] = chapter_plans
                    specs_df = self.update_specs_df(specs_df, updated_book_row_with_specs, index)
                    cdx.save_processed_data(specs_df, job_id=job_id, output_dir=output_dir, stage_name='chapter_plans')
                    logging.info(f"stop_after_chapterplans: {stop_after_chapterplans}")
                    if stop_after_chapterplans:
                        logging.info("Created chapter plans and exiting.")
                        self.write_rows_to_files(specs_df, output_dir)
                        continue
                    else:
                        logging.info("Created chapter plans and continuing")

                        # now create scene plans for the entire bottom level of chapter plans

                        scene_plans = self.create_scene_plans(book_row, model, max_tokens)
                        updated_book_row_with_specs['scene_plans'] = scene_plans[1]
                        # book_row['scene_plans_nested'] = scene_plans[1]
                        specs_df = self.update_specs_df(specs_df, updated_book_row_with_specs, index)
                        cdx.save_processed_data(specs_df, job_id=job_id, output_dir=output_dir,
                                                stage_name='scene_plans')
                        logging.info(f"stop after sceneplans: {stop_after_sceneplans}")
                        if stop_after_sceneplans:
                            logging.info("Created scene plans and exiting.")
                            logging.info("Not generating draft.")
                            self.write_rows_to_files(specs_df, output_dir)
                            continue
                        else:
                            logging.info("Created scene plans and continuing.")

                            drafts = self.generate_draft(book_row, model, max_tokens)
                            updated_book_row_with_specs['drafts'] = drafts
                            specs_df = self.update_specs_df(specs_df, updated_book_row_with_specs, index)
                            cdx.save_processed_data(specs_df, job_id=job_id, output_dir=output_dir, stage_name='drafts')
                            self.write_rows_to_files(specs_df, output_dir)
                # write book_plans column to csv
            book_plans_filepath = os.path.join(output_dir, "book_plans", job_id + "_book_plans.csv")
            try:
                specs_df['book_plan'].to_csv(book_plans_filepath, index=False)
                logging.info(f"Book plan saved to {book_plans_filepath}")
            except Exception as e:
                logging.error(f"Error while saving book plans to {book_plans_filepath}")
                logging.error(traceback.print_exc())

            print(
                "Completed processing books {select_these_rows} from {specs_file_path}. Results are in {output_dir}, one folder per title, and also in the stage directories.")
        return



if __name__ == '__main__':

    argparser = argparse.ArgumentParser()

    argparser.add_argument('--generate_text', '-gt', type=bool, default=False)
    argparser.add_argument('--job_id', type=str, default=None)
    argparser.add_argument('--max_tokens', type=int, default=None)
    argparser.add_argument('--model', '-m', nargs='*', default=["groq"])

    argparser.add_argument('--num_books_this_run', '-nb', type=int, default=1)
    argparser.add_argument('--num_scenes_this_run', '-ns', type=int, default=3)
    argparser.add_argument('--specs_file_path', '-i', type=str,
                           default="resources/codexspecs/short.csv")
    argparser.add_argument('--stop_after_bookplans', '-sb', action='store_true', default=False)
    argparser.add_argument('--stop_after_chapterplans', '-sc', action='store_true', default=False)
    argparser.add_argument('--stop_after_sceneplans', '-sp', action='store_true', default=False)
    argparser.add_argument('--stop_after_specs', '-ss', action='store_true', default=False)
    argparser.add_argument("-l", "--log_level", type=str, default="INFO")

    argparser.add_argument('-o', '--output-dir', type=str, default="output/editing")
    argparser.add_argument("-r", "--select_these_rows", type=str, default="1")

    args = argparser.parse_args()

    generate_text = args.generate_text
    job_id = args.job_id
    max_tokens = args.max_tokens
    models = args.model
    num_books_this_run = args.num_books_this_run
    num_scenes_this_run = args.num_scenes_this_run
    output_dir = args.output_dir
    select_these_rows = args.select_these_rows
    specs_file_path = args.specs_file_path
    stop_after_bookplans = args.stop_after_bookplans
    stop_after_chapterplans = args.stop_after_chapterplans
    stop_after_sceneplans = args.stop_after_sceneplans
    stop_after_specs = args.stop_after_specs
    # validate parameters
    if not isinstance(num_books_this_run, int):
        raise ValueError('Invalid num_books_this_run value: %s' % num_books_this_run)
    print(args)
    if job_id is None:
        job_id = str(uuid.uuid4())[:6]

    # check if outputdir exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    set_logging_level(args.log_level)

    cdx = CodexSpecs2Book()
    dh = dh.DefoeHelpers()
    print(len(models))

    for m in models:
        result = cdx.main(output_dir=output_dir, specs_file_path=specs_file_path, model=m, max_tokens=max_tokens,
                          num_books_this_run=num_books_this_run, job_id=job_id, num_scenes_this_run=num_scenes_this_run,
                          stop_after_specs=stop_after_specs, stop_after_bookplans=stop_after_bookplans,
                          stop_after_chapterplans=stop_after_chapterplans, stop_after_sceneplans=stop_after_sceneplans,
                          select_these_rows=select_these_rows, log_level=args.log_level)
