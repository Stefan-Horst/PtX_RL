import logging
from enum import Enum

import rlptx.util as util


LOGFILE_PATH = 'logs/'

util.mkdir(LOGFILE_PATH)

LOGFILE_NAME = 'log.txt'
LOGGER_NAME = 'main'

loggers = {}
disabled_loggers = []


# for easy use in log function
class Level(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


def configure_logger(loggername, path=LOGFILE_PATH, filename=LOGFILE_NAME):
    """Configure and return a new logger. Initially, the default logger is created from 
    this function's default parameters. Every logger is configured  to write levels DEBUG 
    and higher to console and levels INFO and higher also to file."""
    if loggername in disabled_loggers:
        return
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    filename = (f"{util.get_timestamp()}_{loggername}_{filename}")
    file_handler = logging.FileHandler(util.PROJECT_DIR / path / filename, mode='a')
    file_handler.setLevel(logging.INFO)

    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)-8s - %(levelname)-5s - %(message)s', datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)

    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)-8s - %(message)s', datefmt='%d-%m %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)

    logger = logging.getLogger(loggername)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger


# provide simple logging utility from inside this module
def log(message, loggername=LOGGER_NAME, level=logging.INFO):
    """Log a message to the given logger at the given log level if the logger is enabled. 
    A new logger is created and used if the loggername does not exist yet."""
    if loggername in disabled_loggers:
        return
    
    if len(loggers) == 0: # create default logger
        loggers[LOGGER_NAME] = configure_logger(LOGGER_NAME)
        
    # handle enum from this class vs int from logging module
    level = level.value if isinstance(level, Level) else level
    if loggername not in loggers:
        loggers[loggername] = configure_logger(loggername)
    loggers[loggername].log(level, message)

def reset_loggers():
    """Remove all created loggers."""
    global loggers
    for logger in loggers.values():
        try:
            for handler in logger.handlers:
                logger.removeHandler(handler)
                handler.close()
            logging.root.manager.loggerDict.pop(logger.name)
        except Exception as e:
            print(e)
    loggers.clear()

def disable_logger(loggername=None):
    """Disable logging to the given logger. If no loggername 
    is given, disable logging to all loggers."""
    if loggername is None:
        global disabled_loggers
        disabled_loggers = list(loggers.keys())
    elif loggername not in disabled_loggers:
        disabled_loggers.append(loggername)

def enable_logger(loggername=None):
    """Enable logging to the given logger. If no loggername 
    is given, enable logging to all loggers."""
    if loggername is None:
        disabled_loggers.clear()
    elif loggername in disabled_loggers:
        disabled_loggers.remove(loggername)
