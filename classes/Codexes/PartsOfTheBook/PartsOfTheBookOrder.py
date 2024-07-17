"""
Subclass of ADEPT.PartsOfTheBook
controls order in which parts of the book are assembled in the final published book
order follows Chicago Manual of Style 17th edition unless overridden
attributes:
- default order dict
- override order dict (just override the parts that are different)
"""
class PartsOfTheBookOrder:
    self = OrderedDict()
    self.set_default_order()
    self.default_order = {}