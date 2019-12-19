from multiprocessing import cpu_count,current_process
from os.path import (realpath, isdir, isfile, sep, dirname, abspath, exists, basename, getsize)
from Tool.logUtils import debug
from Tool.toolUtils import APP_DATA_PATH,APP_CONFIG_PATH
import traceback,re
import socket, os
import getpass
if __name__ == '__main__':

    user_name = getpass.getuser()  # 获取当前用户名
    hostname = socket.gethostname()  # 获取当前主机名

    print(type(user_name))

    print('C:\\Users\\' + user_name + '\\AppData\Local\Temp\\')

    print(hostname)
    print(user_name)
    android_xml = sep.join([APP_CONFIG_PATH,'android.xml'])
    if isfile(android_xml):
        print(os.environ['LOCALAPPDATA'])
