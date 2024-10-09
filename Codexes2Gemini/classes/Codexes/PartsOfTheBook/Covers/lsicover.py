#  Copyright (c) 2024. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com

# TO create bookjson fields for back inside and front inside cover
# TODO bookjsons fields into variables
# TODO create back inside cover box

import sys
import traceback

# from app.utilities.utilities import configure_logger

try:
    import scribus
except ImportError:
    print("Unable to import the 'scribus' module. This script will only run within")
    print("the Python interpreter embedded in Scribus. Try Script->Execute Script.")
    sys.exit(1)

import os
import json
import scribus


# logger = configure_logger('root')

# import app.utilities.scribus.dont_have_template as dht


# define helper functions

def applyStyle(style, story):
    '''Try to apply style to selected text. If style doesn't exist, create it.'''

    try:

        scribus.setStyle(style, story)

    except:

        scribus.createParagraphStyle(style)

        scribus.setStyle(style, story)

    return story


def initialize(mode="fromfile", jsonfile="None"):
    bookinfo = {'BookId': 'to be assigned', 'BookTitle': "Title Goes Here", 'SubTitle': "Subtitle Goes Here",
                'Byline': 'Byline Goes Here',
                'ImageFileName': "Full path to cover image", 'InvertedColor': "White",
                'DominantColor': "Nimble Blue",
                'distributor': "LSI", 'trimsizewidth': 8.5, 'trimsizeheight': 11.0,
                'ImprintText': "Nimble Books LLC", "spinewidth": 0.25, "settings": "default",
                "BaseFont": "Skolar PE Regular", "backtext": "Back Text Goes Here", "logoletter": "N",
                "editor_byline": "~ Fred Zimmerman, Editor ~",
                "slogan": "Humans and models making reading richer, more diverse, and more surprising."}
    if mode == 'fromfile':
        bookjsonfilepath = jsonfile
        try:
            with open(bookjsonfilepath, encoding='latin1') as bookjsonfile:
                bookinfo = json.load(bookjsonfile)  # load the json file into a dictionary
        except Exception as e:
            with open(bookjsonfilepath, encoding="utf-8") as bookjsonfile:
                bookinfo = json.load(bookjsonfile)  # load the json file into a dictionary
        finally:
            print("ok")
        # hoist bookinfo dictionary
        # bookinfo = bookinfo["0"]
        bookinfo['logoletter'] = 'N'
    else:
        print("no json file specified, using defaults")
    # set up the colors
    set_custom_colors(palette="Nimble Classic")
    return bookinfo


def set_up_text_styles(BaseFont, invertedcolor="White"):
    print("entering set_up_text_styles")

    BoldFont = "Skolar PE Bold"
    ItalicFont = "Skolar PE Italic"
    BoldItalicFont = "Skolar PE Bold Italic"
    if BaseFont == "Baskerville Regular":
        BoldFont = "Baskerville Bold"
        ItalicFont = "Baskerville Italic"
        BoldItalicFont = "Baskerville Bold Italic"
    elif BaseFont == "CMU Serif Roman":
        BoldFont = "CMU Serif Bold"
        ItalicFont = "CMU Serif Italic"
        BoldItalicFont = "CMU Serif Bold Italic"
    elif BaseFont == "Constantia Regular":
        BoldFont = "Constantia Bold"
        ItalicFont = "Constantia Italic"
        BoldItalicFont = "Constantia Italic"
    elif BaseFont == "CMU Concrete Roman":
        BoldFont = "CMU Concrete Bold"
        print(BoldFont)
        ItalicFont = "CMU Concrete Italic"
        BoldItalicFont = "CMU Concrete Bold Italic"
    elif BaseFont == "Stencil":
        BoldFont = "Stencil Std Bold"
        ItalicFont = "Stencil Std Bold"
        BoldItalicFont = "Stencil Std Bold"
    elif BaseFont.endswith("Regular"):
        BoldFont = BaseFont.replace("Regular", "Bold")
        ItalicFont = BaseFont.replace("Regular", "Italic")
        BoldItalicFont = BaseFont.replace("Regular", "Bold Italic")
    else:
        print('no bold & italic fonts defined for this font')
        BoldFont = BaseFont
    print(invertedcolor)
    createStyles(BaseFont, BoldFont, invertedcolor)
    styles = scribus.getAllStyles()
    styles = str(styles)
    print(styles)
    # scribus.messageBox("Styles", styles, scribus.ICON_WARNING, scribus.BUTTON_OK)
    print("returning from set_up_text_styles")
    return styles


