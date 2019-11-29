from multiprocessing import cpu_count,current_process
from os.path import (realpath, isdir, isfile, sep, dirname, abspath, exists, basename, getsize)
from Tool.logUtils import debug
import traceback
if __name__ == '__main__':
    print(basename('istrator\AppData\Local\Programs\Python\Python36-32\python.zip').replace('.zip', '.txt'))