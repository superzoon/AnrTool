import sys, re, os, datetime, configparser, tarfile, zipfile, socket, uuid
from os import (walk, path, listdir, popen, remove, rename, makedirs, chdir)
from os.path import (realpath, isdir, isfile, sep, dirname, abspath, exists, basename, getsize)
from shutil import (copytree, rmtree, copyfile, move)
from sys import argv
from zipfile import ZipFile
from _io import TextIOWrapper
from Tool import toolUtils
from Tool.toolUtils import *
from Tool.tracesLog import *
from Tool import Anr,GlobalValues, log, logUtils
from Tool.systemLog import *
from Tool import DEF_MAX_DELAY_TIME

DEFAULT_PACKAGE = 'com.android.systemui'
def parseSurfaceFlinger(allAnr :Anr, allLine:LogLine, line:LogLine):
    if not line.globalValues.pidMap.__contains__(line.pid):
        line.globalValues.pidMap[line.pid] = line.tag

# '09-26 02:04:14.363   928   928 E         : freezerd, set_thread_freeze_state, freeze=0, pid=29086, num=139'
def parseNoTag(allAnr :Anr, allLine:LogLine, line:LogLine):
    match = re.match('freezerd, set_thread_freeze_state.*\ pid=([\d]+)[^\d].*', line.msg)
    isParsed = False
    if match:
        pid = int(match.group(1))
        for anr in allAnr:
            if anr.pid == pid:
                line.isFreezerd = True
                line.isFreezerdPid = pid
                allLine.append(line)
                isParsed = True
                break
    return isParsed

# IPCThreadState: IPCThreadState, binder thread pool (4 threads) starved for 9276 ms
# IPCThreadState: IPCThreadState, Waiting for thread to be free. mExecutingThreadsCount=32 mMaxThreads=31
#'IPCThreadState: set_thread_freeze_state, freeze=1, pid=29086, num=152'
pattern_ipc1 = '^.*IPCThreadState, binder thread pool.* ([\d|\.]+)[\ ]?ms.*'
pattern_ipc2 = '^.*IPCThreadState, Waiting.*mExecutingThreadsCount=([\d]+) mMaxThreads=([\d]+).*'
pattern_ipc3 = '^.*set_thread_freeze_state.*\ pid=([\d]+)[^\d].*'
def parseIPCThreadState(allAnr :Anr, allLine:LogLine, line:LogLine):
    isParsed = False
    line.isIPCLine = True
    match = re.match(pattern_ipc1, line.msg)
    if match:
        delay = float(match.group(1))
        for anr in allAnr:
            log(str(line.isDoubtLine(anr))+'  '+str(anr.anrTimeStr)+'-'+str(line.timeStr))
            if line.isDoubtLine(anr):
                line.addDelay(delay)
                allLine.append(line)
                isParsed = True
                break
    if not isParsed and re.match(pattern_ipc2, line.msg):
        addLine = True
        lastLine = allLine[-1] if len(allLine)>0 else None
        if lastLine != None and lastLine.isIPCLine:
            if (line.timeFloat - lastLine.timeFloat) < 3:
                addLine = False
                isParsed = True
        if addLine:
            for anr in allAnr:
                if line.isDoubtLine(anr):
                    allLine.append(line)
                    isParsed = True
                    break
    if not isParsed:
        match = re.match(pattern_ipc3, line.msg)
        if match:
            pid = int(match.group(1))
            for anr in allAnr:
                if anr.pid == pid:
                    line.isFreezerd = True
                    line.isFreezerdPid = pid
                    allLine.append(line)
                    isParsed = True
                    break

    return isParsed

# Slow dispatch took 12050ms main h=com.android.server.job.JobSchedulerService$JobHandler c=null m=1
pattern_loop = '.*Slow dispatch took ([\d|\.]+)ms .*'
def parseLooper(allAnr :Anr, allLine:LogLine, line:LogLine):
    match = re.match(pattern_loop, line.msg)
    isParsed = False
    if match:
        delay = float(match.group(1))
        for anr in allAnr:
            if delay > DEF_MAX_DELAY_TIME and line.isDoubtLine(anr):
                line.addDelay(delay)
                allLine.append(line)
                isParsed = True
                break
    return isParsed

# kgsl-3d0: |kgsl_get_unmapped_area| _get_svm_area: pid 29268 mmap_base f643b000 addr 0 pgoff 35de len 8716288 failed error -12
pattern_kgsl = '^.*kgsl_get_unmapped_area.* failed error ([-|\d]+).*'
def parseKgsl(allAnr :Anr, allLine:LogLine, line:LogLine):
    match = re.match(pattern_kgsl, line.msg)
    isParsed = False
    if match:
        for anr in allAnr:
            if line.isDoubtLine(anr):
                allLine.append(line)
                isParsed = True
                break
    return isParsed

