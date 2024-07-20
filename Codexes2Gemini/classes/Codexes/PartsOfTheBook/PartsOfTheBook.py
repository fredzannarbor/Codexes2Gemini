'''
This class holds all the parts of the book.
Each part of the book is a separate object.
Each part is a dictionary that contains various values.
Each dictionary contains a key called 'type' that indicates the type of part.
Types of parts include:
    text
    image
    table

Each part of the book has a dictionary that includes at a minimum:
    type of part
    content (text, image, or table)
    usual location (frontmatter, body, backmatter, cover)
    required style (font, size, color, etc.) -- only if the part *must* be presented in this style
'''
class BookPart:
    def __init__(self, part_type, content, location, required_style):
        self.part_type = part_type
        self.content = content
        self.location = location
        self.required_style = required_style
        self.name = ""
        self.description = ""

