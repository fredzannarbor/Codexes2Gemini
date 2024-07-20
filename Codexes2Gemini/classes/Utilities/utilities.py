#  Copyright (c) 2023. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com


import inspect
import logging
import sys

from rich.console import Console

console = Console(record=True)


def set_logging_level(log_level: str):
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')
    logging.basicConfig(filename="logs/applications.log", level=numeric_level,
                        format='%(asctime)s - %(levelname)s - %(message)s')


def where_am_i_running_to_dict():
    modulename = __name__
    functionname = inspect.currentframe().f_code.co_name
    return modulename, functionname


def where_am_I_running_to_string(modulename, functionname):
    modulename = __name__
    functionname = inspect.currentframe().f_code.co_name
    return f"{modulename}:{functionname}"



def configure_logger(log_level):
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
    file_handler = logging.FileHandler('logs/applications.log')
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

    print(f"The level of the console handler is: {level_name}")
    print(f"the formatter string is {formatter_string}")

    # Add both handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