# content_update_sample: [content://com.android.contacts/data,insert, , 23,  com.example.sendmessagetest,   5]
pattern_content_update = '^.*,[\ ]*([\d]*)[\ ]*,[\ ]*([^,]*)[\ ]*,[\ ]*([\d]+)][\ ]*'
def parseQuery(allAnr :Anr, allLine:LogLine, line:LogLine):
    match = re.match(pattern_content_update, line.msg)
    isParsed = False
    if match and int(match.group(1)) > DEF_MAX_DELAY_TIME:
        delay = float(match.group(1))
        for anr in allAnr:
            if line.isDoubtLine(anr):
                line.addDelay(delay)
                allLine.append(line)
                isParsed = True
                break
    return isParsed

# dvm_lock_sample: [com.android.settings, 1, (main) , (23),  ManageApplication.java, 1317,  ApplicationState.java, 323 , 5]
pattern_lock = '^.*,[\ ]*([^,]*)[\ ]*,[\ ]*([\d]*)[\ ]*,[\ ]*([^,]*)[\ ]*,[\ ]*([\d]*)[\ ]*,[\ ]*([^,]*)[\ ]*,[\ ]*([\d]*)[\ ]*,[\ ]*([\d]+)][\ ]*'
def parseLock(allAnr :Anr, allLine:LogLine, line:LogLine):
    match = re.match(pattern_lock, line.msg)
    isParsed = False
    if match and int(match.group(2))>DEF_MAX_DELAY_TIME:
        line.threadName = match.group(1)
        delay = float(match.group(2))
        for anr in allAnr:
            if line.isDoubtLine(anr):
                line.addDelay(delay)
                allLine.append(line)
                isParsed = True
                break
    return isParsed

# am_activity_launch_time: [0, 185694486, cn.nubia.launcher/com.android.launcher3.Launcher,  257,  257]
pattern_launcher = '^.*[\ ]*([\d]+),[\ ]*([\d]+)]'
def parseLauncher(allAnr :Anr, allLine:LogLine, line:LogLine):
    match = re.match(pattern_launcher, line.msg)
    isParsed = False
    if match and int(match.group(1))>DEF_MAX_DELAY_TIME:
        delay = float(match.group(1))
        for anr in allAnr:
            if line.isDoubtLine(anr):
                line.addDelay(delay)
                allLine.append(line)
                isParsed = True
                break
    return isParsed

# binder_sample: [ android.app.IActivityManager,  8,   227,    com.android.phone,    45]
pattern_binder = '^.*,[\ ]*([\d]*)[\ ]*,[\ ]*([^,]*)[\ ]*,[\ ]*([\d]+)][\ ]*'
def parseBinder(allAnr :Anr, allLine:LogLine, line:LogLine):
    match = re.match(pattern_binder, line.msg)
    isParsed = False
    if match and int(match.group(1))>DEF_MAX_DELAY_TIME:
        delay = float(match.group(1))
        for anr in allAnr:
            if line.isDoubtLine(anr):
                line.addDelay(delay)
                allLine.append(line)
                isParsed = True
                break
    return isParsed


pattern_vold = '^.*Trimmed.* ([\d]+)ms.*'
def parseVold(allAnr :Anr, allLine:LogLine, line:LogLine):
    if not line.globalValues.pidMap.__contains__(line.pid):
        line.globalValues.pidMap[line.pid] = 'vold'
    match = re.match(pattern_vold, line.msg)
    if match and int(match.group(1))>10000:
        delay = float(match.group(1))
        line.addDelay(delay)
        allLine.append(line)
    return True

def parseKeyguardViewMediator(allAnr :Anr, allLine:LogLine, line:LogLine):
    if not line.globalValues.pidMap.__contains__(line.pid):
        line.globalValues.pidMap[line.pid] = 'systemui'
    if line.msg.startswith('handleHide') or line.msg.startswith('handleShow')\
            or line.msg.startswith('onStartedGoingToSleep') or line.msg.startswith('onFinishedGoingToSleep')\
            or line.msg.startswith('onStartedWakingUp'):
        for anr in allAnr:
            if line.isDoubtLine(anr):
                allLine.append(line)
                break
    return True


def parseAdreno(allAnr :Anr, allLine:LogLine, line:LogLine):
    isParsed = False

    lastLine = allLine[-6:] if len(allLine) > 6 else None
    lastHasFailed = False
    if line.msg.__contains__('mmap failed'):
        if lastLine:
            for i in lastLine:
                if i.msg.__contains__('mmap failed') and i.timeFloat - line.timeFloat < 2:
                    lastHasFailed = True
                    break
    elif line.msg.__contains__('ioctl failed'):
        if lastLine:
            for i in lastLine:
                if i.msg.__contains__('ioctl failed') and i.timeFloat - line.timeFloat < 2:
                    lastHasFailed = True
                    break
    if not lastHasFailed:
        for anr in allAnr:
            if line.isDoubtLine(anr):
                allLine.append(line)
                isParsed = True
                break
    return isParsed

