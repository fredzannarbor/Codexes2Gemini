import json
import os
import csv
import re


def create_lsi_csv(directory):
    """
    Loops through a directory, extracts data from JSON files, and creates a CSV file.

    Args:
        directory (str): The path to the directory containing the JSON files.
    """

    csv_header = ['Non-Empty Key/Value Pairs',
                  'Lightning Source Account #', 'Metadata Contact Dictionary', 'Parent ISBN', 'ISBN or SKU',
                  'Rendition',
                  'Title', 'Publisher', 'Imprint', 'Cover/Jacket Submission Method', 'Text Block Submission Method',
                  'Contributor One', 'Contributor One Role', 'Reserved 1', 'Reserved 2', 'Reserved 3', 'Reserved 4',
                  'Custom Trim Width (inches)', 'Custom Trim Height (inches)', 'Weight(Lbs)', 'Reserved5', 'Reserved6',
                  'Reserved7', 'Reserved8', 'Marketing Image', 'Pages', 'Pub Date', 'Street Date', 'Territorial Rights',
                  'Contributor Two', 'Contributor Two Role', 'Contributor Three', 'Contributor Three Role',
                  'Edition Number',
                  'Edition Description', 'Jacket Path / Filename', 'Interior Path / Filename', 'Cover Path / Filename',
                  'Annotation / Summary', 'Reserved (Special Instructions)',
                  'LSI Special Category  (please consult LSI before using', 'Stamped Text LEFT', 'Stamped Text CENTER',
                  'Stamped Text RIGHT', 'Order Type Eligibility', 'Returnable', 'BISAC Category', 'Language Code',
                  'LSI FlexField1 (please consult LSI before using)',
                  'LSI FlexField2 (please consult LSI before using)',
                  'LSI FlexField3 (please consult LSI before using)',
                  'LSI FlexField4 (please consult LSI before using)',
                  'LSI FlexField5 (please consult LSI before using)', 'Reserved11', 'Reserved12', 'BISAC Category 2',
                  'BISAC Category 3', 'Publisher Reference ID', 'Reserved9', 'Reserved10', 'Carton Pack Quantity',
                  'Contributor One BIO', 'Contributor One Affiliations', 'Contributor One Professional Position',
                  'Contributor One Location', 'Contributor One Location Type Code', 'Contributor One Prior Work',
                  'Keywords',
                  'Thema Subject 1', 'Thema Subject 2', 'Thema Subject 3', 'Regional Subjects', 'Audience', 'Min Age',
                  'Max Age', 'Min Grade', 'Max Grade', 'Short Description', 'Table of Contents', 'Review Quote(s)',
                  '# Illustrations', 'Illustration Notes', 'Series Name', '# in Series', 'color_interior',
                  'US Suggested List Price', 'US Wholesale Discount', 'UK Suggested List Price',
                  'UK Wholesale Discount (%)',
                  'EU Suggested List Price (mode 2)', 'EU Wholesale Discount % (Mode 2)',
                  'AU Suggested List Price (mode 2)',
                  'AU Wholesale Discount % (Mode 2)', 'CA Suggested List Price (mode 2)',
                  'CA Wholesale Discount % (Mode 2)',
                  'GC Suggested List Price (mode 2)', 'GC Wholesale Discount % (Mode 2)',
                  'USBR1 Suggested List Price (mode 2)',
                  'USBR1 Wholesale Discount % (Mode 2)', 'USDE1 Suggested List Price (mode 2)',
                  'USDE1 Wholesale Discount % (Mode 2)', 'USRU1 Suggested List Price (mode 2)',
                  'USRU1 Wholesale Discount % (Mode 2)', 'USPL1 Suggested List Price (mode 2)',
                  'USPL1 Wholesale Discount % (Mode 2)', 'USCN1 Suggested List Price (mode 2)',
                  'USCN1 Wholesale Discount % (Mode 2)', 'USKR1 Suggested List Price (mode 2)',
                  'USKR1 Wholesale Discount % (Mode 2)', 'USIN1 Suggested List Price (mode 2)',
                  'USIN1 Wholesale Discount % (Mode 2)', 'USJP2 Suggested List Price(mode 2)',
                  'USJP2 Wholesale Discount % (Mode 2)', 'UAEUSD Suggested List Price (mode 2)',
                  'UAEUSD Wholesale Discount % (Mode 2)'
                  ]

    csv_data = [csv_header]  # Start with the header row

    for filename in os.listdir(directory):
        if re.match(r'^\d+\.json$', filename):
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r') as f:
                try:
                    alldata = json.load(f)

                    data = alldata["results"][0]  # Access the first element of the "results" list
                    data = json.loads(data)  # Parse the inner JSON string
                    print(data)

                    gemini_title = data.get("gemini_title", " ")
                    gemini_subtitle = data.get("gemini_subtitle", " ")
                    if gemini_title is None:
                        gemini_title = " "
                    if gemini_subtitle is None:
                        gemini_subtitle = " "
                    gemini_authors = data.get("gemini_authors", "")
                    if isinstance(gemini_authors, list):
                        gemini_authors_str = ", ".join(gemini_authors)  # Join authors with commas
                    else:
                        gemini_authors_str = gemini_authors

                    # Extract the basename without extension for Publisher Reference ID
                    publisher_ref_id = os.path.splitext(filename)[0]
                    non_empty_count = len(alldata['results'])
                    csv_row = [
                        non_empty_count, '6024045', '', '', '',
                        'POD: B&W 4 x 6 in or 152 x 102 mm Perfect Bound on White w/Matte Lam',
                        gemini_title + " " + gemini_subtitle, 'W. Frederick Zimmerman', 'Collapsar Classics', 'ftp',
                        'ftp', gemini_authors_str, 'A', '', '', '', '', '4', '6', '', '', '', '', '', '', '', '', '',
                        '', 'Fred Zimmerman', 'F', '', '', '', '', '', '', '', data.get('gemini_summary', ''), '', '',
                        '', '', '', '', 'Yes', '', 'ENG', '', '', '', '', '', '', '', '', '', publisher_ref_id, '', '',
                        '',
                        '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '',
                        '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '']
                    csv_data.append(csv_row)
                except json.JSONDecodeError:
                    print(f"Error: Invalid JSON in file: {filepath}")

    with open('output2.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(csv_data)
    print(f"Wrote file to output.csv")


if __name__ == "__main__":
    create_lsi_csv('/Users/fred/bin/nimble/Codexes2Gemini/processed_data/')
