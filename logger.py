import logging
import util


LOGFILE_PATH = 'logs/'

util.mkdir(LOGFILE_PATH)

# configure logger to write levels DEBUG and higher to console and leveles INFO and higher also to file

LOGFILE_NAME = 'log.txt'

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(util.PROJECT_DIR / LOGFILE_PATH / LOGFILE_NAME, mode='a')
file_handler.setLevel(logging.INFO)

console_formatter = logging.Formatter('%(asctime)s - %(name)-8s - %(levelname)-5s - %(message)s', datefmt='%H:%M:%S')
console_handler.setFormatter(console_formatter)

file_formatter = logging.Formatter('%(asctime)s - %(name)-12s - %(levelname)-8s - %(message)s', datefmt='%d-%m %H:%M:%S')
file_handler.setFormatter(file_formatter)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# provide simple logging utility from inside this module
def log(message, level=logging.INFO):
    logger.log(level, message)
    