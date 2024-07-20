# Copyright (c) 2023. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com
import os
from random import choice, sample, randint

import pandas as pd
import streamlit as st
import textstat
from faker import Faker

from Codexes2Gemini.classes.Utilities.gpt3complete import chatcomplete


class ReaderPanels:

    # creating & managing  ReaderPanels
    def __init__(self, number_of_readers=5, demographic_profile_dict=None):
        self.readers = []
        self.number_of_readers = number_of_readers
        self.demographic_profile_dict = demographic_profile_dict

    def create_reader_panel(self, reader_panel_name, n, default_genres, default_tastes, default_genders,
                            default_ages, default_faker_locale):
        readers_df = pd.DataFrame()

        faker = Faker(default_faker_locale)
        for row in range(n):
            name = faker.name()
            genre = sample(default_genres, 3)
            taste = choice(default_tastes)
            gender = choice(default_genders)
            ages = choice(default_ages)
            # 80 percent chance of having read a book in the last twelve months
            books_read_in_last_twelve_months = randint(0, 9)
            if books_read_in_last_twelve_months >= 8:
                books_read_in_last_twelve_months = 0
            preferred_reading_level = choice([8, 10, 10, 11, 11, 12, 13])
            row = {'name': name, 'genre': genre, 'taste': taste, 'gender': gender, 'age': ages,
                   'books_read_in_last_twelve_months': books_read_in_last_twelve_months,
                   'preferred_reading_level': preferred_reading_level}
            # add dictionary to dataframe as a new row
            row_df = pd.DataFrame([row])
            # concatenate the row dataframe to the readers dataframe
            # do not add the index to the readers dataframe
            readers_df = pd.concat([readers_df, row_df], ignore_index=True)
        if not os.path.exists('resources/reader_panels'):
            os.makedirs('resources/reader_panels')
        if os.path.exists(f'resources/reader_panels/{reader_panel_name}.csv'):
            reader_panel_name = f'{reader_panel_name}_{randint(1, 100)}'
        readers_df.to_csv(f'resources/reader_panels/{reader_panel_name}.csv')
        return readers_df

    def add_LLM_bios_to_reader_panel_rows(self, reader_panel):
        # add LLM row with bio
        reader_panel['bio'] = reader_panel.apply(lambda row: self.get_LLM_bio(row), axis=1)
        return reader_panel

    def get_LLM_bio(self, row, seed=None):
        # turn row into a prompt string block
        prompt = f"Name: {row['name']}\n"
        prompt += f"Age: {row['age']}\n"
        prompt += f"Gender: {row['gender']}\n"
        prompt += f"Genre: {row['genre']}\n"
        prompt += f"Taste: {row['taste']}\n"
        prompt += f"Books read in last twelve months: {row['books_read_in_last_twelve_months']}\n"
        prompt += f"Preferred reading level: {row['preferred_reading_level']}\n"

        if seed:
            prompt += f"Seed: {seed}\n"
        response_text = chatcomplete("CreateReaderBio", prompt, "gpt-3.5-turbo")
        result = response_text
        bio = result
        return bio

    def get_saved_reader_panel(self, reader_panel_name, reader_panel_directory='resources/reader_panels'):
        reader_panel_filepath = f'{reader_panel_directory}/{reader_panel_name}.csv'
        # st.info(f'Loading reader panel from {reader_panel_filepath}')
        saved_panel_df = pd.read_csv(reader_panel_filepath)
        return saved_panel_df

    def get_list_of_reader_panels(self, reader_panel_directory='resources/reader_panels'):
        reader_panels = os.listdir(reader_panel_directory)
        # remove subdirectories
        reader_panels = [panel for panel in reader_panels if '.' in panel]
        return reader_panels

    def collect_evaluations(self, reader_panel):
        # collect evaluations from reader panel
        evaluations = []
        for reader in reader_panel:
            evaluations.append(reader.current_chunk)
        return evaluations

    def summarize_evaluations(self, evaluations):
        # summarize evaluations
        summary = {}
        for evaluation in evaluations:
            if evaluation in summary:
                summary[evaluation] += 1
            else:
                summary[evaluation] = 1
        return summary

    def positive_triggers(self, reader):
        positive_trigger_conditions = [
            # textstat.flesch_reading_ease(reader.current_chunk) > 60,
            str(reader.tastes) in reader.current_chunk]
        return any(positive_trigger_conditions)

    def negative_triggers(self, reader):
        # a reader experiences a chunk as a negative experience if it meets one or more of the following conditions:
        # 1. the chunk is very difficult to read
        # 2. the chunk is very boring
        # 3. the chunk uses hateful, biased, or obscene language
        negative_trigger_conditions = [
            textstat.flesch_reading_ease(reader.current_chunk) < 30,
            str(reader.tastes) not in reader.current_chunk]
        return any(negative_trigger_conditions)

    # def add_reader(self, reader_id, genres, tastes, gender, age, name):
    #     reader = Reader(reader_id, genres, tastes, gender, age, name)
    #     self.readers.append(reader)

    def remove_reader(self, reader_id):
        for reader in self.readers:
            if reader.reader_id == reader_id:
                self.readers.remove(reader)
                break

    def pick_a_random_reader(self, reader_panel_name, reader_panel_directory='resources/reader_panels',
                             randomness_strategy=None):

        if randomness_strategy is None:
            reader_panel = self.get_saved_reader_panel(reader_panel_name, reader_panel_directory)
            # pick a random row from reader panel df
            reader = reader_panel.sample(n=1)
        return reader

    def remove_unwanted_items(self, available_reader_panels, unwanted='.DS_Store'):
        #st.info(f'Removing {unwanted} from list of available reader panels.')
        if unwanted in available_reader_panels:
            available_reader_panels.remove(unwanted)
        return available_reader_panels

    def strip_file_extension(self, panels_list, extension_length=4):
        return [panel[:-extension_length] for panel in panels_list]

    def load_reader_panels(self):
        available_reader_panels = self.get_list_of_reader_panels()
        available_reader_panels = self.remove_unwanted_items(available_reader_panels)
        available_reader_panels = self.strip_file_extension(available_reader_panels)
        return available_reader_panels

    def display_panel(self, selected_panel, n_readers):
        panel_df = self.get_saved_reader_panel(selected_panel)
        if "Random" in selected_panel:
            panel_df = selected_panel.sample(n=n_readers)
            st.caption(f'Sampled {n_readers} Readers from pool.')
        st.dataframe(panel_df)
        st.caption('Browse dataframe to explore Reader profiles.')

    def user_interface(self):
        available_reader_panels = self.load_reader_panels()

        selected_panel = st.selectbox("Available Panels",
                                      available_reader_panels,
                                      key="arp", index=0)
        button = st.button("Load Panel")
        panel_df = self.get_saved_reader_panel(selected_panel)
        if button:
            self.display_panel(selected_panel, 5)
            panel_df = self.load_reader_panels()
            return panel_df
        return panel_df

    def add_random_readers_to_panel(self, source_reader_panel_name="AllReaders",
                                    source_reader_panel_directory_name="resources/reader_panels",
                                    target_reader_panel_name="SelectedPanel",
                                    target_reader_panel_directory='resources/reader_panels', n=1):
        # get source reader panel
        source_reader_panel = self.get_saved_reader_panel(source_reader_panel_name, source_reader_panel_directory_name)
        target_reader_panel = self.get_saved_reader_panel(target_reader_panel_name, target_reader_panel_directory)
        random_readers = source_reader_panel.sample(n=n)
        # add random readers to target reader panel
        target_reader_panel_df = pd.concat([target_reader_panel, random_readers], axis=0, ignore_index=True)
        target_reader_panel_df.to_csv(f'{target_reader_panel_directory}/{target_reader_panel_name}.csv')
        return target_reader_panel_df
