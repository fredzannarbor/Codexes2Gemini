'''
A package that contains all the classes needed to manage enhanced. metadata for
a single codex volume
Creates metadata object that holds all ADEPT values during processing
Class is an orderedDict that can be converted to a dictionary
attributes include:
AI_byline
alpha_sorted_deduped_keywords
author
Bibliographic Keyword Phrases
Book Cover Blurb
Book Description
caseinsensitivematch
catalog_description
catalog_titles
catalogs_checked
color_interior
contributing editor
contributing editor slug
Cover Illustration Designer
creationDate
creator
DALLE2_response
deduped_keywords
deduped_keywords_with_scores
description_of_annotations
ELI5
encryption
exactmatch
extractive_summary
extractive_synopsis
final page count
flags
Foreword
foreword_sig
Formal Dissent
format
fuzzymatchscore
goom terms
Hostile MAGA Perspective
imprint
index_dir
index_dir_status
ISBN
keywords
languages
llama_summary
metadata_extractableness
Methods
midjourney prompt
midjourney_response
modDate
mode
page_by_page_results
pagecount
pageheights
pageresizingneeded
pagewidths
presets_token_budget
producer
publisher
Publisher-supplied Keywords
Publisher-supplied synopsis
Recommended BISAC Categories
Recursive Summaries
Recursive Summarizer Statistics
Red Team Critique
Scientific Style
select
service context
similar titles found by isbnlib
source
spinewidth
subject
submit synopsis
subtitle
Suggested Action Items
Suggested Titles
summary response
summary sources
text_extractableness
Text2CoverImage Prompt
Text2CoverImage Prompt (Stable Diffusion)
Text2MoodImagePrompt
Text2MoodImagePrompt_response
title
TLDR
TLDR (one word)
toc
tokens in recursive_synopsis
tokens in text
trapped
vector_response
word length extracted pages

'''
import datetime
import inspect
import logging
import os
#  Copyright (c) 2023. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com

import uuid
from collections import OrderedDict