# 09-22 04:59:35.929  1778  1841 W ActivityManager: Timeout executing service: ServiceRecord{9312bc1 u0 com.android.systemui/.light.LightEffectService}
# executing service com.android.systemui/.light.LightEffectService
pattern_executing_service = '^.*Timeout executing service.*{[\w|\d]+ [\w|\d]+ ([\w|\d|\/|\.]+)}'
def parseActivityManager(allAnr :Anr, allLine:LogLine, line:LogLine, package_name=DEFAULT_PACKAGE):
    match = re.match(pattern_executing_service, line.msg)
    if match:
        if package_name == package_name:
            delay = 20*1000#前台服务
        else :
            delay = 200*1000#后台服务
        className = match.group(1).strip()
        line.addDelay(delay)
        myAnr:Anr = None
        for anr in [anr for anr in allAnr if anr.anrType == Anr.ANR_TYPE_SERVICE and anr.anr_class_name == className and anr.anrIn.timeFloat > line.timeFloat]:
            if not myAnr:
                myAnr = anr
            elif anr.anrIn.timeFloat < myAnr.anrIn.timeFloat:
                myAnr = anr
        if myAnr:
            oldLine = myAnr.anrCoreLine
            if not (oldLine and oldLine.timeFloat > line.timeFloat):
                if oldLine:
                    oldLine.isAnrCore = False
                myAnr.setCoreLine(line)
                line.isAnrCore = True
                line.file = str(line.globalValues.currentFile)

        allLine.append(line)
    return True

'''BroadcastQueue: Timeout of broadcast BroadcastRecord{2afa62c u-1 android.intent.action.TIME_TICK} - receiver=android.os.BinderProxy@182e848, started 11845ms ago'''
pattern_broadcast = '.*Timeout of broadcast.* ([^ ]+)}.*started ([\d|\.]+)ms ago.*'
def parseBroadcastQueue(allAnr :Anr, allLine:LogLine, line:LogLine):
    math = re.match(pattern_broadcast, line.msg)
    isParsed = False
    # 前台广播10s，后台广播60s
    if math:
        action = math.group(1).strip()
        delayStr = math.group(2).strip()
        delay = float(delayStr)
        line.addDelay(delay)
        myAnr:Anr = None
        for anr in [anr for anr in allAnr if anr.anrType == Anr.ANR_TYPE_BROADCAST and anr.anr_broadcast_action == action and anr.anrIn.timeFloat > line.timeFloat]:
            if not myAnr:
                myAnr = anr
            elif anr.anrIn.timeFloat < myAnr.anrIn.timeFloat:
                myAnr = anr

        if myAnr:
            oldLine = myAnr.anrCoreLine
            if not (oldLine and oldLine.timeFloat > line.timeFloat):
                if oldLine:
                    oldLine.isAnrCore = False
                myAnr.setCoreLine(line)
                line.isAnrCore = True
                line.file = str(line.globalValues.currentFile)
        allLine.append(line)
        isParsed = True
    return isParsed

pattern_input = '^.*Application is not responding.*Reason:(.*)'
pattern_input1 = '^.*Application is not responding.*It has been ([\d|\.]+)ms since event.*'
pattern_input2 = '^.*Application is not responding.*It has been .*Wait queue head age: ([\d|\.]+)ms.'
pattern_input3 = '^.*Application is not responding.*Reason:.*age: ([\d|\.]+)ms.*'
def parseInputDispatcher(allAnr :Anr, allLine:LogLine, line:LogLine):
    if not line.globalValues.pidMap.__contains__(line.pid):
        line.globalValues.pidMap[line.pid] = 'system_server'
    isParsed = False
    delay = 5000
    reason = None
    match = re.match(pattern_input, line.msg)
    if match:
        reason = match.group(1)
    match = re.match(pattern_input1, line.msg)
    if match:
        match = re.match(pattern_input2, line.msg)
    if not match:
        match = re.match(pattern_input3, line.msg)
    if match:
        delayStr = match.group(1)
        delay = float(delayStr)
    if reason:
        isParsed = True
        line.addDelay(delay)
        allLine.append(line)

        myAnr:Anr = None
        for anr in [anr for anr in allAnr if anr.anrType == Anr.ANR_TYPE_INPUT and anr.anr_input_msg in line.msg and anr.anrIn.timeFloat > line.timeFloat]:
            if not myAnr:
                myAnr = anr
            elif anr.anrIn.timeFloat < myAnr.anrIn.timeFloat:
                myAnr = anr

        if myAnr:
            oldLine = myAnr.anrCoreLine
            if not (oldLine and oldLine.timeFloat > line.timeFloat):
                if oldLine:
                    oldLine.isAnrCore = False
                myAnr.setCoreLine(line)
                line.isAnrCore = True
                line.file = str(line.globalValues.currentFile)
    return isParsed


