# Metadatas checklist

'''
A package that contains all the classes needed to manage enhanced. metadata for
a single codex volume
Creates metadata object that holds all ADEPT values during processing
Class is an orderedDict that can be converted to a dictionary
'''

self.ai_byline = ""
self.alpha_sorted_deduped_keywords = ""
~~self.author = ""~~
self.Bibliographic_Keyword_Phrases = ""
self.Book_Cover_Blurb = ""
self.Book_Description = ""
self.caseinsensitivematch = False
self.catalog_description = ""
self.catalog_titles = ""
self.catalogs_checked = ""
self.color_interior = False
self.contributing_editor = ""
self.contributing_editor_slug = ""
self.Cover_Illustration_Designer = ""
self.creationDate = ""
self.creator = ""
self.DALLE2_response = ""
self.deduped_keywords = ""
self.deduped_keywords_with_scores = ""
self.description_of_annotations = "This annotated edition illustrates the capabilities of the AI Lab for Book-Lovers to
add context and ease-of-use to manuscripts. It includes publishing information; abstracts; viewpoints; learning aids;
and references."
self.ELI5 = ""
self.encryption = False
self.exactmatch = False
self.extractive_summary = ""
self.extractive_synopsis = ""
self.filepath = "" # path to the file that is the source of the metadata
self.final_page_count = ""
self.flags = "ADEPT"
self.Foreword = ""
self.foreword_sig = ""
self.Formal_Dissent = ""
self.format = ""
self.fuzzymatchscore = ""
self.gemini_authors = ""
self.gemini_title = ""
self.gemini_summary = ""
self.generate_narrative_metadata = True
self.goom_terms = ""
self.Hostile_MAGA_Perspective = ""
self.imprint = "Nimble Books LLC"
self.imprint_slug = "The AI Lab for Book-Lovers"
self.imprint_editor = "~ Fred Zimmerman, Editor ~"
self.index_dir = "index"
self.index_dir_status = ""
self.interior_filepath = ""
~~self.ISBN = ""~~
self.keywords = ""
self.languages = ""
self.llama_summary = ""
self.metadata_extractableness = False
self.Methods = ""
self.midjourney_prompt = ""
self.midjourney_response = ""
self.min_age = ""
self.max_age = ""
self.max_tokens_default = 150 # default max page size for this object
self.min_grade = ""
self.max_grade = ""
self.modDate = ""
self.mode = "assess"
self.model_default = "gpt-3.5-turbo"  # preferred default model for this object
self.motivation = ""  # 2-3 sentences from the human publisher about why this book is important enough to publish
self.ai_motivation = ""  # AI-written motivation expanding on above
self.gemini_motivation = ""
self.page_by_page_results = ""
self.pages_to_process_limit = 10
self.pagecount = ""
self.pageheights = ""
self.pageresizingneeded = None
self.pagewidths = ""
self.pdf2text_analysis_complete = False
self.persist_dir = "index"
self.predefined_sections_file_path = "resources/json/gemini_prompts/predefined_sections.json"
self.presets_token_budget = ""
self.producer = ""
self.publisher = ""
self.Publisher_supplied_Keywords = ""
self.Publisher_supplied_synopsis = ""
self.Recommended_BISAC_Categories = ""
self.Recursive_Summaries = ""
self.Recursive_Summarizer_Statistics = ""
self.Red_Team_Critique = ""
self.run_recursive = False
self.Scientific_Style = ""
self.section_keys = ["title_page", "publishing_info", "abstracts", "mnemonics", "excerpts", "references"]
self.select = False
self.service_context = ""
self.sheetname = ""
self.similar_titles_found_by_isbnlib = ""
self.source = ""  # where PDF came from
self.source_text = ""  # explanation of source
self.spinewidth = ""  # inches
self.subject = ""
self.submit_synopsis = ""
self.subtitle = ""
self.Suggested_Action_Items = ""
self.Suggested_Titles = ""
self.summary_response = ""
self.summary_sources = ""
self.target_width = 612 # points
self.target_height = 792 # points
self.target_dimensions_units = "points"
self.text_extractableness = False
self.Text2CoverImage_Prompt = False
self.Text2CoverImage_Prompt_Stable_Diffusion = ""
self.Text2MoodImagePrompt = False
self.Text2MoodImagePrompt_response = False
~~self.title = ""~~
self.TLDR = ""
self.TLDR_one_word = ""
self.toc = ""
self.tokens_in_recursive_synopsis = ""
self.tokens_in_text = ""
self.trapped = ""
self.uuid = str(uuid.uuid4())[0:8]
self.shortuuid = str(uuid.uuid4())[:4]
self.vector_response = ""
self.word_length_extracted_pages = ""
self.current_bowker_file_path = "resources/sources_of_truth/bowker_active/prefix-978160888_from_bowker.csv"

# self.year = datetime.now().year


