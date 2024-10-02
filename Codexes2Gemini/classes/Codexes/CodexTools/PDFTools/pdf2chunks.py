# -*- coding: utf-8 -*-


from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer

pdf = "app/userdocs/3/Cantaloupe_Symbolism_check.pdf"


def chunkizepdf(pdf):
    print('chunking pdf', pdf)

    chunk_no = 0
    data = []
    prompt = []
    chunk_list = []
    chunk = ''
    d = {}
    page_so_far = ""
    words_in_chunk = 0

    for page_layout in extract_pages(pdf):
        print('---page---')
        for element in page_layout:

            if isinstance(element, LTTextContainer):
                # print(element.get_text())
                text = element.get_text()
                page_so_far = page_so_far + text
                chunk = page_so_far

        # print(chunk)
        chunk_list.append(chunk)
        page_so_far = ""
    print(chunk_list[60])
    return chunk_list


if __name__ == "__main__":
    chunkize(pdf)