pattern_window_manager1 = '^.*Input event dispatching timed out.*Reason:(.*)'
pattern_window_manager2 = '^.*Input event dispatching timed out.* ([\d|\.]+)ms ago.*'
pattern_window_manager3 = '^.*Input event dispatching timed out.* Wait queue.* ([\d|\.]+)ms.*'
def parseWindowManager(allAnr :Anr, allLine:LogLine, line:LogLine):
    delay = 5000
    match = re.match(pattern_window_manager1, line.msg)
    if match:
        reason = match.group(1).strip()
        match = None
        match1 = re.match(pattern_window_manager2, line.msg)
        if match1:
            match = match1
        match2 = re.match(pattern_window_manager3, line.msg)
        if match2:
            match = match2
        if match:
            delay = float(match.group(1))
            line.addDelay(delay)
        allLine.append(line)

        myAnr:Anr = None
        for anr in [anr for anr in allAnr if anr.anrType == Anr.ANR_TYPE_INPUT and reason in anr.anrReason and anr.anrIn.timeFloat > line.timeFloat]:
            if not myAnr:
                myAnr = anr
            elif anr.anrIn.timeFloat < myAnr.anrIn.timeFloat:
                myAnr = anr
        if myAnr:
            oldLine = myAnr.anrCoreReserveLine
            if not (oldLine and oldLine.timeFloat > line.timeFloat):
                myAnr.setCoreLineReserve(line)
                line.file = str(line.globalValues.currentFile)
    return True

pattern_gl = '^.*\ duration=([\d]+)ms;.*'
def parseOpenGLRenderer(allAnr :Anr, allLine:LogLine, line:LogLine):
    match = re.match(pattern_gl, line.msg)
    if match :
        delay = float(match.group(1))
        line.addDelay(delay)
        if (delay >DEF_MAX_DELAY_TIME):
            allLine.append(line)

    return True

pattern_nubialog = '^.*\ delay=([\d]+)ms\ .*'
pattern_nubialog_draw = '.*draw takes ([\d|\.]+) ms:.*'
def parseNubiaLog(allAnr :Anr, allLine:LogLine, line:LogLine):
    match = re.match(pattern_nubialog, line.msg)
    isParsed = False
    if not match:
        match = re.match(pattern_nubialog_draw, line.msg)
    if match:
        delay = float(match.group(1))
        line.addDelay(delay)
        if delay > DEF_MAX_DELAY_TIME:
            for anr in allAnr:
                if line.isDoubtLine(anr):
                    allLine.append(line)
                    isParsed = True
                    break
    return isParsed

