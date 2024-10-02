#  Copyright (c) 2024. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com
import os

import fitz


def add_footer(pdf_path, output_path):
    doc = fitz.open(pdf_path)
    for i in range(len(doc)):  # for each page in the document
        page = doc[i]
        footer_text = f"Body-{i + 1}"
        # print(page.rect.height)
        # print(page.rect.width)
        footer_position = page.rect.height - 36
        footer_position_bottom = page.rect.height - 12  # convert inches to points
        footer_position_top = footer_position_bottom - 36  # convert inches to points

        rect = fitz.Rect(0, footer_position_top, page.rect.width, footer_position_bottom)

        page.insert_textbox(rect, footer_text, align=1)  # align=1 for center aligned

    # Make output directories if they do not exist
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # Save the PDF
    doc.save(output_path)


if __name__ == "__main__":
    pdf_path = ("working/Logan3pp.pdf")
    output_path = "output.pdf"
    add_footer(pdf_path, output_path)