class Metadatas(OrderedDict):

    def __init__(self, *args, **kwargs):
        super().__init__()  # Initialize the OrderedDict

        class Metadatas(OrderedDict):

            def __init__(self, **kwargs):
                super().__init__()  # Initialize the OrderedDict
                self.ai_byline = kwargs.get("ai_byline", "")
                self.alpha_sorted_deduped_keywords = kwargs.get("alpha_sorted_deduped_keywords", "")
                self.author = kwargs.get("author", "")
                self.Bibliographic_Keyword_Phrases = kwargs.get("Bibliographic_Keyword_Phrases", "")
                self.Book_Cover_Blurb = kwargs.get("Book_Cover_Blurb", "")
                self.Book_Description = kwargs.get("Book_Description", "")
                self.caseinsensitivematch = kwargs.get("caseinsensitivematch", False)
                self.catalog_description = kwargs.get("catalog_description", "")
                self.catalog_titles = kwargs.get("catalog_titles", "")
                self.catalogs_checked = kwargs.get("catalogs_checked", "")
                self.color_interior = kwargs.get("color_interior", False)
                self.contributing_editor = kwargs.get("contributing_editor", "")
                self.contributing_editor_slug = kwargs.get("contributing_editor_slug", "")
                self.Cover_Illustration_Designer = kwargs.get("Cover_Illustration_Designer", "")
                self.creationDate = kwargs.get("creationDate", "")
                self.creator = kwargs.get("creator", "")
                self.DALLE2_response = kwargs.get("DALLE2_response", "")
                self.deduped_keywords = kwargs.get("deduped_keywords", "")
                self.deduped_keywords_with_scores = kwargs.get("deduped_keywords_with_scores", "")
                self.description_of_annotations = kwargs.get("description_of_annotations",
                                                             "This annotated edition illustrates the capabilities of the AI Lab for Book-Lovers to add context and ease-of-use to manuscripts. It includes publishing information; abstracts; viewpoints; learning aids; and references.")
                self.ELI5 = kwargs.get("ELI5", "")
                self.encryption = kwargs.get("encryption", False)
                self.exactmatch = kwargs.get("exactmatch", False)
                self.extractive_summary = kwargs.get("extractive_summary", "")
                self.extractive_synopsis = kwargs.get("extractive_synopsis", "")
                self.filepath = kwargs.get("filepath", "")  # path to the file that is the source of the metadata
                self.final_page_count = kwargs.get("final_page_count", "")
                self.flags = kwargs.get("flags", "ADEPT")
                self.Foreword = kwargs.get("Foreword", "")
                self.foreword_sig = kwargs.get("foreword_sig", "")
                self.Formal_Dissent = kwargs.get("Formal_Dissent", "")
                self.format = kwargs.get("format", "")
                self.fuzzymatchscore = kwargs.get("fuzzymatchscore", "")
                self.gemini_authors = kwargs.get("gemini_authors", "")
                self.gemini_title = kwargs.get("gemini_title", "")
                self.gemini_summary = kwargs.get("gemini_summary", "")
                self.generate_narrative_metadata = kwargs.get("generate_narrative_metadata", True)
                self.goom_terms = kwargs.get("goom_terms", "")
                self.Hostile_MAGA_Perspective = kwargs.get("Hostile_MAGA_Perspective", "")
                self.imprint = kwargs.get("imprint", "Nimble Books LLC")
                self.imprint_slug = kwargs.get("imprint_slug", "The AI Lab for Book-Lovers")
                self.imprint_editor = kwargs.get("imprint_editor", "~ Fred Zimmerman, Editor ~")
                self.index_dir = kwargs.get("index_dir", "index")
                self.index_dir_status = kwargs.get("index_dir_status", "")
                self.interior_filepath = kwargs.get("interior_filepath", "")
                self.ISBN = kwargs.get("ISBN", "")
                self.keywords = kwargs.get("keywords", "")
                self.languages = kwargs.get("languages", "")
                self.llama_summary = kwargs.get("llama_summary", "")
                self.metadata_extractableness = kwargs.get("metadata_extractableness", False)
                self.Methods = kwargs.get("Methods", "")
                self.midjourney_prompt = kwargs.get("midjourney_prompt", "")
                self.midjourney_response = kwargs.get("midjourney_response", "")
                self.min_age = kwargs.get("min_age", "")
                self.max_age = kwargs.get("max_age", "")
                self.max_tokens_default = kwargs.get("max_tokens_default", 150)  # default max page size for this object
                self.min_grade = kwargs.get("min_grade", "")
                self.max_grade = kwargs.get("max_grade", "")
                self.modDate = kwargs.get("modDate", "")
                self.mode = kwargs.get("mode", "assess")
                self.model_default = kwargs.get("model_default",
                                                "gpt-3.5-turbo")  # preferred default model for this object
                self.motivation = kwargs.get("motivation",
                                             "")  # 2-3 sentences from the human publisher about why this book is important enough to publish
                self.ai_motivation = kwargs.get("ai_motivation", "")  # AI-written motivation expanding on above
                self.gemini_motivation = kwargs.get("gemini_motivation", "")
                self.page_by_page_results = kwargs.get("page_by_page_results", "")
                self.pages_to_process_limit = kwargs.get("pages_to_process_limit", 10)
                self.pagecount = kwargs.get("pagecount", "")
                self.pageheights = kwargs.get("pageheights", "")
                self.pageresizingneeded = kwargs.get("pageresizingneeded", None)
                self.pagewidths = kwargs.get("pagewidths", "")
                self.pdf2text_analysis_complete = kwargs.get("pdf2text_analysis_complete", False)
                self.persist_dir = kwargs.get("persist_dir", "index")
                self.predefined_sections_file_path = kwargs.get("predefined_sections_file_path",
                                                                "resources/json/gemini_prompts/predefined_sections.json")
                self.presets_token_budget = kwargs.get("presets_token_budget", "")
                self.producer = kwargs.get("producer", "")
                self.publisher = kwargs.get("publisher", "")
                self.Publisher_supplied_Keywords = kwargs.get("Publisher_supplied_Keywords", "")
                self.Publisher_supplied_synopsis = kwargs.get("Publisher_supplied_synopsis", "")
                self.Recommended_BISAC_Categories = kwargs.get("Recommended_BISAC_Categories", "")
                self.Recursive_Summaries = kwargs.get("Recursive_Summaries", "")
                self.Recursive_Summarizer_Statistics = kwargs.get("Recursive_Summarizer_Statistics", "")
                self.Red_Team_Critique = kwargs.get("Red_Team_Critique", "")
                self.run_recursive = kwargs.get("run_recursive", False)
                self.Scientific_Style = kwargs.get("Scientific_Style", "")
                self.section_keys = kwargs.get("section_keys",
                                               ["title_page", "publishing_info", "abstracts", "mnemonics", "excerpts",
                                                "references"])
                self.select = kwargs.get("select", False)
                self.service_context = kwargs.get("service_context", "")
                self.sheetname = kwargs.get("sheetname", "")
                self.similar_titles_found_by_isbnlib = kwargs.get("similar_titles_found_by_isbnlib", "")
                self.source = kwargs.get("source", "")  # where PDF came from
                self.source_text = kwargs.get("source_text", "")  # explanation of source
                self.spinewidth = kwargs.get("spinewidth", "")  # inches
                self.subject = kwargs.get("subject", "")
                self.submit_synopsis = kwargs.get("submit_synopsis", "")
                self.subtitle = kwargs.get("subtitle", "")
                self.Suggested_Action_Items = kwargs.get("Suggested_Action_Items", "")
                self.Suggested_Titles = kwargs.get("Suggested_Titles", "")
                self.summary_response = kwargs.get("summary_response", "")
                self.summary_sources = kwargs.get("summary_sources", "")
                self.target_width = kwargs.get("target_width", 612)  # points
                self.target_height = kwargs.get("target_height", 792)  # points
                self.target_dimensions_units = kwargs.get("target_dimensions_units", "points")
                self.text_extractableness = kwargs.get("text_extractableness", False)
                self.Text2CoverImage_Prompt = kwargs.get("Text2CoverImage_Prompt", False)
                self.Text2CoverImage_Prompt_Stable_Diffusion = kwargs.get("Text2CoverImage_Prompt_Stable_Diffusion", "")
                self.Text2MoodImagePrompt = kwargs.get("Text2MoodImagePrompt", False)
                self.Text2MoodImagePrompt_response = kwargs.get("Text2MoodImagePrompt_response", False)
                self.title = kwargs.get("title", "")
                self.TLDR = kwargs.get("TLDR", "")
                self.TLDR_one_word = kwargs.get("TLDR_one_word", "")
                self.toc = kwargs.get("toc", "")
                self.tokens_in_recursive_synopsis = kwargs.get("tokens_in_recursive_synopsis", "")
                self.tokens_in_text = kwargs.get("tokens_in_text", "")
                self.trapped = kwargs.get("trapped", "")
                self.uuid = kwargs.get("uuid", str(uuid.uuid4())[0:8])
                self.shortuuid = kwargs.get("shortuuid", str(uuid.uuid4())[:4])
                self.vector_response = kwargs.get("vector_response", "")
                self.word_length_extracted_pages = kwargs.get("word_length_extracted_pages", "")
                self.current_bowker_file_path = kwargs.get("current_bowker_file_path",
                                                           "resources/sources_of_truth/bowker_active/prefix-978160888_from_bowker.csv")
                self.year = kwargs.get("year", datetime.now().year)

    # list all empty attributes

    def get_all_attributes(self):
        return self.__dict__

    def get_attribute(self, attribute):
        return getattr(self, attribute)

    def list_empty_attributes(self):
        empty_attributes = []
        for attr, value in self.__dict__.items():
            if value == "":
                empty_attributes.append(attr)
        return empty_attributes

    def list_all_attributes(self):
        return self.__dict__.keys()

    def list_all_attributes_and_values(self):
        return self.__dict__.items()

    def list_all_boolean_attributes(self):
        boolean_attributes = []
        for attr, value in self.__dict__.items():
            if value == True or value == False:
                boolean_attributes.append(attr)
        return boolean_attributes

    # set attribute value
    def set_attribute(self, attribute, value):
        setattr(self, attribute, value)

    def set(self, attribute, value):
        setattr(self, attribute, value)

    # get attribute value
    def get_attribute(self, attribute):
        return getattr(self, attribute)

    def get(self, attribute):
        return getattr(self, attribute)

    # set selected attributes to empty
    def set_selected_attributes_to_empty(self, attributes):
        for attribute in attributes:
            setattr(self, attribute, "")

    # for the metadata object, set the attributes listed as keys
    # in the custom_dict to the values listed as values in the custom_dict
    def set_attributes_to_values(self, custom_dict):
        # st.info(custom_dict)
        for key, value in custom_dict.items():
            setattr(self, key, value)

    def get_values_for_keys(self, attributes):
        # st.info(attributes)
        values = {}
        for attribute in attributes:
            values.update({attribute: getattr(self, attribute)})
        return values

    # for the metadata object, set the attributes listed as keys
    # define length method
    def __len__(self):
        return len([attr for attr in dir(self) if not callable(getattr(self, attr)) and not attr.startswith("__")])

    # close object to make room for new one
    def close(self):
        del self

    def to_dict(self):
        return self.__dict__

    def to_json(self):
        import json
        return json.dumps(self.__dict__)

    def save_at_stage(self, comments=""):
        self.stage = inspect.currentframe().f_code.co_name
        self.stage_comments = comments
        self.stage_saves = os.path.join(self.thisdoc_dir, "stage_saves")
        # mkdir stage_saves in thisdoc_dir
        if not os.path.exists(self.stage_saves):
            os.makedirs(os.path.join(self.stage_saves))
        # save json
        self.stage_save_file_path = os.path.join(self.stage_saves, self.stage + "_metadata.json")
        try:
            self.to_json(self.stage_save_file_path)
            logging.debug(f"wrote metadatas for {self.stage} to {self.stage_save_file_path}")
        except Exception as e:
            logging.error(f"failed to save metadata for self.stage to {self.stage_save_file_path}")


