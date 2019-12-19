import tkinter as tk
from tkinter import Tk ,messagebox, Toplevel, Label, ttk, Event
from tkinter.filedialog import askdirectory
from shutil import (rmtree, copyfile)
from Tool.workThread import postAction,addWorkDoneCallback, LockUtil
from Tool import downloadLog
from configparser import ConfigParser
from Tool.workThread import WorkThread
from queue import Queue
from os.path import (realpath, isdir, isfile, sep, dirname, abspath, exists, basename, getsize)
from os import startfile
import re, time
from Tool import widget
from Tool import TEST

EXE_PATH = '//MININT-578MFLI/Share/WorkTool/'
VERSION_INI_FILE = EXE_PATH+'version.ini'
EXE_FILE_NAME = 'WorkTool.zip'

CURRENT_VERSION = '1.0.000'
CURRENT_UPDATE_CONTENT = '第一个版本'

def updateExe():
    update = False
    version = ''
    content = ''
    if isfile(VERSION_INI_FILE):
        customerConf = ConfigParser()
        customerConf.read(VERSION_INI_FILE)
        defaultConf = customerConf.defaults()
        def versionToInt(version:str):
            vint = 0
            for istr in version.split('.'):
                vint = vint*1000+int(istr)
            return vint
        if 'version' in defaultConf:
            versionToInt(defaultConf['version'])
            remote_version = versionToInt(defaultConf['version'])
            current_version = versionToInt(CURRENT_VERSION)
            if remote_version > current_version:
                update = True
                version = 'v{}'.format(defaultConf['version'])
        if 'content' in defaultConf:
            content = defaultConf['content']
    if update:
        ret = tk.messagebox.askquestion(title='新版本更新', message='是否更新版本{}?\n\n{}'.format(version,content))
        if ret == 'yes' or str(ret) == 'True':
            file_path = askdirectory()
            bar = widget.GressBar()
            def copyTool():
                zip_file = sep.join([file_path, 'WorkTool.zip'])
                copyfile(EXE_PATH+'WorkTool.zip', zip_file)
                time.sleep(3)
                if isfile(zip_file):
                    startfile(zip_file)
                else:
                    tk.messagebox.showinfo(title='提示', message='下载失败！')
                bar.quit()

            WorkThread(action=copyTool).start()
            bar.start('更新软件','正在下载......')