def createStyles(BaseFont, BoldFont, invertedcolor="White"):
    print(BaseFont, BoldFont, invertedcolor)
    # get all fonts
    fonts = scribus.getXFontNames()
    # print(fonts)

    try:
        scribus.createCharStyle(name="Title 1", font=BoldFont, fontsize=48, features='smallcaps,outline',
                                fillcolor=invertedcolor)
        scribus.createCharStyle(name="Title 1", font=BoldFont, fontsize=48, features='smallcaps,outline',
                                fillcolor=invertedcolor)

        scribus.createParagraphStyle("Title 1", linespacingmode=1,
                                     alignment=1, charstyle="Title 1")

        scribus.createCharStyle(name="SubTitle", font=BoldFont,
                                fontsize=36, features='smallcaps,outline', fillcolor=invertedcolor)
        scribus.createParagraphStyle("SubTitle", linespacingmode=1,
                                     alignment=1, charstyle="SubTitle")

        scribus.createCharStyle(name="Byline", font=BoldFont,
                                fontsize=36, features='smallcaps,outline', fillcolor=invertedcolor)
        scribus.createParagraphStyle("Byline", linespacingmode=1,
                                     alignment=1, charstyle="Byline")

        scribus.createCharStyle(name="Body Text", font=BaseFont,
                                fontsize=11, features='', fillcolor=invertedcolor)
        scribus.createParagraphStyle("Body Text", linespacingmode=1,
                                     alignment=3, charstyle="Body Text")

        scribus.createCharStyle(name="Picture Caption", font=BaseFont,
                                fontsize=10, features='', fillcolor=invertedcolor)
        scribus.createParagraphStyle("Picture Caption", linespacingmode=1,
                                     alignment=2, charstyle="Picture Caption")
        scribus.createCharStyle(name="Imprint", font=BaseFont, fontsize=18, features='smallcaps,outline',
                                fillcolor=invertedcolor)
        scribus.createParagraphStyle("Imprint", linespacingmode=1, alignment=1, charstyle="Imprint")
        scribus.createCharStyle(name="Slogan", font=BaseFont, fontsize=14, features='', fillcolor=invertedcolor)
        scribus.createParagraphStyle("Slogan", linespacingmode=1, alignment=1, charstyle="Slogan")
        scribus.createCharStyle(name="NimbleN", font="Phosphate Inline", fontsize=18, features='outline',
                                fillcolor=invertedcolor)

        scribus.createParagraphStyle("NimbleN", linespacingmode=1, alignment=1, charstyle="NimbleN")
        # scribus.createCharStyle("Duplex", font=BaseFont, fontsize=10, features='', fillcolor=invertedcolor)
        #
        # scribus.setCharStyle("Duplex")  # Select the style to modify
        #
        # # Apply properties from the image
        # scribus.setLineSpacingMode(scribus.AUTOMATIC_LINESPACING, "Duplex")
        # scribus.setTextAlignment(scribus.ALIGN_LEFT, "Duplex")
        # scribus.setLanguage("en_US", "Duplex")
        # scribus.setParStyle("Body Text", "Duplex")  # Assuming "Body Text" is your paragraph style
        # scribus.setFillShade(100.0, "Duplex")
        # scribus.setStrokeColor("Black", "Duplex")
        # scribus.setStrokeShade(100.0, "Duplex")
        # scribus.setShadowColor("None", "Duplex")
        # scribus.setShadowShade(100.0, "Duplex")

    except Exception as e:
        a = traceback.print_exc()
        scribus.messageBox("Error", f"Could not create styles: {a}", scribus.ICON_WARNING, scribus.BUTTON_OK)

    return


