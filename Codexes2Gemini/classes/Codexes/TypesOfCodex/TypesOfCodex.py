#  Copyright (c) 2023. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com
from classes.Codexes.Metadata.Metadatas import Metadatas


# master class is Codexes
# subclass is Metadatas
# subclass is TypesOfCodex

class TypesOfCodex(Metadatas):

    def __init__(self, *args, **kwargs):
        self.title = "Types of Codex"
        self.description = "A codex is a book constructed of a number of sheets of paper, vellum, papyrus, or similar materials. The term is now usually only used of manuscript books, with hand-written contents, but describes the format that is now near-universal for printed books in the Western world.  This class is for all the different types of codexes that exist, specifically including physical, digital, and generative-AU codexes."
        self.media_types = ["Physical", "Digital", "Generative-AI"]
        self.binding_types = ["Hardcover", "Paperback", "Spiral", "Stapled", "Perfect", "Saddle-stitch"]
        self.cover_types = ["Soft", "Hard", "Dust Jacket", "Linen", "Leather", "Plastic"]
        self.page_types = ["Lined", "Blank", "Grid", "Dotted", "Numbered", "Unnumbered"]
