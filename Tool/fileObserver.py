
from os.path import (realpath, isdir, isfile, sep, dirname, abspath, exists, basename, getsize)
from Tool.workThread import WorkThread
from Tool import GLOBAL_VALUES, toolUtils
import os, time

class FileEvent():
    CREATED = 1
    DELETED = 2
    MODIFIED = 3
    def __init__(self, file:str, action:int):
        self.file = file
        self.action = action
        if action == FileEvent.CREATED:
            self.actionStr = 'crate'
        elif action == FileEvent.DELETED:
            self.actionStr = 'deleted'
        elif action == FileEvent.MODIFIED:
            self.actionStr = 'modify'
        else:
            self.actionStr = 'normal'

    def __str__(self):
        return 'file={}, action={}, actionStr={}'.format(self.file.replace(sep, '/'), self.action, self.actionStr)

def _update_observer_():
    if len(GLOBAL_VALUES.observerFiles) > 0 and not GLOBAL_VALUES.isObserverRun:
        GLOBAL_VALUES.isObserverFile = True
        GLOBAL_VALUES.observerThread.start()
    else:
        GLOBAL_VALUES.isObserverFile = False

class FileObserver():
    NO_FILE_NO_OBSERVER = False
    def __init__(self, file:str, callback):
        '''
        :param file:
        :param callback(event:FileEvent):
        '''
        self.file = file
        self.isFile = isfile(file)
        self.callback = callback
        self.filing = dict()
        if self.isFile:
            self.fileSize = getsize(file)
            self.file_mtime = os.stat(file).st_mtime
        else:
            self.allFile = dict()
            for path in toolUtils.getAllFileName(self.file):
                self.allFile[path]:os.stat_result = os.stat(path)

    def __check__file__(self):
        if not isfile(self.file) and FileObserver.NO_FILE_NO_OBSERVER:
            self.callback(FileEvent(self.file, FileEvent.DELETED))
            if self in GLOBAL_VALUES.observerFiles:
                GLOBAL_VALUES.observerFiles.remove(self)
                _update_observer_()
        elif getsize(self.file) != self.fileSize or self.file_mtime != os.stat(self.file).st_mtime:
            self.fileSize = getsize(self.file)
            self.file_mtime = os.stat(self.file).st_mtime
            self.callback(FileEvent(self.file, FileEvent.MODIFIED))

    def __check__dir__(self):
        if not isdir(self.file) and FileObserver.NO_FILE_NO_OBSERVER:
            self.callback(FileEvent(self.file, FileEvent.DELETED))
            if self in GLOBAL_VALUES.observerFiles:
                GLOBAL_VALUES.observerFiles.remove(self)
                _update_observer_()
        else:
            allFiles = toolUtils.getAllFileName(self.file)
            newAllFiles = dict()
            for path in allFiles:
                stat = os.stat(path)
                newAllFiles[path]:os.stat_result = stat
                if path in self.allFile:
                    oldStat = self.allFile.pop(path)
                    if stat.st_mtime != oldStat.st_mtime:
                        self.callback(FileEvent(path, FileEvent.MODIFIED))
                else:
                    self.callback(FileEvent(path, FileEvent.CREATED))
            for path, stat in self.allFile.items():
                self.callback(FileEvent(path, FileEvent.DELETED))
            self.allFile = newAllFiles

    def __check__changed__(self):
        if self.isFile:
            self.__check__file__()
        else:
            self.__check__dir__()

GLOBAL_VALUES.observerFiles:FileObserver = list()
GLOBAL_VALUES.isObserverRun = False
GLOBAL_VALUES.isObserverFile = False

def observerRun():
    print('start observer files')
    GLOBAL_VALUES.isObserverRun = True
    while GLOBAL_VALUES.isObserverFile:
        for observer in GLOBAL_VALUES.observerFiles:
            observer.__check__changed__()
        time.sleep(1)
    GLOBAL_VALUES.isObserverRun = False
    GLOBAL_VALUES.observerThread:WorkThread = WorkThread(action=observerRun)
    print('end observer files')

GLOBAL_VALUES.observerThread:WorkThread = WorkThread(action=observerRun)


def removeFileObserver(observer:FileObserver):
    if observer in GLOBAL_VALUES.observerFiles:
        GLOBAL_VALUES.observerFiles.remove(observer)
        _update_observer_()
        return True
    else:
        return False

def addFileObserver(observer:FileObserver):
    if not isfile(observer.file) and not isdir(observer.file):
        return False
    else:
        if observer in GLOBAL_VALUES.observerFiles:
            return False
        else:
            GLOBAL_VALUES.observerFiles.append(observer)
            _update_observer_()
            return True


if __name__ == '__main__':
    fo = FileObserver('D:/GitStub/superzoon/AnrTool/'.replace('/',sep),lambda x:print(x))

    addFileObserver(fo)
    time.sleep(3000)