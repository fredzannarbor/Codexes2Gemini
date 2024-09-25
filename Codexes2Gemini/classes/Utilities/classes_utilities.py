#  Copyright (c) 2023. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com


import inspect
import logging
import sys
import streamlit
import pandas as pd
import pip
from rich.console import Console
from Codexes2Gemini import ensure_directory_exists

console = Console(record=True)




def set_logging_level(log_level: str):
    """
    Sets the logging level for the application.

    Args:
        log_level (str): The desired logging level. Valid options are:
            - DEBUG
            - INFO
            - WARNING
            - ERROR
            - CRITICAL

    Raises:
        ValueError: If an invalid log level is provided.
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')
    logging.basicConfig(filename="logs/applications.log", level=numeric_level,
                        format='%(asctime)s - %(levelname)s - %(message)s')


def where_am_i_running_to_dict():
    """
    Returns a dictionary containing the module name and function name of the current execution context.

    Returns:
        tuple: A tuple containing the module name and function name as strings.
    """
    modulename = __name__
    functionname = inspect.currentframe().f_code.co_name
    return modulename, functionname


def where_am_I_running_to_string(modulename, functionname):
    """
    Returns a string representation of the module name and function name of the current execution context.

    Args:
        modulename (str): The name of the module.
        functionname (str): The name of the function.

    Returns:
        str: A string representation of the module name and function name.
    """
    modulename = __name__
    functionname = inspect.currentframe().f_code.co_name
    return f"{modulename}:{functionname}"



def configure_logger(log_level):
    """
    Configures the application logger with the specified logging level.

    Args:
        log_level (str): The desired logging level. Valid options are:
            - DEBUG
            - INFO
            - WARNING
            - ERROR
            - CRITICAL

    Returns:
        logging.Logger: The configured logger object.
    """
    # create log directory in user's home directory
    logdir_path = ensure_directory_exists("logs")


    # Create logger object

    # logger = logging.getLogger(__name__)
    logger = logging.getLogger("applications")
    # print(logger)

    # Set logger to handle all messages
    logger.setLevel(logging.DEBUG)

    for handler in logger.handlers[:]:  # list copy for iteration
        handler.close()
        logger.removeHandler(handler)

    # Create a file handler that handles all messages and writes them to a file
    file_handler = logging.FileHandler(os.path.join(logdir_path, "c2g.log"))
    file_handler.setLevel(logging.DEBUG)

    # Create a stream handler that handles only warning and above messages
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))

    formatter_string = '%(asctime)s - %(levelname)s - %(module)s - %(lineno)d: %(message)s'
    # Create formatter
    formatter = logging.Formatter(formatter_string)

    # Assign the formatter to the handlers
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    numeric_level = console_handler.level

    # Convert numeric level to string
    level_name = logging.getLevelName(numeric_level)

    logging.info(f"The level of the console handler is: {level_name}")
    logging.info(f"the formatter string is {formatter_string}")

    # Add both handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def get_pip_version():
    try:
        pip_version = pip.__version__
        logging.info(f"Pip Version: {pip_version}")
        return pip_version
    except AttributeError:
        logging.info("Pip version not found.")


def get_commit_messages():
    """Fetches commit messages from the main branch in reverse chronological order."""
    try:
        # Execute the git command and capture the output
        output = subprocess.check_output(['git', 'log', '--pretty=format:- %s (%h) <br>', 'main'],
                                         stderr=subprocess.STDOUT)
        # Decode the output from bytes to string
        commit_messages = output.decode('utf-8')
        return commit_messages
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.output.decode('utf-8')}")
        return ""


import os
import subprocess


def get_commit_messages():
    """Fetches commit messages from the main branch in reverse chronological order."""
    try:
        # Execute the git command and capture the output
        output = subprocess.check_output(['git', 'log', '--pretty=format:- %s (%h) <br>', 'main'],
                                         stderr=subprocess.STDOUT)
        # Decode the output from bytes to string
        commit_messages = output.decode('utf-8')
        return commit_messages
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.output.decode('utf-8')}")
        return ""


def write_commit_messages_to_file(filename="Commit History.md"):
    """Writes the commit messages to a file."""
    # Get the absolute path of the directory containing setup.py
    setup_py_dir = os.path.dirname(os.path.abspath(__file__))
    # Construct the full path to the output file
    filepath = os.path.join(setup_py_dir, filename)

    commit_messages_md = get_commit_messages()
    with open(filepath, "w") as f:
        f.write(commit_messages_md)
    print(f"Commit messages written to: {filepath}")


def load_spreadsheet(filename):
    """
    Load a spreadsheet file into a pandas DataFrame.

    Parameters:
    filename (str): File path to the spreadsheet.


    Returns:
    DataFrame: pandas DataFrame with the spreadsheet data.

    Try utf-8 encoding first for csv, then ISO-8859-1, then Win-1252

    """
    # Check the file extension
    _, extension = os.path.splitext(filename)

    if extension == '.csv':
        encoding_options = ['utf-8', 'ISO-8859-1', 'Win-1252']
        for encoding in encoding_options:
            try:
                df = pd.read_csv(filename, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue

    elif extension == ".xlsx":
        df = pd.read_excel(filename, engine='openpyxl')

    elif extension == ".xls":
        df = pd.read_excel(filename)

    return df
