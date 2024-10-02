from PyPDF2 import PdfFileReader, PdfFileWriter, pdf

pageold = PdfFileReader(open("app/data/evens_body3.pdf", "rb")).getPage(0)

# default PDF UserUnit is 1/72 inch

page = pdf.PageObject.createBlankPage(width=792, height=612)
scale = 1.05
offsetX = 0
offsetY = -27
page.mergeScaledTranslatedPage(pageold, scale, offsetX, offsetY, expand=False)

output = PdfFileWriter()
output.addPage(page)
output.write(open("app/data/evens_new.pdf", "wb"))