class SpecsDF(Metadatas):
    class SpecsDF:
        def __init__(self, title, subtitle, author, motivation, ai_motivation, source, extractive_summary,
                     publisher_supplied_synopsis, llama_summary, publisher_supplied_keywords, isbn, contributing_editor,
                     filename, flags, pdf_needs_resizing, pagewidths, pageheights, pagecount, sheetname, tokens_in_text,
                     uuid):
            self.title = title
            self.subtitle = subtitle
            self.author = author
            self.motivation = motivation
            self.ai_motivation = ai_motivation
            self.source = source
            self.extractive_summary = extractive_summary
            self.publisher_supplied_synopsis = publisher_supplied_synopsis
            self.llama_summary = llama_summary
            self.publisher_supplied_keywords = publisher_supplied_keywords
            self.isbn = isbn
            self.contributing_editor = contributing_editor
            self.filename = filename
            self.flags = flags
            self.pdf_needs_resizing = pdf_needs_resizing
            self.pagewidths = pagewidths
            self.pageheights = pageheights
            self.pagecount = pagecount
            self.sheetname = sheetname
            self.tokens_in_text = tokens_in_text
            self.uuid = uuid


class MetadataValidityChecker(Metadatas):
    '''
    functions to

    - report on number of keys present
    - report on number of values present
    - report on number of values that are:
      -- None
      -- empty strings
      -- json
      -- objects
      -- boolean
    - make sure all required keys are present at each stage
    - make sure all required values:
       -- present
       -- correct type
       -- well formed
       -- pass sanity check
    '''

    def __init__(self):

        super().__init__()
        self.valid_keys = []
        self.stages = ["initialized", "scanned", "built", "validated"]
        self.stage = self.stages[0]
        self.required_keys_by_stage = {
            "initialized": [],
            "scanned": [],
            "built": [],
            "validated": []
        }
        self.number_of_keys_that_are_None: int = 0
        self.number_of_values_that_are_None: int = 0
        self.number_of_values_that_are_empty_strings: int = 0
        self.number_of_values_that_are_boolean: int = 0
        self.number_of_values_that_are_True: int = 0
        self.number_of_values_that_are_json: int = 0
        self.number_of_values_that_are_objects: int = 0

    def list_all_boolean_attributes(self):
        boolean_attributes = []
        for attr, value in self.__dict__.items():
            if isinstance(value, bool):
                boolean_attributes.append(attr)
        return boolean_attributes
