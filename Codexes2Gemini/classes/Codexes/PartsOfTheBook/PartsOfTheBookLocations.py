'''
Parts of the book locations
A subclass of ADEPT.PartsOfTheBook
Locations of parts include:
    frontmatter
    body
    backmatter
    cover
Cover locations include:
    front binding
    back binding
    spine binding
    dust jacket front cover
    dust jacket back cover
    dust jacket spine
Special locations include:
    gilt edged page labels
    attached bookmarks
    attached ribbons
    boxes
    bookplates
    inserts
    foldouts


'''
class PartsOfTheBookOrder:
    def __init__(self):
        self = OrderedDict()

    def default_order():