def parseLine(allAnr :Anr, allLine:LogLine, line:LogLine, packageName = DEFAULT_PACKAGE):
    isParsed = False
    tag = line.tag.lower()
    #根据log的tag进行解析
    ##########################ANR 核心 log###########################
    #服务执行超时
    if not isParsed and tag.strip() == 'ActivityManager'.strip().lower():
        isParsed = parseActivityManager(allAnr, allLine, line, packageName)
    #输入时间超时
    if not isParsed and tag == 'InputDispatcher'.lower():
        isParsed = parseInputDispatcher(allAnr, allLine, line)
    #广播超时
    if not isParsed and tag == 'BroadcastQueue'.lower():
        isParsed = parseBroadcastQueue(allAnr, allLine, line)
    ##########################内存问题 log###########################
    #kgsl内存问题
    if not isParsed and tag.strip().startswith('kgsl-'):
        isParsed = parseKgsl(allAnr, allLine, line)
    #gsl内存问题
    if not isParsed and tag == 'Adreno-GSL'.lower():
        isParsed = parseAdreno(allAnr, allLine, line)
    ##########################卡顿问题 log###########################
    #nubia 自己加的延迟信息
    if not isParsed and tag == 'nubialog'.lower():
        isParsed = parseNubiaLog(allAnr, allLine, line)
    #gl 卡顿信息
    if not isParsed and tag == 'OpenGLRenderer'.lower():
        isParsed = parseOpenGLRenderer(allAnr, allLine, line)
    #锁屏是否显示
    if not isParsed and tag == 'KeyguardViewMediator'.lower():
        isParsed = parseKeyguardViewMediator(allAnr, allLine, line)
    #vold磁盘耗时
    if not isParsed and tag.strip() == 'vold    '.strip().lower():
        isParsed = parseVold(allAnr, allLine, line)
    #binder超时
    if not isParsed and tag.strip() == 'binder_sample'.strip().lower():
        isParsed = parseBinder(allAnr, allLine, line)
    #查询超时
    if not isParsed and tag.strip() == 'content_query_sample'.strip().lower():
        isParsed = parseQuery(allAnr, allLine, line)
    #锁超时
    if not isParsed and tag.strip() == 'dvm_lock_sample'.strip().lower():
        isParsed = parseLock(allAnr, allLine, line)
    #启动activity超时
    if not isParsed and tag.strip() == 'am_activity_launch_time'.strip().lower():
        isParsed = parseLauncher(allAnr, allLine, line)
    #looper缓慢的派遣
    if not isParsed and tag.strip().lower() == 'Looper'.strip().lower():
        isParsed = parseLooper(allAnr, allLine, line)
    #input回应超时
    if not isParsed and tag.strip() == 'WindowManager'.strip().lower():
        isParsed = parseWindowManager(allAnr, allLine, line)
    ##########################线程池 log###########################
    #线程池满
    if not isParsed and tag.strip() == 'IPCThreadState'.strip().lower():
        isParsed = parseIPCThreadState(allAnr, allLine, line)
    ##########################pid log###########################
    #保存SF的pid
    if not isParsed and tag.strip() == 'SurfaceFlinger'.strip().lower():
        isParsed = parseSurfaceFlinger(allAnr, allLine, line)

    ##########################pid log###########################
    #保存SF的pid
    if not isParsed and len(tag.strip()) == 0:
        isParsed = parseNoTag(allAnr, allLine, line)


    ##########################解析完成###########################
    #如果有解析则打印该行
    if isParsed:
        log(line.line)
    #有延时信息保存该行
    pattern_delay = '.*delay.*([\d]+)[\ ]*ms.*'
    if not isParsed:
        math = re.match(pattern_delay,line.msg)
        if math and int(math.group(1)) > DEF_MAX_DELAY_TIME:
            allLine.append(line)

