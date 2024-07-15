#  Copyright (c) 2023. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com

# master class is Codexes
# subclass is Metadatas
# subclass is TypesOfCodex
# subclass is PictureBook

class PictureBook(TypesOfCodex):

    def __init__(self, *args, **kwargs):
        self.title = "Picture Book"
        self.description = "A picture book is a book, typically for children, in which the illustrations are as important as—or more important than—the words in telling the story. Picture books have traditionally been 32 pages long, although Little Golden Books are 24 pages."