def add_styled_paragraphs_to_text_frame(story, paragraphs):
    for paragraph, style in paragraphs:
        # scribus.messageBox("Paragraph", str(paragraph), scribus.ICON_WARNING, scribus.BUTTON_OK)
        scribus.insertText(paragraph + "\n", -1, story)
        # Apply the paragraph style
        # Note: This assumes the cursor is at the end of the text frame
        scribus.selectText(scribus.getTextLength(story) - len(paragraph) - 1, len(paragraph), story)
        scribus.setStyle(style, story)
    return story


def set_custom_colors(palette="Nimble Classic"):
    if palette == "Nimble Classic":
        scribus.defineColor("Nimble Maroon", 0, 255, 255, 141)
        scribus.defineColor("Nimble Napoleonic Green", 187, 0, 200, 187)
        scribus.defineColor("Nimble Blue", 255, 171, 0, 159)
        scribus.defineColor("Nimble Feldgrau", 154, 102, 131, 110)
        scribus.defineColor("Nimble Metallic Gold", 113, 120, 200, 51)
        scribus.defineColor("Nimble Reference Red", 0, 255, 255, 0)
        scribus.defineColor("USAF Blue", 100, 66, 0, 44)
        scribus.defineColor("DOE Green", 50, 0, 50, 60)
        scribus.defineColor("IJN Red", 0, 0, 0, 0)
        scribus.defineColor("Union Blue", 255, 255, 0, 128)
        scribus.defineColor("Cadet Grey", 68, 0, 35, 0)
    else:
        print("did not recognize palette name")
    # for more aviation blues see https://en.wikipedia.org/wiki/Air_Force_blue
    return


def create_bylineBox(canvaswidth: object, trimsizewidth: object, trimsizeheight: object, textsafety: object,
                     invertedcolor: object, byline: object,
                     color: object, title_text_distance: object = 0.5) -> object:
    bylineBoxTopX = canvaswidth - trimsizewidth

    bylineBoxTopY = trimsizeheight - 0.25 - 3.6333
    bylineBox = scribus.createText(bylineBoxTopX, bylineBoxTopY,
                                   trimsizewidth - textsafety, 1.3333,
                                   "BylineBox")
    scribus.setTextColor(invertedcolor, bylineBox)
    scribus.setParagraphStyle("Imprint", bylineBox)
    scribus.setTextDistances(0.25, 0.25, 0.25, 0.25, bylineBox)
    scribus.setTextAlignment(2, bylineBox)
    scribus.setTextVerticalAlignment(0, bylineBox)
    scribus.setFillColor(color, bylineBox)
    return bylineBox


def create_imprint_box(canvaswidth, trimsizewidth, trimsizeheight, textsafety, invertedcolor, imprinttext,
                       editor_byline, slogan, color="Nimble Reference Red", title_text_distance=0.5):
    # create & position ImprintBox
    # imprint box goes on bottom of front cover
    imprintBoxTopX = canvaswidth - trimsizewidth

    imprintBoxTopY = trimsizeheight - 0.25 - 1.3333
    ImprintBox = scribus.createText(imprintBoxTopX, imprintBoxTopY,
                                    trimsizewidth - title_text_distance + textsafety, 1.3333,
                                    "ImprintBox")
    scribus.setTextColor(invertedcolor, ImprintBox)
    scribus.setParagraphStyle("Imprint", ImprintBox)
    scribus.setTextDistances(0.25, 0.25, 0.25, 0.25, ImprintBox)
    scribus.setTextAlignment(2, ImprintBox)
    scribus.setTextVerticalAlignment(0, ImprintBox)
    scribus.setFillColor(color, ImprintBox)
    return ImprintBox


def copy_paste_object(layer_src, object_name, layer_dst="TopLayer"):
    scribus.setActiveLayer(layer_src)
    scribus.selectObject(object_name)
    scribus.copyObject()
    scribus.setActiveLayer(layer_dst)
    scribus.pasteObject()