def parseLogDir(destDir:str, resonFile:TextIOWrapper, packageName:str=DEFAULT_PACKAGE):
    #保存所有公共变量
    globalValues = GlobalValues()
    #获取目录下的所有文件
    allFiles = toolUtils.getAllFileName(destDir)
    #获取所有的 system log文件
    systemFiles = [file for file in allFiles if 'system.txt' in file]
    systemFiles.sort(reverse = True)
    #获取所有的 events log文件
    eventFiles = [file for file in allFiles if 'events.txt' in file]
    eventFiles.sort(reverse = True)
    #获取所有的 main log文件
    mainFiles = [file for file in allFiles if 'main.txt' in file]
    mainFiles.sort(reverse = True)
    #获取所有的 radio log文件
    radioFiles = [file for file in allFiles if 'radio.txt' in file]
    radioFiles.sort(reverse = True)
    #获取所有的 kernel log文件
    kernelFiles = [file for file in allFiles if 'kernel.txt' in file]
    kernelFiles.sort(reverse = True)
    #获取所有的 crash log文件
    crashFiles = [file for file in allFiles if 'crash.txt' in file]
    #获取所有的 anr trace文件
    anrFiles = [file for file in allFiles if sep.join(['anr','anr_'+str(packageName)]) in file]
    anrFiles.sort(reverse = False)
    #获取所有的 system.prop文件
    propFiles = [file for file in allFiles if 'system.prop' in file]
    #解析prop文件获取手机信息
    propMsg = toolUtils.parseProp(propFiles)

    #添加所有需要需要解析的log文件
    parseFiles = []
    for f in systemFiles:
        parseFiles.append(f)
    for f in eventFiles:
        parseFiles.append(f)
    for f in mainFiles:
        parseFiles.append(f)
    for f in radioFiles:
        parseFiles.append(f)
    for f in kernelFiles:
        parseFiles.append(f)
    #用于保存重要的信息行LogLine对象
    allLine = []
    #用于保存所有的Anr对象
    allAnr = []
    # 从systemui解析有多少个anr
    systemLog = SystemLog(systemFiles, allAnr, globalValues, packageName)
    systemLog.findAllAnr()
    #解析所有的anr trace
    mainStacks = list()
    blockStacks = dict()
    pattern='anr_[\w|\.]+_([\d]+)_([\d|-]+)'
    parseTracesPids = list()
    tracesLogs = []
    for file in anrFiles:
        match = re.match(pattern,  basename(file))
        if match:
            pid = match.group(1)
            if not pid in  parseTracesPids:
                parseTracesPids.append(pid)
                willParser = False
                for anr in allAnr:
                    if str(pid) == str(anr.pid):
                        willParser = True
                if willParser:
                    log(file)
                    trace = TracesLog(file, globalValues, packageName)
                    trace.parser()
                    tracesLogs.append(trace)
                    stack:ThreadStack = trace.getMainStack()
                    #如果堆栈出现两次相同则加入到数列中
                    if stack != None:
                        mainStacks.append(stack)
    #最后一行main log，用于验证main log是否包含anr时间
    mainLine = None
    #保存最后发生anr的时间，当mainLine时间小于anr时间则main log不全
    anrTimeFloat = 0;
    for file in parseFiles:
        log('--' + file + '--')
        with open(file, encoding=toolUtils.checkFileCode(file)) as mFile:
            #全局变量，当前解析的文件
            globalValues.currentFile = file
            linenum = 0
            #是否在解析main log
            isMainLine = True if ('main.txt' in file) else False
            while True:
                line = mFile.readline()
                linenum = linenum + 1
                if not line:
                    break
                else:
                    line = line.strip()
                    temp = LogLine(line, linenum, globalValues)
                    if temp.isLogLine :
                        #保存最后一行main log
                        if isMainLine:
                            if (mainLine == None or temp.timeFloat > mainLine.timeFloat):
                                mainLine = temp;
                            if temp.pid == temp.tid:
                                for anr in allAnr:
                                    temp.addAnrMainLog(anr)
                        #解析该行
                        parseLine(allAnr, allLine, temp, packageName)

    log('####################start write######################')
    #将手机的信息写入到文件

    for (key, value) in propMsg.items():
        temp = "{}:{}\n".format(key, value)
        globalValues.showMessage.append(temp)
        resonFile.writelines(temp)
    temp = '\n'
    globalValues.showMessage.append(temp)
    resonFile.writelines(temp)
    #讲对应的am anr添加到主要信息中
    for anr in allAnr:
        if not anr.anrCoreLine and anr.anrCoreReserveLine:
            anr.setCoreLine(anr.anrCoreReserveLine)
        anr.computerAnrTime()
        anr.findAllCoreLine(allLine)
        if len(anr.systemAnr.lines)>=8:
            for line in anr.systemAnr.lines[0:8]:
                allLine.append(line)

    #保存发生anr的pid，从堆栈trace中查找对应的pid
    pids = []
    #将所有的anr信息输出到文件
    for anr in allAnr:
        pids.append(anr.pid)
        temp = "pid:"+str(anr.pid)+'\n'+"发生时间:"+str(anr.anrTimeStr)+'\n'+"发生原因:"+anr.anrReason+'\n\n'
        globalValues.showMessage.append(temp)
        resonFile.writelines(temp)
        mainMsg:[] = anr.addMainLogBlock(allLine)
        if mainMsg:
            font = mainMsg[0]
            back = mainMsg[1]
            temp = ('主线程阻塞:{}  ==>  {}\n\t{}\n\t{}'.format(font.timeStr, back.timeStr,  font.line, back.line))+'\n\n'
            globalValues.showMessage.append(temp)
            resonFile.writelines(temp)

        startDelayLine = anr.anrCoreLine
        key = lambda line:line.delayStartTimeFloat
        if anr.anrCoreLines:
            temp = '核心log:\n'
            globalValues.showMessage.append(temp)
            resonFile.writelines(temp)
            delayLines = [delayLine for delayLine in anr.anrCoreLines if delayLine.isDelayLine]
            for line in delayLines:
                temp ='\t'+line.line+'\n'
                globalValues.showMessage.append(temp)
                resonFile.writelines(temp)
                temp = "\t\tstartTime:{}\n".format(line.delayStartTimeStr)
                globalValues.showMessage.append(temp)
                resonFile.writelines(temp)
            delayLines = sorted(delayLines, key=key, reverse=True)
            for line in delayLines:
                if startDelayLine==None or (line.delayStartTimeFloat < startDelayLine.delayStartTimeFloat and line.timeFloat > startDelayLine.delayStartTimeFloat):
                    startDelayLine = line
            temp = '\n'
            globalValues.showMessage.append(temp)
            resonFile.writelines(temp)

            # 输出阻塞的堆栈
        for stack in [stack for item in mainStacks if str(item.pid) == str(anr.pid)]:
            if stack:
                temp = '\t\nmain pid='+str(stack.pid)+' time='+str(stack.pidStack.time)+' java栈:' + '\t\n\t' + str(stack.top) + '\n'
                globalValues.showMessage.append(temp)
                resonFile.writelines(temp)
                temp = '\t\t' + '\n\t\t'.join(stack.javaStacks if len(stack.javaStacks) < 10 else stack.javaStacks[0:10])
                globalValues.showMessage.append(temp)
                resonFile.writelines(temp)
                temp = '\n\n'
                globalValues.showMessage.append(temp)
                resonFile.writelines(temp)

        if startDelayLine:
            temp = '起始阻塞log:\n'+'\t'+startDelayLine.line+"\n\t\tstartTime:{}\n".format(startDelayLine.delayStartTimeStr)+'\n'
            globalValues.showMessage.append(temp)
            resonFile.writelines(temp)

        log(anr.anrTimeStr)
        log(anr.anrTimeFloat)
        #获取最后发生anr的时间，用于推断main log是否全
        if anr.anrTimeFloat>anrTimeFloat:
            anrTimeFloat = anr.anrTimeFloat
        log(anr.anrReason)
    # 将主要信息按时间排序
    allLine.sort(key=lambda line: line.timeFloat)
    #判断是否main log不足
    if mainLine!=None and (mainLine.timeFloat < anrTimeFloat):
        log("main log 不足")
        temp ="main log 不足 time:" + str(toolUtils.getTimeStamp(mainLine.timeFloat)) + '\n\n'
        globalValues.showMessage.append(temp)
        resonFile.writelines(temp)
    #输出pid和线程名称到文件
    if len(globalValues.pidMap)>0:
        temp ="线程名称:\n\t"
        resonFile.writelines(temp)
        globalValues.showMessage.append(temp)
        count = 0
        temp = ''
        for key in sorted(globalValues.pidMap.keys()):
            temp = temp + 'pid={} : name={},\t\t'.format(key, globalValues.pidMap[key])
            count = count+1
            if len(temp)>80:
                temp = temp+'\n\t'
                globalValues.showMessage.append(temp)
                resonFile.writelines(temp)
                temp = ''
        if len(temp)>0:
            resonFile.writelines(temp)
            globalValues.showMessage.append(temp)
    #查找最异常binder
    hungerBinder = dict()
    maxBinderNum = 0
    maxBinder = ''
    for key, value in globalValues.hungerBinders.items():
        newKey = '{}:{}'.format(key.split(':')[0], value.split(':')[0])
        if newKey in hungerBinder.keys():
            hungerBinder[newKey] = hungerBinder[newKey] + 1
        else:
            hungerBinder[newKey] = 1
        if maxBinderNum < hungerBinder[newKey]:
            maxBinder = newKey
            maxBinderNum = hungerBinder[newKey]

    if hungerBinder:
        temp = '\n\ndump时候异常binder 等待binder共有{}个：'.format(len(globalValues.hungerBinders))
        for key, value in hungerBinder.items():
            if maxBinderNum == value or value > 3 or len(hungerBinder)==1:
                pids = key.split(':')
                fromPid = int(pids[0])
                toPid = int(pids[1])
                temp = temp+'\n\t其中 binder form {} to {}, 数量 = {}。'.format(fromPid, toPid, value)

                if fromPid in globalValues.pidMap and toPid in globalValues.pidMap:
                    temp = temp+'\n\t\tfrom name={}, to name={}'.format(globalValues.pidMap[fromPid],globalValues.pidMap[toPid])

        globalValues.showMessage.append(temp)
        resonFile.writelines(temp)

    if len(tracesLogs) > 0 and len(tracesLogs[0].suspiciousStack)>0:
        temp = '\n\n阻塞线程\n'
        globalValues.showMessage.append(temp)
        resonFile.writelines(temp)
        for tracesLog in tracesLogs:
            temp = '\n'
            for title, stack  in tracesLog.suspiciousStack.items():
                pidStack: PidStack = stack
                temp = '{}\t{}\n\t\t{}\n'.format(temp, title,'\n\t\t'.join(pidStack.javaStacks[:10]))
                globalValues.showMessage.append(temp)
                resonFile.writelines(temp)

    temp = '\n'
    globalValues.showMessage.append(temp)
    resonFile.writelines(temp)
    log("len ==  "+str(len(allLine)))
    #未找到相关log
    if(len(allLine)) == 0 and mainLine!=None:
        log(mainLine.timeFloat)
        log(anrTimeFloat)
    else:
        #输出所有的分析行信息到文件
        resonFile.writelines("\n关键log:\n")
        for line in allLine:
            if line.isAnrCore:
                start = len(dirname(dirname(dirname(destDir))))+1
                resonFile.writelines("\n  My Anr core: in file {} -> line={}\n\n".format(line.file[start:], line.linenum))
            resonFile.writelines("\t{}\n".format(line.line.strip()))
            if line.isDelayLine:
                resonFile.writelines("\t\tstartTime:{}\n".format(line.delayStartTimeStr))
        resonFile.writelines("\n")

    # 判断是否有anr
    if len(allAnr) == 0:
        temp = ("{}未找到anr报错信息\n".format(basename(destDir)))
        logUtils.info(temp)
        globalValues.showMessage.append(temp)
        resonFile.writelines(temp)
    log('####################end write######################')
    return globalValues

