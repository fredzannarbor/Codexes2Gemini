import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory
parent_dir = os.path.dirname(current_dir)

# Get the directory above the parent
grandparent_dir = os.path.dirname(parent_dir)

# Append both directories to the Python path
sys.path.append(parent_dir)
sys.path.append(grandparent_dir)


def ensure_directory_exists(directory_path):
    """Ensures that a directory exists, creating it if necessary."""
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)


# Create the output directory
ensure_directory_exists("output")
ensure_directory_exists("output/c2g")
ensure_directory_exists("logs")
ensure_directory_exists("userspaces")
ensure_directory_exists("userspaces/self")

__version__ = "0.2.3.2"
__announcements__ = """

"""
