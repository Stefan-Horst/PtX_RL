import logging
import datetime
from enum import Enum

import util


LOGFILE_PATH = 'logs/'

util.mkdir(LOGFILE_PATH)

LOGFILE_NAME = 'log.txt'
LOGGER_NAME = 'main'


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
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    timestamp = datetime.datetime.now().replace(microsecond=0)
    filename = (f"{str(timestamp)}_{loggername}_{filename}").replace(':', '-').replace(' ', '_')
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

loggers = {LOGGER_NAME: configure_logger(LOGGER_NAME)}

# provide simple logging utility from inside this module
def log(message, loggername=LOGGER_NAME, level=logging.INFO):
    """Log a message to the given loggername at the given log level. 
    A new logger is created and used if the loggername does not exist yet."""
    if loggername not in loggers:
        loggers[loggername] = configure_logger(loggername)
    loggers[loggername].log(level, message) 