def parseZipLog(fileName, resonFile:TextIOWrapper, packageName:str=DEFAULT_PACKAGE, removeDir = True, callbackMsg = None):
    log("parLogZip : fileName={},  packageName={}".format(fileName, packageName))
    callbackMsg('正在解析{}'.format(basename(fileName)))
    #如果不是pid文件则不解析
    if not zipfile.is_zipfile(fileName):
        exit(-1)
    #获取文件路径和文件全名
    (filepath, tempfilename) = os.path.split(fileName)
    #获取文件名和文件后缀
    (name, extension) = os.path.splitext(tempfilename)
    #获取解压的文件路径
    tempDir = sep.join([dirname(fileName), name])
    #解压的文件路径如果存在就删除
    if isdir(tempDir):
        rmtree(tempDir)
    #创建解压路径
    makedirs(tempDir)
    #解压zip文件到指定路径
    toolUtils.unzip_single(fileName, tempDir)
    #解析刚刚解压的文件
    globalValues:GlobalValues =parseLogDir(tempDir, resonFile, packageName)
    #删除刚刚解压的临时文件夹
    if removeDir:
        rmtree(tempDir)
    return globalValues

def parserZipLogDir(foldPath, packageName =DEFAULT_PACKAGE, removeDir = True, callbackMsg = None):
    #打印需要解析的路径
    msg = '--parserZipLogDir thread={} foldPath={}'.format(current_thread().getName(), foldPath)
    logUtils.info(msg)
    #获取该路径下所有的zip文件
    allZips = [file for file in toolUtils.getAllFileName(foldPath) if zipfile.is_zipfile(file)]
    #创建该路径下的reason文件，用于保存解析结果
    resonFile = open(file=sep.join([foldPath, '{}.txt'.format(basename(foldPath))]), mode='w', encoding='utf-8')
    #用于标记在第几个zip
    zipPoint = 0
    #解析每一个zip
    globalValuesList:GlobalValues = list()
    for zipFile in allZips:
        zipPoint = zipPoint + 1
        #在文件输出解析zip的名称
        resonFile.writelines('{}.{}\n\n'.format(str(zipPoint), abspath(zipFile)[len(dirname(foldPath)) + 1:-4]))
        #解析zip log
        globalValuesList.append(parseZipLog(zipFile, resonFile, packageName = packageName, removeDir=removeDir, callbackMsg=callbackMsg))
        #解析完后换行
        resonFile.writelines('\n\n')
    resonFile.writelines("\n\n 解析有误或者有建议请邮箱xiao.liang@nubia.com(肖良)")
    #将解析的内容写入到文件
    resonFile.flush()
    #关闭文件流
    resonFile.close()
    return globalValuesList