def main(headless, bookjsonfilepath, outputfilepath):
    """
    Main function that generates a book cover using the input parameters.

    Parameters:
    - headless (bool): Flag indicating whether the program should be run in headless mode or not.
    - bookjsonfilepath (str): The path of the bookjson file.
    - outputfilepath (str): The path where the generated book cover will be saved.

    Returns:
    - None

    Example usage:
    ```
    main(True, '/path/to/book.json', '/path/to/output.png')
    ```
    """
    print('---> entering lsicover:main ----')
    path = ('/Users/fred/bookpublishergpt/')
    os.chdir(path)

    if not scribus.haveDoc():
        # scribus.newDocument(PAPER_A4, (10, 10, 20, 20), LANDSCAPE, 7, UNIT_POINTS, PAGE_4, 3, 1)\
        PageWidth = 21
        PageHeight = 12
        scribus.newDocument((PageWidth, PageHeight), (10, 10, 10, 10), PORTRAIT, 1, UNIT_INCHES, PAGE_1, 0, 1)
    else:
        scribus.setUnit = 2
        # scribus.UNIT_INCHES = 2
        PageWidth, PageHeight = scribus.getPageSize()
        print(PageWidth, PageHeight)
        PageWidth = float(PageWidth)

    if not headless:
        bookjsonfilepath = scribus.fileDialog("Pick a bookjson file", "*.json")

    try:
        jsonbookinfo = initialize("fromfile", bookjsonfilepath)
        print(jsonbookinfo)
    except Exception as e:
        print(e)

    if not headless:
        # logging.debug(f"Book JSON File: {str(jsonbookinfo)}")
        print(f"Book JSON File: {str(jsonbookinfo)}")

    distributor = jsonbookinfo["distributor"]
    ISBN = jsonbookinfo["BookID"]
    imprinttext = jsonbookinfo["ImprintText"]
    booktitle = jsonbookinfo["BookTitle"]
    subtitle = jsonbookinfo["SubTitle"]
    byline = jsonbookinfo["Byline"]
    imagefilename = jsonbookinfo["ImageFileName"]
    invertedcolor = jsonbookinfo["InvertedColor"]
    dominantcolor = jsonbookinfo["DominantColor"]
    trimsizewidth = jsonbookinfo["trimsizewidth"]
    trimsizeheight = jsonbookinfo["trimsizeheight"]
    spinewidth = jsonbookinfo["spinewidth"]
    if isinstance(spinewidth, str):
        if spinewidth == '':
            spinewidth = scribus.valueDialog("Missing Spine Width", "Enter Spine Width as string", "0.25")
        spinewidth = float(spinewidth)
    settings = jsonbookinfo["settings"]
    basefont = jsonbookinfo["BaseFont"]
    backtext = jsonbookinfo["backtext"]
    logoletter = jsonbookinfo["logoletter"]
    # scribus.messageBox('Font Is', basefont, scribus.ICON_WARNING, scribus.BUTTON_OK)
    print("successfully read bookjson file")
    try:
        set_up_text_styles(basefont, invertedcolor)
    except Exception as e:
        print(e)

    set_custom_colors("Nimble Classic")
    if "slogan" not in jsonbookinfo:
        slogan = "Humans and models making reading richer, more diverse, and more surprising."
    if "editor_byline" not in jsonbookinfo:
        editor_byline = "~ Fred Zimmerman, Editor ~"

    coverwidth = PageWidth
    canvasheight = PageHeight

    textsafety = 0.25
    if spinewidth > 0.35:
        spinesafety = 0.0625
    else:
        spinesafety = 0.03125
    edgesafety = 0.125
    # if Case or case in settings
    if " case" in settings.lower():
        spinesafety += 0.5

    fillwidth = (trimsizewidth * 2) + spinewidth + (2 * spinesafety) + (2 * edgesafety)
    fillheight = trimsizeheight + (textsafety)

    # now positioning from TOP RIGHT!
    if PageWidth == 15:  # hacky test
        # TODO - canvaswidth isn't really canvaswidth, it is coverwidth; refactor
        coverwidth = coverwidth - 2
        leftfronttext = coverwidth - textsafety - trimsizewidth - (spinesafety / 2) - textsafety
        topLeftX = coverwidth - fillwidth
        scribus.messageBox('leftfronttext', str(leftfronttext), scribus.ICON_WARNING, scribus.BUTTON_OK)
    else:
        leftfronttext = coverwidth - textsafety - trimsizewidth - (spinesafety / 2) - textsafety
        topLeftX = coverwidth - fillwidth
    scribus.createLayer("Fill")

    # position fill box

    topLeftY = 0

    scribus.createRect(topLeftX, topLeftY, fillwidth, fillheight, "FillBox")
    scribus.setFillColor(dominantcolor, "FillBox")

    #  create front text layer
    scribus.createLayer("FrontText")

    # create image box that covers entire safe area on front cover
    textboxwidth = trimsizewidth - 0.25
    scribus.createImage(coverwidth - trimsizewidth - spinesafety, topLeftY, trimsizewidth + spinesafety,
                        trimsizeheight, "FrontCoverImage")
    if imagefilename:
        scribus.loadImage(imagefilename, "FrontCoverImage")
    else:
        # scribus.valueDialog(imagefilename, 'Full path to front cover image')

        print('no image loaded')
        # scribus.loadImage(imagefilename, "FrontCoverImage")

    btb = scribus.createText(coverwidth - trimsizewidth, 0.25, trimsizewidth - (textsafety), trimsizeheight - 0.25,
                             "FrontTextBox")
    title_text_distance = 0.5
    scribus.setTextDistances(title_text_distance, title_text_distance, title_text_distance, title_text_distance, btb)

    btb = scribus.createText(coverwidth - trimsizewidth, 0.25, trimsizewidth - (2 * textsafety), trimsizeheight - 0.25,
                             "FrontTextBox")
    if "duplex" in settings.lower():
        scribus.setTextDistances(0.25, 0.25, 0.25, 0.25, btb)
    else:
        scribus.setTextDistances(0.5, 0.5, 0.5, 0.5, btb)

    scribus.setTextColor(invertedcolor, btb)
    # Define the paragraphs and their associated styles
    paragraphs = [(booktitle, "Title 1"),
                  (subtitle, "Title 1")]

    # Add paragraphs to the frame and apply specific style
    btb = add_styled_paragraphs_to_text_frame(btb, paragraphs)

    paragraphs = []
    bylineBox = create_bylineBox(canvaswidth=coverwidth, trimsizewidth=trimsizewidth, trimsizeheight=trimsizeheight,
                                 textsafety=textsafety, invertedcolor=invertedcolor, byline=byline, color=dominantcolor,
                                 title_text_distance=0.5)
    # check if byline is a single line
    if '\n' in byline:
        byline.replace('\n', ' ')
    bylineparagraphs = [(byline, "Byline")]

    bylineBox = add_styled_paragraphs_to_text_frame(bylineBox, bylineparagraphs)

    imprintbox = create_imprint_box(canvaswidth=coverwidth, trimsizewidth=trimsizewidth, trimsizeheight=trimsizeheight,
                                    textsafety=textsafety,
                                    invertedcolor=invertedcolor, imprinttext=imprinttext, editor_byline=editor_byline,
                                    slogan=slogan, color="Nimble Reference Red", title_text_distance=0.5)

    imprintparagraphs = [(imprinttext, "Imprint"), (editor_byline, "Imprint"), (slogan, "Slogan")]

    imprintbox = add_styled_paragraphs_to_text_frame(imprintbox, imprintparagraphs)

    scribus.createLayer("BackText")
    if trimsizewidth < 6.0:
        BackTextBox = scribus.createText(coverwidth - trimsizewidth - spinewidth - trimsizewidth, textsafety,
                                         trimsizewidth - textsafety,
                                         trimsizeheight * 0.67, "BackTextBox")
    else:
        BackTextBox = scribus.createText(coverwidth - trimsizewidth - spinewidth - trimsizewidth, textsafety,
                                         trimsizewidth - textsafety,
                                         trimsizeheight * 0.67, "BackTextBox")

    columns = scribus.setColumns(2, BackTextBox)
    scribus.setColumnGap(0.1666, BackTextBox)
    if "condensed" in settings.lower():
        scribus.setTextDistances(0.25, 0.25, 0.25, 0.25, BackTextBox)
    else:
        scribus.setTextDistances(0.5, 0.5, 0.5, 0.5, BackTextBox)
    scribus.setTextColor(invertedcolor, BackTextBox)
    scribus.insertText(backtext, 0, BackTextBox)
    scribus.setParagraphStyle("Body Text", BackTextBox)
    scribus.setFontSize(11, BackTextBox)
    scribus.hyphenateText(BackTextBox)

    # create Spine layer & text
    scribus.createLayer("Spine")
    scribus.setActiveLayer("Spine")

    # target the N on the spine
    spinetop = 0
    spineleft = trimsizewidth + 0.25

    if spinewidth >= 0.25:
        spinetitle = booktitle
        SpineTop = scribus.createText(coverwidth - trimsizewidth - 0.125, 0.75, trimsizeheight - 2, spinewidth,
                                      "SpineBox")
        NimbleNBox = scribus.createText(coverwidth - trimsizewidth - 0.125 - spinewidth, trimsizeheight - 0.75,
                                        spinewidth, spinewidth, "NimbleNBox")
        # create & position SpineBox
        scribus.setTextColor(invertedcolor, SpineTop)
        scribus.insertText(spinetitle, 0, "SpineBox")
        scribus.setParagraphStyle("Title 1", SpineTop)
        scribus.setTextAlignment(0, SpineTop)
        scribus.setTextVerticalAlignment(1, SpineTop)
        scribus.setFontSize(12, SpineTop)
        scribus.setTextDistances(0.5, 0, 0, 0, SpineTop)
        scribus.rotateObject(270, SpineTop)
        #  create & position NimbleNBox
        scribus.setText(logoletter, NimbleNBox)
        scribus.setTextColor(invertedcolor, NimbleNBox)
        scribus.setFont(basefont, NimbleNBox)
        scribus.setFontSize(14, NimbleNBox)
        scribus.setTextAlignment(1, NimbleNBox)
        scribus.setTextDistances(0, 0, 0, 0, NimbleNBox)

    else:
        print("spine too narrow")
        # scribus.messageBox("Spine Too Narrow", "No spine text, spinewidth too narrow", scribus.ICON_WARNING,
        # scribus.BUTTON_OK)

    scribus.createLayer("UnderISBN")
    scribus.createLayer("ISBN")

    scribus.setActiveLayer("Background")
    # if headless:

    scribus.deselectAll()
    # Get all objects on the current page
    all_objects = scribus.getAllObjects()

    # Print the names of the objects
    for obj in all_objects:
        print(obj)
    if not headless:
        scribus.selectObject("Group4")
        scribus.sendToLayer("ISBN")
        scribus.deselectAll()
        # scribus.unGroupObject("Group8")
    scribus.createRect(coverwidth - textsafety - trimsizewidth - spinewidth - 2.25, trimsizeheight - 1.5, 2.25, 1.5,
                       "UnderISBN")
    scribus.setFillColor("White", "UnderISBN")
    scribus.setLineColor(dominantcolor, "UnderISBN")
    # scribus.selectObject("Group8")
    # scribus.sendToLayer("UnderISBN")
    scribus.selectObject("UnderISBN")
    scribus.sendToLayer("UnderISBN")
    try:
        scribus.saveDocAs(outputfilepath)
        print(f"Saved draft cover SLA to {outputfilepath}")
    except Exception as e:
        print(f'could not save file: {e}')

    if "duplex" in settings.lower():
        scribus.gotoPage(2)
        #
        scribus.setActiveLayer("Fill")
        duplex_fill_width = trimsizewidth + spinesafety + edgesafety
        scribus.createRect(topLeftX - 4, topLeftY, duplex_fill_width, fillheight, "FillBoxInteriorLeft")
        scribus.createRect(topLeftX + 2, topLeftY, duplex_fill_width, fillheight, "FillBoxInteriorRight")
        scribus.setFillColor(dominantcolor, "FillBoxInteriorLeft")
        scribus.setFillColor(dominantcolor, "FillBoxInteriorRight")

        scribus.setActiveLayer("FrontText")
        # Create front inside cover text layer
        front_inside_left_cover = scribus.createText(coverwidth - trimsizewidth, 0.25, duplex_fill_width,
                                                     trimsizeheight - 0.25, "front_inside_left_cover")
        front_inside_right_cover = scribus.createText(coverwidth - trimsizewidth, 0.25, duplex_fill_width,
                                                      trimsizeheight - 0.25, "front_inside_right_cover")

        if "condensed" in settings.lower():
            title_text_distance = 0.25
        else:
            title_text_distance = 0.5

        scribus.setTextDistances(title_text_distance, title_text_distance, title_text_distance, title_text_distance,
                                 "front_inside_right_cover")
        scribus.setTextDistances(title_text_distance, title_text_distance, title_text_distance, title_text_distance,
                                 "front_inside_left_cover")

        # Set text color
        scribus.setTextColor(invertedcolor, front_inside_left_cover)
        scribus.setTextColor(invertedcolor, front_inside_right_cover)

        # Define the paragraphs and their associated styles
        paragraphs_left = [("About this Book", "SubTitle"),
                           (
                           "Collapsar Condensed Editions introduce readers to the classics into an engaging and convenient new format without compromising on quality.\n\nEach pocket-sized paperback includes a carefully justified selection of the most important passages in their original work; specially written 'condensed matter' that captures the spirit and language of the original; essays placing the work in its historic context and explaining why it is important today; and abstracts, learning aids, glossaries, and timelines. \n\nOur meticulous approach ensures every word serves a purpose. We bring the past alive in a way that's both engaging and insightful, leaving you with a deeper understanding of the topic and a desire to explore more.\n\nFred Zimmerman, Publisher",
                           "Body Text")]

        paragraphs_right = [("More Like This", "SubTitle")]


        # Add paragraphs to the frame and apply specific style
        front_inside_left_cover = add_styled_paragraphs_to_text_frame(front_inside_left_cover, paragraphs_left)
        front_inside_right_cover = add_styled_paragraphs_to_text_frame(front_inside_right_cover, paragraphs_right)

    save_sla_to_pdf(ISBN, outputfilepath)

    return


