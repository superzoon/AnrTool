import re, io, sys, time
from Tool import *
from Tool import toolUtils

# sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf8')

TEST = False
DEF_MAX_DELAY_TIME = 1000
SHOW_LOG = False
def log(msg):
    if SHOW_LOG:
        print(msg)

class GlobalValues:
    def __init__(self):
        self.pidMap = dict()
        self.currentFile = ''
        self.showMessage = list()
        self.year = '2000'
        self.callbacks = dict()
        self.opener = None
        self.debug = True
        self.hungerBinders = dict()

    def setCallback(self,key:str, callback):
        if key:
            self.callbacks[key] = callback

    def removeCallback(self,key:str):
        if key and key in self.callback.keys():
            self.callbacks[key] = None

    def callbackFromKey(self, key:str, obj):
        if key and key in self.callbacks.keys():
            callback = self.callbacks[key]
            if callback:
                callback(obj)

GLOBAL_VALUES = GlobalValues()

class LogLine():
    '''
    10-11 07:10:00.024  1303  1303 V SettingsProvider: Notifying for 0: content://settings/system/next_alarm_formatted
    (timeStr)[\ ]+(pid)[\ ]+(tid)[\ ]+(level)[\ ]+(tag)?:\ (msg)
    '''
    pattern= '^([\d]{2}-[\d]{2}[\ ]+[\d|:|\.]+)[\ ]+([\d|\ ]+)[\ ]+([\d|\ ]+)[\ ]+([\w])[\ ](.*)'

    def __init__(self, line: str, linenum:int = 0, globalValues:GlobalValues = GLOBAL_VALUES):
        self.globalValues = globalValues
        self.line = line
        self.linenum = linenum
        match = re.match(LogLine.pattern, line+' ')
        if match:
            self.isLogLine = True
            self._timeStr_ = match.group(1)
            self.timeStr = self.globalValues.year + '-' +self._timeStr_
            self.timeFloat = toolUtils.getTimeFloat(self.globalValues.year + '-' + self._timeStr_ + '000')
            self.pid = int(match.group(2).strip())
            self.tid = int(match.group(3).strip())
            self.level = match.group(4).strip()
            other = match.group(5)
            index = other.index(': ') if other.__contains__(': ') else -1
            if index >= 0:
                self.tag = other[:index]
                self.msg = other[index+2:]
            else:
                self.tag = ''
                self.msg = other
            self.initOther()
        else:
            self.isLogLine = False
            print(line)

    def initOther(self):
        self.isFreezerd = False
        self.isIPCLine = False
        self.isGslMmapFailed = False
        self.isGslIoctlFailed = False
        self.isAnrCore = False
        self.file = ''
        self.isDelayLine = False
        self.delayFloat = 0;
        self.delayStartTimeStr = ''
        self.delayStartTimeFloat = ''
        self.threadName=''

    def updateYear(self):
        if self.isLogLine:
            self.timeStr = self.globalValues.year + '-' + self._timeStr_
            self.timeFloat = toolUtils.getTimeFloat(self.timeStr)

    # 比传入的行阻塞晚,阻塞起始时间在它行时间中间
    def isAfterDelay(self, other):
        if self.isDelayLine and other.isDelayLine:
            selfStartTime = self.timeFloat-self.delayFloat
            otherStartTime = other.timeFloat-other.delayFloat
            return (selfStartTime>otherStartTime) and (selfStartTime<=other.timeFloat)
        return False

    def findFontLine(self, all):
        temp = None
        for line in [line for line in all if line.isDelayLine]:
            if self.isAfterDelay(line):
                if not temp or temp.delayFloat >  line.delayFloat:
                    temp = line
        return temp

    # 比传入的行阻塞早，他行起始时间在改行的时间中间
    def isBeforeDelay(self, other):
        if self.isDelayLine and other.isDelayLine:
            selfStartTime = self.timeFloat-self.delayFloat
            otherStartTime = other.timeFloat-other.delayFloat
            return (self.timeFloat<other.timeFloat) and (self.timeFloat>= otherStartTime)
        return False

    def findBackLine(self, all):
        temp = None
        for line in [line for line in all if line.isDelayLine]:
            if self.isBeforeDelay(line):
                if not temp or temp.delayFloat <  line.delayFloat:
                    temp = line
        return temp

    def isDoubtLine(self, anr):
        return self.timeFloat < (60+ anr.anrTimeFloat) and  self.timeFloat > (anr.anrTimeFloat - 500)

    def addAnrMainLog(self, anr):
        if anr.pid == self.pid and self.timeFloat < (500+ anr.anrTimeFloat) and  self.timeFloat > (anr.anrTimeFloat - 1000):
            anr.main_logs.append(self)

    def addDelay(self, delay:float):
        self.isDelayLine = True
        self.delayFloat = delay
        self.delayStartTimeFloat = self.timeFloat-delay/1000
        self.delayStartTimeStr = str(toolUtils.getTimeStamp(self.delayStartTimeFloat))