if __name__ == '__main__':
    start = time.clock()
    #     D:\workspace\整机monkey
    # D:\workspace\anr_papser\log\LOG-36743
    current = 'NX627JV2B-1080'
    current = ''
    current = sep.join(['anr_papser','test'])
    current = sep.join(['anr_papser','papser','LOG-495539','NX629J_Z0_CN_VLF0P_V227','YYeXlc.RgwXbXQ.zip'])
    current = sep.join(['anr_papser','papser','LOG-494778'])
    if len(current) > 0:
        papserPath = sep.join(['D:','workspace',current])
        if isfile(papserPath):
            foldPath = dirname(abspath(papserPath))
            resonFile = open(file=sep.join([foldPath, basename(foldPath)]), mode='w', encoding='utf-8')
            resonFile.writelines('{}.{}\n\n'.format(str(1), abspath(papserPath)[len(dirname(foldPath)) + 1:]))
            parseZipLog(papserPath, resonFile, removeDir=True,callbackMsg=lambda msg:logUtils.info(msg))

            resonFile.writelines('\n\n')
        else:
            parserZipLogDir(papserPath, removeDir=True,callbackMsg=lambda msg:logUtils.info(msg))
        end = time.clock()
        time.strftime("%b %d %Y %H:%M:%S",)
        logUtils.info('---used {}----'.format(toolUtils.getUsedTimeStr(start, end)))
    else:
        papserPath = sep.join(['C:','Users','Administrator','Downloads','parse'])
        for foldPath in [ sep.join([papserPath, child]) for child in listdir(papserPath)]:
            parserZipLogDir(foldPath, True)
        end = time.clock()
        logUtils.info('---used {}----'.format(toolUtils.getUsedTimeStr(start, end)))


