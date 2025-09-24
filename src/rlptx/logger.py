import logging
from enum import Enum

import rlptx.util as util


LOGFILE_PATH = 'logs/'

util.mkdir(LOGFILE_PATH)

LOGFILE_NAME = 'log.txt'
LOGGER_NAME = 'main'

loggers = {}
disabled_loggers = []

deferred_logs = []


# for easy use in log function
class Level(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


def configure_logger(loggername, path=LOGFILE_PATH, filename=LOGFILE_NAME, 
                     console_level=logging.DEBUG, file_level=logging.INFO):
    """Configure and return a new logger. Every logger is by default configured to write levels 
    DEBUG and higher to console and levels INFO and higher also to a file in the logs folder."""
    if loggername in disabled_loggers:
        return
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)

    filename = (f"{util.get_timestamp()}_{loggername}_{filename}")
    file_handler = logging.FileHandler(util.PROJECT_DIR / path / filename, mode='a')
    file_handler.setLevel(file_level)

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
def log(message, loggername=LOGGER_NAME, level=logging.INFO, deferred=False):
    """Log a message to the given logger at the given log level if the logger is enabled. 
    A new logger is created and used if the loggername does not exist yet. 
    Deferring logs prevents immediately writing them to output; they will be written when 
    flush_deferred_logs() is called. This prevents the interruption of progress bars."""
    if loggername in disabled_loggers:
        return

    # handle enum from this class vs int from logging module
    level = level.value if isinstance(level, Level) else level
    if loggername not in loggers:
        loggers[loggername] = configure_logger(loggername)
    
    if not deferred:
        # make sure all logs appear in the right order in the output by writing deferred ones first
        flush_deferred_logs()
        loggers[loggername].log(level, message)
    else:
        deferred_logs.append((loggername, level, message))

def flush_deferred_logs():
    """Write all deferred logs to output."""
    for loggername, level, message in deferred_logs:
        loggers[loggername].log(level, message)
    deferred_logs.clear()

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
