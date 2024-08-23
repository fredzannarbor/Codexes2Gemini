import os


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

__version__ = "0.2.2.19"
__announcements__ = """
- Adds chardet to required packages
---
- **Improves packaging of resources to avoid file not found errors**, ensure forward compatibility.
- Streamlines logging.
- Adds self-identification.
"""