class Anr():
    ANR_TYPE_UNKNOWN = 0
    ANR_TYPE_BROADCAST = 1
    ANR_TYPE_INPUT = 2
    ANR_TYPE_SERVICE = 3

    def __init__(self, line:LogLine):
        self.anrIn = line
        self.anrType = Anr.ANR_TYPE_UNKNOWN;
        self.anrPackageName = None
        self.pid:int = 0
        self.anrReason = None
        self.anrTimeStr:str = None
        self.anrTimeFloat:float = 0 #ms
        self.systemAnr = None
        self.anr_broadcast_action:str = None
        self.anr_class_name:str = None
        self.anr_input_msg:str = None
        self.anrCoreLine:LogLine = None
        self.anrCoreLines:LogLine = list()
        self.anrCoreReserveLine:LogLine = None
        self.main_logs:LogLine = list()
        self.font_main_log:LogLine = None
        self.back_main_log:LogLine = None

    def addMainLogBlock(self, allLine:LogLine):
        if len(self.main_logs) == 0:
            return None
        font_line = None
        back_line = None
        time_space = 0
        for line in self.main_logs:
            if not font_line:
                font_line = line
            else:
                back_line = line
                current_time_space = back_line.timeFloat - font_line.timeFloat
                if current_time_space > time_space and font_line.timeFloat < self.anrTimeFloat+1 and self.anrTimeFloat+1 < back_line.timeFloat:
                    time_space = current_time_space
                    self.font_main_log = font_line
                    self.back_main_log = back_line
                font_line = back_line

        if self.font_main_log and self.back_main_log:
            if not self.font_main_log in allLine:
                allLine.append(self.font_main_log)
            if not self.back_main_log in allLine:
                allLine.append(self.back_main_log)
            delay = self.back_main_log.timeFloat - self.font_main_log.timeFloat
            isMainAnr = False
            if self.anrType == Anr.ANR_TYPE_BROADCAST:
                isMainAnr = delay>=10
            elif self.anrType == Anr.ANR_TYPE_INPUT:
                isMainAnr = delay>=5
            elif self.anrType == Anr.ANR_TYPE_SERVICE:
                isMainAnr = delay>=20
            if isMainAnr:
                return [self.font_main_log, self.back_main_log]
            else:
                log(self.font_main_log.line)
                log(self.back_main_log.line)
                return None

    def computerAnrTime(self):
        if self.anrCoreLine and self.anrCoreLine.isDelayLine:
            self.anrTimeFloat = self.anrCoreLine.delayStartTimeFloat
            self.anrTimeStr = self.anrCoreLine.delayStartTimeStr
        elif self.anrCoreReserveLine and self.anrCoreReserveLine.isDelayLine:
            self.anrTimeFloat = self.anrCoreReserveLine.delayStartTimeFloat
            self.anrTimeStr = self.anrCoreReserveLine.delayStartTimeStr


    def findAllFontLine(self, line:LogLine, allLine: LogLine):
        fontLine = line.findFontLine(allLine)
        if fontLine and len(self.anrCoreLines) < 6:
            if not fontLine in self.anrCoreLines:
                self.anrCoreLines.append(fontLine)
            self.findAllFontLine(fontLine, allLine)

    def findAllCoreLine(self, allLine: LogLine):
        if self.anrCoreLine:
            self.anrCoreLines.append(self.anrCoreLine)
            backLine = self.anrCoreLine.findBackLine(allLine)
            if backLine and not backLine in self.anrCoreLines:
                self.anrCoreLines.append(backLine)
            self.findAllFontLine(self.anrCoreLine, allLine)
            self.anrCoreLines.sort(key=lambda line: line.timeFloat)

    def setCoreLine(self, line: LogLine):
        self.anrCoreLine = line

    def setCoreLineReserve(self, line: LogLine):
        self.anrCoreReserveLine = line

    def setAnrBroadcast(self, action:str):
        self.anrType = Anr.ANR_TYPE_BROADCAST
        self.anr_broadcast_action = action

    def setAnrService(self, class_name:str):
        self.anrType = Anr.ANR_TYPE_SERVICE
        self.anr_class_name = class_name

    def setAnrInput(self, input_msg:str):
        self.anrType = Anr.ANR_TYPE_INPUT
        self.anr_input_msg = input_msg


