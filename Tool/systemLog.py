from Tool import toolUtils
from Tool import LogLine
from Tool import Anr
from Tool import GlobalValues
import re
class AnrLine(LogLine):

    anr_pattern = '^.*ANR in ([\w|\.]+).*'
    def __init__(self, line: str, linenum:int, globalValues:GlobalValues):
        super().__init__(line, linenum, globalValues)
        self.packageName = None

    def isAnrLine(self, packageName: str = 'com.android.systemui'):
        if not self.isLogLine or not self.tag or not self.msg :
            return False
        match = re.match(AnrLine.anr_pattern, self.msg)
        if match:
            self.packageName = match.group(1).strip()
            return self.packageName == packageName
        else:
            return False

class SystemAnr():

    def __init__(self, line: AnrLine,anr: Anr):
        self.anrLine = line
        self.anr:Anr = anr
        self.anr.anrPackageName = line.packageName
        self.anr.pid = line.pid
        self.lines = []
        self.lines.append(line)
        self.pid = -1
        self.usage_time = 0
        self.cpu_one = None
        self.cpu_two = None

    def addLine(self, line: LogLine, allAnr:Anr):
        self.lines.append(line)
        if len(self.lines) < 8:
            self.parser(line.msg.strip(), allAnr)

    def getYear(self):
        return self.anrLine.timeYear

    pid_pattern = '^PID:(.*)'
    '''Reason: Broadcast of Intent { act=android.intent.action.TIME_TICK flg=0x50200014 (has extras) }'''
    reason_pattern = '^Reason:(.*)'
    '''CPU usage from 0ms to 7411ms later (2019-10-11 12:29:13.178 to 2019-10-11 12:29:20.589):'''
    cpu_pattern = '^CPU usage from ([\d]+)ms to ([-|\d]+)ms.*\(([\d]{4}).*'

    def parser(self, msg: str, allAnr:Anr):
        match = re.match(SystemAnr.pid_pattern, msg)
        if match:
            self.pid = int(match.group(1).strip())
            self.anr.pid = self.pid
            samePidCount = len([anr for anr in allAnr if anr.pid == self.pid])
            if allAnr and samePidCount > 1 and self.anr in allAnr:
                allAnr.remove(self.anr)
        match = re.match(SystemAnr.reason_pattern, msg)
        if match:
            self.anr.anrReason = match.group(1).strip()
            self.parseReason(self.anr.anrReason)
            return
        match = re.match(SystemAnr.cpu_pattern, msg)
        if match:
            self.usage_time = int(match.group(2).strip())-int(match.group(1).strip())
            self.anrLine.globalValues.year = match.group(3)
            self.anrLine.updateYear()
            self.anr.anrTimeStr = self.anrLine.timeStr
            self.anr.anrTimeFloat = self.anrLine.timeFloat
            for line in self.lines:
                line.updateYear()
            return


    '''Reason: Broadcast of Intent { act=android.intent.action.TIME_TICK flg=0x50200014 (has extras) }'''
    broadcast_pattern = '^.*Broadcast of Intent { act=([\w|\.]+).*'
    '''Reason: executing service com.android.systemui/.light.LightEffectService'''
    service_pattern = '^.*executing service ([^ ]+).*'
    '''Reason: Input dispatching timed out (Waiting because no window has focus but there is a focused application that may eventually add a window when it finishes starting up.)'''
    input_pattern = '^.*Input dispatching timed out \((.*)\).*'

    def parseReason(self, reson: str):
        match = re.match(SystemAnr.broadcast_pattern, reson)
        if match:
            self.anr.setAnrBroadcast(match.group(1))
            return
        match = re.match(SystemAnr.service_pattern, reson)
        if match:
            self.anr.setAnrService(match.group(1))
            return
        match = re.match(SystemAnr.input_pattern, reson)
        if match:
            self.anr.setAnrInput(match.group(1))
            return

class SystemLog():

    def __init__(self, files, anrs: Anr, globalValues : GlobalValues, packageName: str = 'com.android.systemui'):
        self.globalValues = globalValues
        self.allAnr = anrs
        if files and len(files)>0:
            self.files = sorted(files,reverse=True)
            firstFile = self.files[0]
            self.files = self.files
            self.files.append(firstFile)
        else:
            self.files = []
        self.packageName = packageName

    def findAllAnr(self):
        systemAnr = None
        for file in self.files:
            with open(file, encoding=toolUtils.checkFileCode(file)) as mFile:
                linenum = 0
                while True:
                    linenum = linenum+1
                    line = mFile.readline()
                    if not line:
                        break
                    else:
                        line = line.strip()
                        if systemAnr == None:
                            temp = AnrLine(line, linenum, self.globalValues)
                            if temp.isAnrLine(self.packageName):
                                anr = Anr(temp)
                                systemAnr = SystemAnr(temp, anr)
                                anr.systemAnr = systemAnr
                                self.allAnr.append(anr)
                        else:
                            temp = LogLine(line, linenum, self.globalValues)
                            if temp.isLogLine and temp.tag == systemAnr.anrLine.tag:
                                systemAnr.addLine(temp, self.allAnr)
                            else:
                                systemAnr = None

        return self.allAnr