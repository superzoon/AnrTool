import sys, re, os, datetime, configparser, tarfile, zipfile, socket, uuid
from os import (walk, path, listdir, popen, remove, rename, makedirs)
from os.path import (realpath, isdir, isfile, sep, dirname, abspath, exists, basename, getsize)
from shutil import (copytree, rmtree, copyfile, move)
from xml.dom import (Node,minidom)
from xml.dom.minidom import Document
from Tool import logUtils, GLOBAL_VALUES
from Tool.fileObserver import FileObserver, FileEvent, addFileObserver

APP_DATA_PATH = sep.join([os.environ['LOCALAPPDATA'], 'NubiaTool'])
APP_CONFIG_PATH = sep.join([APP_DATA_PATH, 'config'])
if not isdir(APP_CONFIG_PATH):
    makedirs(APP_CONFIG_PATH)

ANDROID_CONFIG_XML = sep.join([APP_CONFIG_PATH,'android.xml'])

class AndroidFile():
    ACTION_NORMAL = 'normal'
    ACTION_KILL = 'kill'
    ACTION_REBOOT = 'reboot'
    ACTION_STOP = 'force-stop'
    def __init__(self, fileName, path, progress=None, action=None, start=None, clean=False, delayTime:int=0):
        self.fileName = fileName
        self.path = path
        self.progress = progress
        if action==AndroidFile.ACTION_KILL or  action==AndroidFile.ACTION_REBOOT or  action==AndroidFile.ACTION_STOP:
            self.action = action
        else:
            self.action = AndroidFile.ACTION_NORMAL
        self.start = start
        self.clean = clean
        self.delayTime = delayTime

    def __str__(self):
        return "fileName={}, path={}, progress={}, action={}, start={}, clean={}, delayTime={}"\
            .format(self.fileName,self.path,self.progress,self.action,self.start,self.clean,self.delayTime)

def __read_android_config__(file:str, config:dict):
    if file and file.endswith('.xml') and isfile(file):
        dom = minidom.parse(file)
        root = dom.documentElement
        for node in [child for child in root.getElementsByTagName("file") if child.nodeType == Node.ELEMENT_NODE]:
            fileName = node.getAttribute("fileName")
            path = node.getAttribute("path")
            progress = node.getAttribute("progress")
            action = node.getAttribute("action")
            start = node.getAttribute("start")
            clean = node.getAttribute("clean")
            if clean and 'yes'==clean:
                clean = True
            else:
                clean = False
            delayTime = node.getAttribute("delayTime").strip()
            if delayTime and re.match('[\d]+', delayTime):
                delayTime = int(delayTime)
            else:
                delayTime = 0

            if fileName and path:
                config[fileName] = AndroidFile(fileName, path, progress, action, start, clean, delayTime)


def __write_android_config__(file:str, config:dict):
    if config:
        doc = Document()
        doc.encoding = 'utf-8'
        root = doc.createElement('android')
        for androidFile in config.values():
            node = doc.createElement('file')
            node.setAttribute('fileName', androidFile.fileName)
            node.setAttribute('path', androidFile.path)
            if androidFile.progress:
                node.setAttribute('progress', androidFile.progress)
            if androidFile.action:
                node.setAttribute('action', androidFile.action)
            if androidFile.start:
                node.setAttribute('start', androidFile.start)
            if androidFile.clean:
                node.setAttribute('clean', 'yes')
            if androidFile.delayTime:
                node.setAttribute('delayTime', str(androidFile.delayTime))
            root.appendChild(node)
    if not isdir(dirname(file)):
        makedirs(dirname(file))
    with open(file, mode='w', encoding='utf-8') as out:
        out.write(root.toprettyxml(indent='    '))
        out.close()

ANDROID_FILE_CONFIG = dict()

# 配置文件更改后保存到系统路径中
def __onAndroidConfigChange__(event:FileEvent):
    if event and not event.file != ANDROID_CONFIG_XML:
        logUtils.info(event)
        if event.action == FileEvent.MODIFIED or event.action == FileEvent.CREATED:
            __read_android_config__(event.file, ANDROID_FILE_CONFIG)
            __write_android_config__(ANDROID_CONFIG_XML, ANDROID_FILE_CONFIG)


GLOBAL_VALUES.androidConfigFiles = list()
def getAndroidFileConfig(configFile:str=sep.join([dirname(__file__), 'config', 'android.xml'])):
    # 对配置文件进行监听，
    if configFile and not configFile in GLOBAL_VALUES.androidConfigFiles:
        GLOBAL_VALUES.androidConfigFiles.append(configFile)
        addFileObserver(FileObserver(configFile, __onAndroidConfigChange__))
    # 读取系统配置中的值
    if isfile(ANDROID_CONFIG_XML):
        __read_android_config__(ANDROID_CONFIG_XML, ANDROID_FILE_CONFIG)
    # 读取配置文件中的值
    if isfile(configFile):
        __read_android_config__(configFile, ANDROID_FILE_CONFIG)
    else:
        logUtils.info('文件不存在 file={}'.format(configFile))
    return ANDROID_FILE_CONFIG

ANDROID_FILE_CONFIG = getAndroidFileConfig()

if __name__ == '__main__':
    import time
    ANDROID_FILE_CONFIG = getAndroidFileConfig(sep.join([dirname(dirname(__file__)),'config','android.xml']))
    while True:

        print( '\n,'.join([str(item) for item in ANDROID_FILE_CONFIG.values()]))
        time.sleep(30)