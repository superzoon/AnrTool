import sys, re, os, datetime, configparser, tarfile, zipfile, socket, uuid
from os import (walk, path, listdir, popen, remove, rename, makedirs)
from os.path import (realpath, isdir, isfile, sep, dirname, abspath, exists, basename, getsize)
from shutil import (copytree, rmtree, copyfile, move)
from sys import argv
from zipfile import ZipFile
from Tool.workThread import LockUtil
from Tool import logUtils
import time
from threading import current_thread

getTime = lambda timeStr: time.mktime(time.strptime(timeStr, '%Y-%m-%d %H:%M:%S.%f'))
BASE_TIME_FLOAT = time.mktime((2000,0,0,0,0,0,0,0,0))
def getUsedTimeStr(startTime:float, endTime:float):
    used = int(endTime-startTime)
    return  'time = {} , s = {}'.format(time.strftime("%H:%M:%S",time.localtime(BASE_TIME_FLOAT+used)),used)

def getNextItem(array, item, defItem):
    index = array.index(item) if item in array else -1
    if index > 0 and len(array) >= (index+2):
        return array[index+1]
    return defItem

def zip_single(src_file, dest_zip):
    z = zipfile.ZipFile(dest_zip, 'w')
    cwd = os.getcwd()
    os.chdir(src_file)
    for root_path, dir_names, file_names in os.walk('.'):
        for fn in file_names:
            file = os.path.join(root_path, fn)
            z.write(file)
    z.close()
    os.chdir(cwd)

def unzip_single(src_file, dest_dir, password = None):
    ''' 解压单个文件到目标文件夹。'''
    LockUtil.acquire()
    if password:
        password = password.encode()
    zf = zipfile.ZipFile(src_file)
    cwd = os.getcwd()
    os.chdir(dest_dir)
    root_path = None
    for name in zf.namelist():
        zinfo = zf.getinfo(name)
        if zinfo.flag_bits & 0x800:
            fname_str=name
        else:
            fname_str=name.encode('cp437').decode('gbk')
        try:
            if fname_str.endswith('/') and fname_str.count('/')==1 and fname_str!=name:
                root_path = name
            if not fname_str.endswith('/'):
                if not isdir(dirname(fname_str)) and len(dirname(fname_str)) > 0:
                    makedirs(dirname(fname_str))
                zf.extract(name, dest_dir, pwd=password)
                if name != fname_str:
                    os.rename(name, fname_str)
            elif not isdir(fname_str):
                makedirs(fname_str)
        except RuntimeError:
            logUtils.logException('unzip_single')
    if root_path and isdir(root_path):
        rmtree(root_path)
    zf.close()
    os.chdir(cwd)
    LockUtil.release()

def encodeAndDecode(dest_dir:str):
    for root_path, dir_names, file_names in os.walk(dest_dir):
        for fn in dir_names:
            path = os.path.join(root_path, fn)
            if not zipfile.is_zipfile(path):
                try:
                    fn = fn.encode('cp437').decode('utf-8')
                    new_path = os.path.join(root_path, fn)
                    os.rename(path, new_path)
                except Exception :
                    logUtils.logException('encodeAndDecode')

def unzip_all(source_dir, dest_dir, password):
     if not os.path.isdir(source_dir):    # 如果是单一文件
         unzip_single(source_dir, dest_dir, password)
     else:
         it = os.scandir(source_dir)
         for entry in it:
             if entry.is_file() and os.path.splitext(entry.name)[1]=='.zip' :
                 unzip_single(entry.path, dest_dir, password)

def getAllFileName(dst_dir):
    allFiles = []
    for parent, dirnames, filenames in os.walk(dst_dir):
        if '.svn' in parent or '.git' in parent:
            continue
        for filename in filenames:
            allFiles.append(((parent if parent.endswith(sep) else parent+sep)+filename))
    return allFiles

def getTimeFloat(timeStr: str):
    return datetime.datetime.strptime(timeStr, '%Y-%m-%d %H:%M:%S.%f').timestamp()
    #return time.mktime(time.strptime(timeStr, '%Y-%m-%d %H:%M:%S.%f'))

def getTimeStamp(timeFloat):
    return datetime.datetime.fromtimestamp(timeFloat)
    #return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timeFloat))

def checkFileCode(filename):
    '''检查该文件的字符编码 避免读取字符串报错
    :param filename: 文件路径
    :return: 字符编码格式
    '''
    import codecs
    for encode in ['utf-8','gb2312','gb18030','gbk','cp437','ISO-8859-2','Error']:
        try:
            f = codecs.open(filename, mode='r', encoding=encode)
            u = f.read()
            f.close()
            return encode
        except:
            if encode=='Error':
                return None

def parseProp(propFiles):
    allProp = {}
    keys = [
        'ro.build.date','ro.build.display.id',
        'ro.build.rom.id','ro.build.version.sdk'
            ]
    for file in propFiles:
        with open(file, encoding=checkFileCode(file)) as mFile:
            while True:
                line = mFile.readline()
                if not line:
                    break
                else:
                    line = line.strip()
                    match = re.match( '^.*\[(.*)\].*\[(.*)\].*', line)
                    if match and match.group(1) in keys:
                        allProp[match.group(1)] = match.group(2)
    return allProp

import socket
import getpass

user_name = getpass.getuser() # 获取当前用户名
hostname = socket.gethostname() # 获取当前主机名