#  Copyright (c) 2023. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com


# import a library to detect ethnic slurs


class Reader:

    def __init__(self):
        self.default_genres = ['fiction', 'nonfiction', 'poetry', 'drama', 'comedy', 'tragedy', 'satire', 'romance',
                               'adventure']
        self.default_genders = ['male', 'female']
        self.default_ages = ['child', 'teenager', 'young adult', 'adult', 'elder']
        self.default_tastes = ['sophisticated', 'lowbrow', 'middlebrow', 'highbrow', 'pop', 'cult', 'classic']
        self.default_faker_locale = None
        self.name = "J. Doe"
        self.likes = ['likes']
        self.dislikes = ['dislikes']
        self.default_number_books_read_in_last_twelve_months = 1
        self.median_preferred_reading_level = 11.0
        self.demographic_attributes = {"role": "assistant", "content": "Female, 25-34, income 65,000, Minnesota."}
        self.global_reading_preferences = "Enjoys literary fiction, poetry, and adventure narratives."
        self.on_page_reading_preferences = "Likes: classical quotations; complex sentences; allusions to mythology; references to the natural world; and the use of metaphor. Dislikes: typos, sexism."
        self.immediate_goal = "Relaxation and entertainment."
        self.long_term_goals = "To become a better writer."
        self.current_chunk_no = 0
        self.current_chunk = None
        self.current_work = None
        self.current_page_no = None
        self.current_page_text = "A page of text."
        self.running_posneg = 0
        self.on_page_assignments = [
            {"role": "assistant",
             "content": "Does the experience of reading this page fit with the immediate goal of the reader persona? You MUST answer with only the words  'true', 'false', or 'unsure'."},
            {"role": "assistant",
             "content": "Do you see any spelling errors on this page? You MUST answer with ONLY the words 'true' or 'false'."},
            {"role": "assistant",
             "content": "Your gut reaction to this page in ten words or less. Stay in character with the demographic attributes of the reader persona."},
            {"role": "assistant",
             "content": "Identify the most noteworthy passage of under 50 words on this page and provide it as an exact quotation."},
            {"role": "assistant",
             "content": "Classify the text of this page as offensive or neutral. You MUST answer with only the words 'offensive' or 'neutral'."}
        ]
        self.global_assignments = [
            {"role": "assistant", "content": "Rate this book on a scale of 1 to 5, with 5 being the best."}
        ]
        self.system_batch_command = '{"role": "system", "content": "Complete every element of the array. Reply with an array of all completions."}'
        self.system_yourjob = {"role": "system",
                               "content": "Your job is to simulate and report upon the experience that a particular human person would have when first reading a page of text."}

        # Example usage

    manuscript = '''
        Once upon a time, in a land far, far away... a princess was born.  
         was beautiful, tall, and intelligent. Her cat was furry. Obstinate intransigence transmogrified the princess into a amphibian cryptid.
    '''

# Define attributes for the panel of readers