class DownloadFrame():

    def __init__(self, window:Tk, width, height):
        self.window = window
        self.width = width;
        self.height = height
        self.initView()

    def initView(self):
        width = self.width
        height = self.height
        frame = tk.Frame(window, width=width, height=height)
        MIN = 2
        MAX = 20
        left = 0
        top = 0
        self.padding = int(width/40)
        self.width =width-2*self.padding
        self.height =height
        left = 0+self.padding
        top = 0+self.padding

        height = 40
        width = self.width/2
        left = self.width/4+self.padding
        lable = tk.Label(frame, text='Jira Log下载',bg=widget.gray, anchor=widget.ANCHOR_CENTER, fg =widget.blue, font=('Arial', 16))
        lable.place(x=left, y=top, anchor='nw', width=width, height=height)

        top = top + height + self.padding
        ###tip
        left = self.padding+20
        width = self.width
        tipLable = tk.Label(frame, text='多个Jira、机型、版本使用空格隔开，Jira与机型必填', anchor=widget.ANCHOR_W, fg =widget.gray, font=(11))
        tipLable.place(x=left, y=top, anchor='nw', width=width, height=height)
        self.frame = frame

        top = top + height
        left = 0+self.padding
        height = 40
        ###jira
        jiraWidth = int(self.width*0.3)
        left = left
        width = self.width*0.1
        jiraLable = tk.Label(frame, text='Jira:',anchor=widget.ANCHOR_E, font=(14))
        jiraLable.place(x=left, y=top, anchor='nw', width=width, height=height)
        self.jiraLable = jiraLable

        left = left+width+MIN*2
        width = jiraWidth - left
        jiraEntry = tk.Entry(window, show='', font=('Arial', 14))
        jiraEntry.place(x=left, y=top, anchor='nw', width=width, height=height)
        if TEST:
            jiraEntry.insert('insert', 'LOG-67680')
        self.jiraEntry = jiraEntry

        ###sersin
        modelWidth = int(self.width*0.3)
        left = left + width + MAX/2
        width = self.width*0.1
        modelLable = tk.Label(frame, text='机型:', anchor=widget.ANCHOR_E, font=(14))
        modelLable.place(x=left, y=top, anchor='nw', width=width, height=height)
        self.versionLable = modelLable

        left = left+width+MIN
        width = modelWidth - MIN - width - MAX/2
        modelEntry = tk.Entry(window, show='', font=('Arial', 14))
        modelEntry.place(x=left+MIN, y=top, anchor='nw', width=width, height=height)
        if TEST:
            modelEntry.insert('insert', 'NX629J')
        self.modelEntry = modelEntry

        ###sersin
        versionWidth = int(self.width*0.4)
        left = left + width + MAX/2
        width = self.width*0.1
        versionLable = tk.Label(frame, text='版本:', anchor=widget.ANCHOR_E, font=(14))
        versionLable.place(x=left, y=top, anchor='nw', width=width, height=height)
        self.versionLable = versionLable

        left = left+width+MIN
        width = versionWidth - width
        versionEntry = tk.Entry(window, show='', font=('Arial', 14))
        versionEntry.place(x=left+MIN, y=top, anchor='nw', width=width, height=height)
        self.versionEntry = versionEntry

        top = top+height+self.padding
        height = 40

        ###save
        self.savePath = None
        def selectPath():
            self.savePath = askdirectory()
            self.saveEntry.delete(0, len(self.saveEntry.get()))
            self.saveEntry.insert('insert', self.savePath)
        saveWidth = self.width
        left = self.padding
        width = self.width*0.15
        saveLable = tk.Button(frame, text='选择路径:',command=selectPath , font=('Arial', 14))
        saveLable.place(x=left, y=top, anchor='nw', width=width, height=height)
        self.saveLable = saveLable

        left = left+width+MIN
        width = self.width*0.7
        saveEntry = tk.Entry(window, show='', font=('Arial', 14))
        saveEntry.place(x=left+MIN, y=top, anchor='nw', width=width-MIN, height=height)
        self.saveEntry = saveEntry

        def downloadJira():
            self.downloadJira()

        left = left+width+MIN
        width = saveWidth - left + self.padding - MAX/2
        saveButton = tk.Button(window, text='下载', command=downloadJira , font=(14))
        saveButton.place(x=left+MIN*2, y=top, anchor='nw', width=width, height=height)
        self.saveButton = saveButton

        top = top+height
        ###parseCheck
        self.anrParse = False
        var = tk.BooleanVar()
        def checklistener():
            self.anrParse = var.get()
        parseCheck = tk.Checkbutton(window, text='Anr解析', variable=var, onvalue=True, offvalue=False, command=checklistener )
        def showParseCheck():
            self.parseCheck.place(x=left+MIN, y=top, anchor='nw', width=width, height=height)
            self.parseCheckShow = True
        def hideParseCheck():
            self.parseCheck.place_forget()
            self.parseCheckShow = False

        self.parseCheckShow = False
        self.parseCheck = parseCheck
        self.showParseCheck = showParseCheck
        self.hideParseCheck = hideParseCheck

    def showAnrBox(self):
        if hasattr(self, 'showParseCheck') and not self.parseCheckShow:
            self.showParseCheck()
        elif hasattr(self, 'hideParseCheck') and self.parseCheckShow:
            self.hideParseCheck()

    def check(self):
        savePath:str = self.saveEntry.get()
        if not savePath or len(savePath) == 0:
            messagebox.showwarning(title='目录为空', message='请选择有效目录！')
            return False
        if not isdir(savePath):
            messagebox.showwarning(title='找不到目录', message='请选择有效目录！')
            return False
        self.savePath = savePath

        jira:str = self.jiraEntry.get()
        if not jira or len(jira) == 0:
            messagebox.showwarning(title='Jira号为空', message='请请输入有效Jira号，多个Jira号使用空格隔开！')
            return False
        jiras = jira.split(' ')
        pattern = 'LOG-[\d]+'
        self.jiras = []
        for item in jiras:
            jira = item.strip()
            if jira and len(jira) > 0:
                if not re.match(pattern, jira):
                    messagebox.showwarning(title='有无效Jira号输入', message='请请输入有效Jira号，多个Jira号使用空格隔开！')
                    return False
                if not jira in self.jiras:
                    self.jiras.append(jira)
        if len(self.jiras)==0:
            messagebox.showwarning(title='有无效Jira号输入', message='请请输入有效Jira号，多个Jira号使用空格隔开！')
            return False

        model:str = self.modelEntry.get()
        if not model or len(model) == 0:
            messagebox.showwarning(title='机型为空', message='请请输入有效机型，多个机型使用空格隔开！')
            return False
        models = model.split(' ')
        self.models = []
        for item in models:
            model = item.strip()
            if not model in self.models:
                self.models.append(model)
        if len(self.models)==0:
            messagebox.showwarning(title='有无效机型输入', message='请请输入有效机型，多个机型使用空格隔开！')
            return False

        version:str = self.versionEntry.get()
        self.versions = []
        if version or len(version) >0:
            self.versions = version.split(' ')
        for item in models:
            model = item.strip()
            if not model in self.models:
                self.models.append(model)

        return True

    def downloadJira(self):
        if self.check():
            def callbackMsg(msg:str):
                if self.gressBar:
                    self.gressBar.updateMsg(msg)

            def downCallback():
                time.sleep(1)
                if self.gressBar:
                    self.gressBar.quit()
                if len(downloadLog.downLoadErrs)>0:
                    file = sep.join([self.savePath,'downloadError.txt']);
                    with open(file, mode='w') as errFile:
                        errFile.write('\n'.join(downloadLog.downLoadErrs))
                startfile(self.savePath)
            addWorkDoneCallback(downCallback)
            self.gressBar = widget.GressBar()
            for jiraId in self.jiras:
                def getAction( outPath, callback, jiraId, models, versions, anrParse):
                    def downloadAction():
                        downloadLog.download(outPath = outPath, callbackMsg=callback, jiraId = jiraId, productModels = models, productVersions= versions,  parse=anrParse)
                    return downloadAction
                postAction(getAction( self.savePath, callbackMsg, jiraId, self.models, self.versions, self.anrParse))
            self.gressBar.start()

    def pack(self):
        self.frame.pack()

if __name__ == '__main__':
    window = tk.Tk()
    window.resizable(width=False, height=False)
    widget.setTitleIco(window, 'Log下载工具')
    height = 300
    width = 800
    screenwidth = window.winfo_screenwidth()
    screenheight = window.winfo_screenheight()
    alignstr = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
    window.geometry(alignstr)
    downloadFrame = DownloadFrame(window, width, height)
    downloadFrame.pack()

    var = tk.StringVar(value='0')
    def touchTeam(events:Event):
        currentTime = time.time()
        timestamp = currentTime - float(var.get())
        if timestamp < 0.2:
            downloadFrame.showAnrBox()
        var.set(str(currentTime))

    lableWidth = width/5
    lableHeight = 30
    lable = tk.Label(window, text='Nubia SystemUI team', fg =widget.gray, font=('Arial', 12))
    lable.bind("<Button-1>",touchTeam)  # 鼠标点击事件 <Button-1>表示左键 2表示滚轮 3表示右键
    lable.place(x=width - lableWidth - 50, y=height - lableHeight - 10 , anchor='nw', width=lableWidth, height=lableHeight)

    ##########检查更新#########
    updateExe()
    window.mainloop()