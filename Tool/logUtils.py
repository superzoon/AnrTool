import logging

from os.path import isfile
from os import remove
from traceback import TracebackException, format_exc
import sys

LOG_FILE = "log.txt"
TAG = "xlan"

try:
    if isfile(LOG_FILE):
        remove(LOG_FILE)
except Exception as e:
    print('初始化log文件异常 {}'.format(e.args))

logger = logging.getLogger(TAG)

handler1 = logging.StreamHandler()
handler2 = logging.FileHandler(filename=LOG_FILE)

logger.setLevel(logging.DEBUG)
handler1.setLevel(logging.WARNING)
handler2.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
handler1.setFormatter(formatter)
handler2.setFormatter(formatter)

logger.addHandler(handler1)
logger.addHandler(handler2)

def debug(msg, printMsg:bool=True):
    logger.debug(msg)
    if printMsg:
        print(msg)

def info(msg, printMsg:bool=True):
    logger.info(msg)
    if printMsg:
        print(msg)

def info(msg, printMsg:bool=True):
    logger.info(msg)
    if printMsg:
        print(msg)

def warning(msg, printMsg:bool=True):
    logger.warning(msg)

def error(msg, printMsg:bool=True):
    logger.error(msg)

def critical(msg, printMsg:bool=True):
    logger.critical(msg)

def logException(msg, printMsg:bool=False):
     error('{}:\n{}'.format(msg, format_exc()), printMsg)

def traceback(printMsg:bool=False):
    (etype, value, tb) = sys.exc_info()
    for line in TracebackException(type(value), value, tb, limit=None).format(chain=True):
        warning(line, printMsg)

