import csv
import os
import random

from Codexes2Gemini.classes.Codexes.Builders import BuildLauncher
from Codexes2Gemini.classes.Codexes.Builders import Codexes2Parts

# Configuration
N = 3  # Number of random documents to process
METADATA_FILE = "/Users/fred/bin/Codexes2Gemini/Codexes2Gemini/private/pg19/metadata.csv"
DATA_DIRS = [
    "/Users/fred/bin/Codexes2Gemini/Codexes2Gemini/private/pg19/test/test",
    "/Users/fred/bin/Codexes2Gemini/Codexes2Gemini/private/pg19/train/train",
    "/Users/fred/bin/Codexes2Gemini/Codexes2Gemini/private/pg19/validation/validation",
]

# Initialize Codexes2Parts class
CODEXES2PARTS = Codexes2Parts()


def create_file_index(metadata_file, data_dirs):
    """Creates a file index for efficient lookup of text files."""
    file_index = {}
    with open(metadata_file, "r") as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            textfilename = row[0]
            for data_dir in data_dirs:
                filepath = os.path.join(data_dir, f"{textfilename}.txt")
                if os.path.exists(filepath):
                    file_index[textfilename] = filepath
                    break
    return file_index


def process_document(filepath):
    """Processes a single document using Codexes2Parts."""
    with open(filepath, "r") as f:
        text = f.read()
    BL = BuildLauncher()
    pln = BL.create_prompt_plan(
        config={"context": text, "mode": "codex", "complete_system_instruction": "You are thorough and energetic.",
                "user_prompt": "Summarize this document in nine words or fewer.", "thisdoc_dir": "output/collapsar/"})
    print(type(pln))

    safety_settings = CODEXES2PARTS.safety_settings
    generation_config = CODEXES2PARTS.generation_config
    model = CODEXES2PARTS.create_model("gemini-1.5-flash-001", safety_settings, generation_config, cache=None)
    response = CODEXES2PARTS.gemini_get_response(pln, pln.complete_system_instruction, pln.user_prompt, pln.context,
                                                 model)
    print(response)


def main():
    """Main function to process and enhance PG19 dataset."""
    file_index = create_file_index(METADATA_FILE, DATA_DIRS)

    with open(METADATA_FILE, "r") as f:
        reader = csv.reader(f)
        next(reader)  # Skip header row
        rows = list(reader)

    selected_rows = random.sample(rows, N)

    for row in selected_rows:
        textfilename = row[0]
        filepath = file_index.get(textfilename)
        if filepath is None:
            print(f"Warning: Could not find file for {textfilename}")
            continue
        process_document(filepath)


if __name__ == "__main__":
    main()
