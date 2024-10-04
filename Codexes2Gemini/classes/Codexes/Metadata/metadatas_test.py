import os
from Codexes2Gemini.classes.Codexes.Metadata.Metadatas import Metadatas
from Codexes2Gemini.classes.Codexes.Distributors.LSI.create_LSI_ACS_spreadsheet import create_LSI_ACS_spreadsheet


def create_test_metadata():
    """Creates a complete and valid Metadatas object for testing."""
    metadata = Metadatas()
    metadata.ISBN = "978-1-234-56789-0"
    metadata.title = "Test Book Title"
    metadata.author = "Test Author"
    metadata['final page count'] = 200
    metadata['publication date'] = "2024-03-05"  # Example date
    metadata['Annotation / Summary'] = "This is a test book summary."
    metadata['keywords'] = ["test", "book", "keywords"]
    metadata['min_age'] = 18
    metadata['max_age'] = 35
    metadata['min_grade'] = ''
    metadata['max_grade'] = ''
    metadata['TLDR'] = "Test book TLDR."
    metadata['toc'] = "Chapter 1\nChapter 2\nChapter 3"
    metadata['color_interior'] = True
    metadata['recommended price'] = 19.99
    metadata['jacket_filepath'] = "path/to/jacket.jpg"
    metadata['interior_filepath'] = "path/to/interior.pdf"
    metadata['cover_filepath'] = "path/to/cover.pdf"
    metadata['Bibliographic_Keyword_Phrases'] = "# Bibliographic Key Phrases\n\nkeyword 1; keyword 2; keyword 3"
    return metadata


def main():
    """Creates a test LSI ACS spreadsheet and saves it as a CSV file."""
    metadata = create_test_metadata()
    lsi_df = create_LSI_ACS_spreadsheet(metadata)

    # Save the DataFrame to a CSV file
    output_dir = "test_output"
    os.makedirs(output_dir, exist_ok=True)
    output_csv_path = os.path.join(output_dir, "test_lsi_acs.csv")
    lsi_df.to_csv(output_csv_path, index=False)
    print(f"LSI ACS spreadsheet saved to: {output_csv_path}")


if __name__ == "__main__":
    main()
