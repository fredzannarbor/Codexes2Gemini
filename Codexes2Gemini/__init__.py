import os
import sys
from pathlib import Path

current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory
parent_dir = os.path.dirname(current_dir)

# Get the directory above the parent
grandparent_dir = os.path.dirname(parent_dir)

# Append both directories to the Python path
sys.path.append(parent_dir)
sys.path.append(grandparent_dir)


def ensure_directory_exists(directory_name):
    """Ensures a directory exists, handling package installation and source code execution.

    Args:
        directory_name: The name of the directory to create.
    """

    try:
        # Try to get the package installation directory
        base_dir = Path(__file__).resolve().parent.parent / ".codexes2gemini"
    except NameError:
        # If __file__ is not defined (running from source), use the project root
        base_dir = Path(__file__).resolve().parent.parent / "Codexes2Gemini"

    target_dir = base_dir / directory_name
    target_dir.mkdir(parents=True, exist_ok=True)

    return target_dir

ensure_directory_exists("output")
ensure_directory_exists("output/c2g")
ensure_directory_exists("output/collapsar")
ensure_directory_exists("logs")
ensure_directory_exists("user_data")
ensure_directory_exists("user_data/self")
ensure_directory_exists("resources")
ensure_directory_exists("resources/data_tables")
ensure_directory_exists("resources/data_tables/LSI")
ensure_directory_exists("processed_data")

__version__ = "0.4.4.0"
__announcements__ = """
- Adds ability to save and load PromptPacks as JSON
- renames InstructionPacks to PromptPacks for clarity, consistency
- Fixes incorrect path assignment for dataset2gemini cli.
- Makes pdf creation of latex markdown fail gracefully.
- Adds data editor to allow removing docs from selection.
- Fixes method name, parameter call in pg19 fetcher.
- Improvements to document assembly.
- Additional prompts, tweaks to existing ones
- More accurate object sizing and location for duplex covers.
"""