def save_sla_to_pdf(ISBN, outputfilepath):
    pdf = scribus.PDFfile()
    pdf.file = outputfilepath_pdf
    pdf.quality = 1
    pdf.fontEmbedding = 0
    pdf.version = 13
    pdf.pages = [1]
    basefilename = os.path.basename(outputfilepath)
    basefilename_split = os.path.splitext(basefilename)[0]
    print(f"basefilename_split: {basefilename_split}")
    dirpath = os.path.dirname(outputfilepath)
    outputfilepath_ISBN = os.path.join(dirpath, ISBN + '_cover_' + basefilename_split[:23] + '.pdf')
    print(outputfilepath_ISBN)
    pdf.file = outputfilepath_ISBN
    try:
        pdf.save()
        scribus.messageBox("Save Successful", f"saved to outputfilepath_ISBN: {outputfilepath_ISBN}",
                           scribus.ICON_WARNING, scribus.BUTTON_OK)
    except Exception as e:
        traceback.print_exc()
        exit()


if __name__ == "__main__":

    import argparse

    argparser = argparse.ArgumentParser(description='Parser for Scribus Python app.')
    argparser.add_argument("-i", "--bookjson", required=False, help="Path to bookjson file",
                           default="test/bookjson/test.json")
    argparser.add_argument("-o", "--outputfilepath", required=False, help="Path to write output file",
                           default="output/bookcovers/test.sla")
    # add --headless as true if present
    argparser.add_argument("--headless", action='store_true',
                           help="Run the script in headless mode")  # Adding help text is optional but recommended

    args = argparser.parse_args()

    bookjsonfilepath = args.bookjson
    outputfilepath = args.outputfilepath

    outputfilepath_pdf = os.path.splitext(outputfilepath)[0] + '.pdf'
    # now format ISBN
    headless = args.headless

    main(headless, bookjsonfilepath, outputfilepath)

