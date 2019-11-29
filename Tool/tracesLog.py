
import re
from os.path import sep
from Tool import toolUtils
from os.path import (realpath, isdir, isfile, sep, dirname, abspath, exists, basename, getsize)
from Tool import GlobalValues
class ThreadStack:
    def __init__(self, name:str, prio, tid, state, pid, top, pidStack):
        self.name = name
        if name.startswith('HwBinder:{}_'.format(pid)) or name.startswith('Binder:{}_'.format(pid)):
            self.isBinderThread = True
        else:
            self.isBinderThread = False
        self.prio = prio
        self.tid = tid
        self.state = state
        self.nativeStacks = []
        self.javaStacks = []
        self.pid = pid
        self.top = top
        self.hasSameStack = False
        if 'Blocked'.lower() == str(self.state).lower():
            self.isBlock = True
        else:
            self.isBlock = False
        self.pidStack = pidStack

    def addLine(self, line:str):
        isParser = False
        if line.strip().startswith('native'):
            self.nativeStacks.append(line)
            isParser = True
        elif line.strip().startswith('at') or line.strip().startswith('- '):
            self.javaStacks.append(line)
            isParser = True
        return isParser

class PidStack:
    def __init__(self, pid, time, timeline, globalValues:GlobalValues):
        self.pid = pid
        self.time = time
        self.timeline = timeline
        self.packageName = ''
        self.threadStacks:ThreadStack = []
        self.tempThreadStack = None
        self.isSystemServer = False
        self.maxBlockNumber = 0
        self.maxBlockStack = None
        self.globalValues = globalValues

    def getMainStack(self):
        for threadStack in self.threadStacks:
            if threadStack.name == 'main':
                return threadStack

    pattern_cmd = '.*Cmd line: (.*)'
    pattern_thread = '"(.*)" prio=([\d]+) tid=([\d]+) ([\w]+).*'
    def addLine(self, line:str):
        match = re.match(PidStack.pattern_cmd, line)
        if match:
            self.packageName = match.group(1).strip()
            self.globalValues.pidMap[int(self.pid)] = self.packageName
            if self.packageName == 'system_server':
                self.isSystemServer = True

        match = re.match(PidStack.pattern_thread, line)
        isParser = False
        if len(line.strip()) == 0:
            self.tempThreadStack = None
        elif match:
            self.tempThreadStack = ThreadStack(match.group(1), match.group(2), match.group(3), match.group(4), self.pid,  line, self)
            self.threadStacks.append(self.tempThreadStack)
            isParser = True

        if self.tempThreadStack != None:
            self.tempThreadStack.addLine(line)

        return isParser

    def check(self):
        keyMap = dict()
        blockMap = dict()
        for stack in self.threadStacks:
            if stack.isBinderThread and stack.isBlock and stack.javaStacks:
                key = str(stack.javaStacks[:3])
                if key in keyMap:
                    keyMap[key] = keyMap[key] + 1
                else:
                    keyMap[key] = 1
                    blockMap[key] = stack
                if self.maxBlockNumber <  keyMap[key]:
                    self.maxBlockNumber = keyMap[key]
                    self.maxBlockStack = blockMap[key]

    PATTERN_PID = '----- pid ([\d]+) at ([\d]{4}-[\d]{2}-[\d]{2} [\d]{2}:[\d]{2}:[\d]{2}) -----'

    @staticmethod
    def getPidStack(line:str, globalValues):
        match = re.match(PidStack.PATTERN_PID, line)
        if match:
            return PidStack(match.group(1), match.group(2), line, globalValues)
        return None

class TracesLog():

    def __init__(self, file, globalValues:GlobalValues, packageName: str = 'com.android.systemui'):
        self.globalValues = globalValues
        self.file = file
        self.packageName = packageName
        self.pidStacks:PidStack = list()
        self.binderOutgoing = dict()
        self.hungerBinders = globalValues.hungerBinders
        self.suspiciousStack = dict()


    #'outgoing transaction 4019025: 0000000000000000 from 7075:7075 to 1333:0 code 1 flags 10 pri 0:120 r1'
    OUTGOING_PATTERN = 'outgoing transaction .* from ([\d]+:[\d]+) to ([\d]+:[\d]+) .* '
    def parserBinderLine(self, line):
        match = re.match(TracesLog.OUTGOING_PATTERN, line)
        if match:
            outTid = match.group(1)
            inTid = match.group(2)
            self.binderOutgoing[outTid] = inTid
            if inTid.split(':')[1]=='0':
                self.hungerBinders[outTid] = inTid

    def addPidStackToList(self,pidStack:PidStack):
        inList = False
        if not pidStack:
            return
        for stack in self.pidStacks:
            if str(stack.pid) == str(pidStack.pid):
                inList = True

        if not inList:
            self.pidStacks.append(pidStack)

    def parser(self):
        with open(self.file, encoding=toolUtils.checkFileCode(self.file)) as mmFile:
            lines = mmFile.readlines()
            tempPidStack = None
            binderTransaction = False
            for line in [line.strip() for line in lines]:
                if 'Binder Transaction Start' in line:
                    binderTransaction = True
                elif 'Binder Transaction End' in line:
                    binderTransaction = False

                if binderTransaction:
                    self.parserBinderLine(line)
                else:
                    newPid = PidStack.getPidStack(line, self.globalValues)
                    if newPid:
                        if tempPidStack:
                            tempPidStack.check()
                        tempPidStack = newPid
                        self.addPidStackToList(tempPidStack)
                    if tempPidStack:
                        tempPidStack.addLine(line)
            if tempPidStack:
                tempPidStack.check()
                self.addPidStackToList(tempPidStack)

            for stack in [stack for stack in self.pidStacks if stack.maxBlockNumber > 3]:
                pidName = int(stack.pid)
                if int(stack.pid) in self.globalValues.pidMap:
                    pidName = self.globalValues.pidMap[pidName]
                key = 'pid{} {} 单个进程binder阻塞{}个,{}'.format(stack.pid, pidName, str(stack.maxBlockNumber), self.file[len(dirname(self.file))+1:])
                self.suspiciousStack[key] = stack.maxBlockStack

    def getMainStack(self):
        threadStack = []
        for stack in [stack for stack in self.pidStacks if stack.getMainStack() and stack.packageName == self.packageName]:
            threadStack.append(stack.getMainStack())
        if len(threadStack)>=2 :
            if  threadStack[0].javaStacks == threadStack[1].javaStacks:
                if threadStack[0].javaStacks and not threadStack[0].isBlock:
                    threadStack[0].isBlock = True
                    threadStack[0].top = threadStack[0].top+' --> 阻塞Stack'
                if threadStack[1].javaStacks and not threadStack[1].isBlock:
                    threadStack[1].isBlock = True
                    threadStack[1].top = threadStack[1].top+' --> 阻塞Stack'
            return threadStack[0]
        elif len(threadStack)>0 and threadStack[0].javaStacks:
            return threadStack[0]
        return None



