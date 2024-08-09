#  Copyright (c) 2024. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com
import os
import subprocess
import sys

# Assuming BookAnalysisPlan.py and text2gemini.py are in the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Ensure the script can find the modules
sys.path.append(current_dir)

# Import the BookAnalysisPlan class
from BookAnalysisPlan import BookAnalysisPlan

# Create an instance of BookAnalysisPlan with default settings
plan = BookAnalysisPlan()

# Create a temporary script to run text2gemini.py with default settings
script_content = f"""
import sys
sys.path.append(r'{current_dir}')
from text2gemini import Text2Gemini
from BookAnalysisPlan import BookAnalysisPlan

# Initialize the plan
plan = BookAnalysisPlan()

# Initialize Text2Gemini
t2g = Text2Gemini()

# Set up arguments for the plan
class Args:
    def __init__(self, **entries):
        self.__dict__.update(entries)

args = Args(**vars(plan))

# Run the main function with default arguments
t2g.submit_to_gemini(args)
"""

# Write the script content to a temporary file
temp_script_path = os.path.join(current_dir, 'temp_test_script.py')
with open(temp_script_path, 'w') as temp_script_file:
    temp_script_file.write(script_content)

# Run the temporary script using subprocess
subprocess.run(['python3', temp_script_path])

# Optionally, clean up the temporary script file after execution
os.remove(temp_script_path)
