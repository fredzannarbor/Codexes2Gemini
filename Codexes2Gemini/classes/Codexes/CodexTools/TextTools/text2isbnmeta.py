from isbnlib import goom


# text= "The book isbn 978-3-16-148410-0 is a great book"
# list = ["Cannery Row", "Maasdfasy", "Shane"]
# dict = {'ISBN-13': '9781119016779', 'Title': 'Professional Swift', 'Authors': ['Michael Dippery'], 'Publisher': 'John Wiley & Sons', 'Year': '2015', 'Language': 'en'}

def text2goom2isbnmetadict(text):
    listofisbndicts = goom(text)  # list of dicts
    return listofisbndicts


def list2goom2isbnmetadict(list):
    results = []
    for title in list:
        result = goom(title)
        results.append(result)
    return results


def isbnmetadict2list(dict):
    result = dict.values()  # def isbnmetadict2list(isbnmetadict):
    return result
