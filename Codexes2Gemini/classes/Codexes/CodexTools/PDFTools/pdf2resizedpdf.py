import argparse
import logging
import traceback
from pathlib import Path

import fitz


def two_step_landscape_to_portrait(pdf_file, output_file, width, height):
    """
    Resize unevenly sized pages to a specified width and height, ensuring that landscape
    pages are properly shrunk to fit within portrait dimensions.
    """
    pdf_file = Path(pdf_file)
    output_file = Path(output_file)
    src = fitz.Document(str(pdf_file))  # Ensure path is converted to string
    doc = fitz.Document()
    all_scales_found = [1]
    for ipage in src:
        if ipage.number % 40 == 0:
            logging.info(f"analyzing page number {ipage.number}")
        rotation = ipage.rotation
        # print(ipage.rect.width, width)
        # print(ipage.rect.height, height)
        # print(rotation)
        # Check the orientation of the page and decide on scaling
        if rotation in {90, 270}:
            # Calculate scale to fit the landscape page into a square page
            # whose dimensions are width x width
            scale = width / max(ipage.rect.width, ipage.rect.height)
            all_scales_found.append(scale)

            # print(f"min scale with fudge factor for margins is is {scale:.1%}")
            mat = fitz.Matrix(scale, scale).prerotate(0)
            pix = ipage.get_pixmap(matrix=mat, alpha=False)
            # print(f"pix dimensions are {pix.width}x{pix.height}")
            # Insert the pixmap into the new page

            # Create a new page
            new_page = doc.new_page(-1, width=612, height=792)
            fudge_factor = 0.93
            new_page.insert_image(fitz.Rect(0, 0, width * fudge_factor, width), pixmap=pix)
        else:
            # No scaling needed, just apply rotation if it's not a standard portrait
            # mat = fitz.Matrix(1.0, 1.0).prerotate(rotation)
            # print(f"no scaling needed, just ensuring rotation is to 0 degrees on  {ipage.number}")
            # copy current page to new doc

            copy_page_to_custom_size(src, doc, ipage.number, 612, 792)
    print("all resizing scales found: " + ", ".join(f"{i:.1%}" for i in sorted(list(set(all_scales_found)))))
    src.close()

    try:
        doc.save(str(output_file))
        doc.close()
        print(f"saved {output_file}")
    except Exception as e:
        traceback.print_exc()
        print("failed to save target document")


def copy_page_to_custom_size(src, doc, page_number, new_width, new_height):
    """
    Copies a specific page from the source document (src) to a new custom-sized page in the destination document (doc).

    :param src: The source Document object.
    :param doc: The destination Document object.
    :param page_number: The page number (zero-based) to copy from the source document.
    :param new_width: The width of the new custom-sized page in points.
    :param new_height: The height of the new custom-sized page in points.
    """
    # Add a new page to the destination document with the specified size
    new_page = doc.new_page(-1, width=new_width, height=new_height)

    # Ensure the page_number is within the range of the source document
    if page_number < 0 or page_number >= len(src):
        print(f"Page number {page_number} is out of range for the source document.")
        return

    # Copy the content of the specified page from the source document to the new page
    src_page = src.load_page(page_number)  # Load the specific page from the source document
    new_page.show_pdf_page(new_page.rect, src, src_page.number)  # Render the source page onto the new page


def calculate_target_dimensions(metadatas, target_width, target_height):
    target_width = target_height = None
    if metadatas.get_attribute('pagewidths') == target_width and metadatas.get_attribute(
            'pageheights') == target_height:
        metadatas.set_attribute('pagewidths', target_width)
        metadatas.set_attribute('pageheights', target_height)
    return metadatas


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--pdf_file', help='PDF file to resize',
                        default='working/manhattan_project/MDH-B1V04C12-General-Aux-National_Bureau_of_Standards.pdf')
    parser.add_argument('-o', '--output_file', help='Output file', default='test/output_resized.pdf')
    parser.add_argument('-w', '--width', default=612, type=float, help="target width")
    parser.add_argument('-ht', '--height', default=792, type=float, help="target height")
    args = parser.parse_args()
    pdf_file = args.pdf_file
    output_file = args.output_file
    width = args.width
    height = args.height

    # simple_rotate_landscapey_pages(pdf_file, output_file, width, height)
    # simple_rotate_landscape_pages(pdf_file, output_file, width, height)
    two_step_landscape_to_portrait(pdf_file, output_file, width, height)
