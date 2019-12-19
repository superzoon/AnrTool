import tkinter as tk
from tkinter import Tk
from tkinter import (PhotoImage, Frame)
from os import (startfile, walk, path, listdir, popen, remove, rename, makedirs, chdir)
import base64
from subprocess import call
from zipfile import ZipFile
from shutil import (rmtree, copyfile)
import threading
from tkinter.filedialog import askdirectory, askopenfilename
from AnrTool import parseZipLog, parserZipLogDir, GlobalValues
from Tool.workThread import WorkThread
from Tool.workThread import (postAction, addWorkDoneCallback)
from Tool import GLOBAL_VALUES
from tkinter import messagebox, Toplevel, Label, ttk
import zipfile, time
from os.path import (realpath, isdir, isfile, sep, dirname, abspath, exists, basename, getsize)
from datetime import datetime
from AnrTool import DEFAULT_PACKAGE
from configparser import ConfigParser
from Tool import logUtils
from Tool.widget import GressBar
current_dir = dirname(abspath(__file__))

EXE_PATH = '//MININT-578MFLI/Share/AnrTool/'
VERSION_INI_FILE = EXE_PATH+'version.ini'

CURRENT_VERSION = '1.0.007'
CURRENT_UPDATE_CONTENT = '多线程操作修复'

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
    else:
        if GLOBAL_VALUES.debug:
            logUtils.debug('不能连接服务器跟新文件{}'.format(EXE_PATH+'AnrTool.zip'))
        print('不能连接服务器')
    if update:
        ret = tk.messagebox.askquestion(title='新版本更新', message='是否更新版本{}?\n\n{}'.format(version,content))
        if ret == 'yes' or str(ret) == 'Ture':
            file_path = askdirectory()
            bar = GressBar()
            def copyAnrTool():
                zip_file = sep.join([file_path, 'AnrTool.zip'])
                copyfile(EXE_PATH+'AnrTool.zip', zip_file)
                time.sleep(3)
                if isfile(zip_file):
                    startfile(zip_file)
                else:
                    tk.messagebox.showinfo(title='提示', message='下载失败！')
                bar.quit()

            WorkThread(action=copyAnrTool).start()
            bar.start('更新软件','正在下载......')

HEIGHT = 600
WIDTH = 800

if __name__ == '__main__':
    window = tk.Tk()
    window.title('Anr 工具')
    window.resizable(0, 0)
    ico = sep.join(['res',"anr.ico"])
    if isfile(ico):
        window.iconbitmap(ico)
    sw = window.winfo_screenwidth()
    sh = window.winfo_screenheight()
    ww = WIDTH
    wh = HEIGHT
    x = (sw - ww) / 2
    y = (sh - wh) / 2
    window.geometry("%dx%d+%d+%d" % (ww, wh, x, y))

    bg = sep.join(['res','window_bg.png'])
    if isfile(bg):
        canvas = tk.Canvas(window, height=HEIGHT, width=WIDTH)
        image_file = tk.PhotoImage(file=bg)
        image = canvas.create_image(WIDTH / 2, HEIGHT / 2, anchor='center', image=image_file)  # n 北方，s 南方， w西方，e东方，center中间
        canvas.pack(side='top')
    h = 10
    title = tk.Label(window, text='今天的ANR你努力了吗?', bg='green', font=('Arial', 12), width=30, height=2)
    title.place(x=WIDTH / 2, y=h, anchor='n')

    select = tk.IntVar()
    select.set(0)
    h = h+50
    packageLabel = tk.Label(window, text='包名:', font=('Arial', 14))
    packageLabel.place(x=160, y=h, anchor='nw',width=80, height=40)
    packageEntry = tk.Entry(window, show='',  font=('Arial', 14))
    packageEntry.place(x=250, y=h, anchor='nw',width=400, height=40)
    packageEntry.insert('insert', DEFAULT_PACKAGE)

    w = 360
    h = h+50
    tip = tk.Label(window, font=('Arial', 12), height=2)
    tip.place(x=w, y=h, anchor='nw')
    h = h+5
    def select_radio():
        value = select.get()
        if value == 0:
            selse_button.config(text='文件')
            tip.config(text='解析单个anr的zip文件(例如:Jira号/版本号/LogId.zip)')
        if value == 1:
            selse_button.config(text='文件夹')
            tip.config(text='解析解析目录下所有anr文件(例如:项目/Jira号)')
        if value == 2:
            selse_button.config(text='文件夹')
            tip.config(text='解析解析目录下所有anr文件(例如:/项目)')


    w = w-100
    rb1 = tk.Radiobutton(window, text="单个Anr", variable=select, value=0 , command=select_radio)
    rb1.place(x=w, y=h, anchor='nw')
    w = w-100
    rb2 = tk.Radiobutton(window, text="多个Anr", variable=select, value=1, command=select_radio)
    rb2.place(x=w, y=h, anchor='nw')
    w = w-100
    rb3 = tk.Radiobutton(window, text="多个Jira", variable=select, value=2, command=select_radio)
    rb3.place(x=w, y=h, anchor='nw')

    h = h+50
    text_view = tk.Text(window)
    text_view.place(x=50, y=h+50, anchor='nw', width=WIDTH - 100, height=HEIGHT - h - 80)

    entry = tk.Entry(window, show=None, font=('Arial', 14))  # 显示成明文形式
    entry.place(x=WIDTH / 10 + 65, y=h, anchor='nw', width=500, height=40)
    def selectPath():
        value = select.get()
        file_path = None
        if value == 0:
            file_path = askopenfilename()
        if value == 1 or value==2:
            file_path = askdirectory()
        if file_path:
            if len(entry.get())>0:
                entry.delete(0, len(entry.get()))

            entry.insert('insert', file_path)
    def parserAnr():
        value = select.get()
        file_path = entry.get()
        packageName = packageEntry.get().strip()
        if not packageName:
            packageName = DEFAULT_PACKAGE
            packageEntry.insert('insert', packageName)
        bar = GressBar()

        def downCallback():
            time.sleep(1)
            bar.quit()
            start_file = ''
            if value == 0 :
                start_file = sep.join([foldPath, basename(file_path).replace('.zip','.txt') if '.zip' in basename(file_path) else 'reason.txt'])
            elif value == 1 :
                start_file = sep.join([file_path, '{}.txt'.format(basename(file_path))])
            elif value == 2 :
                start_file = file_path
            if exists(start_file):
                startfile(start_file)
        addWorkDoneCallback(downCallback)
        if value == 0 :
            # tip.config(text='解析单个anr的zip文件(例如:Jira号/版本号/LogId.zip)')
            if zipfile.is_zipfile(file_path):
                text_view.delete('1.0', 'end')
                foldPath = dirname(abspath(file_path))
                fileTxt = sep.join([foldPath, basename(file_path).replace('.zip','.txt') if '.zip' in basename(file_path) else 'reason.txt'])
                resonFile = open(file=fileTxt, mode='w', encoding='utf-8')
                resonFile.writelines('{}.{}\n\n'.format(str(1), abspath(file_path)[len(dirname(foldPath)) + 1:]))
                try:
                    def parse():
                        globalValue = parseZipLog(file_path, resonFile, packageName=packageName, removeDir=True, callbackMsg=bar.updateMsg)
                        resonFile.writelines("\n\n 解析有误或者有建议请邮箱xiao.liang@nubia.com(肖良)")
                        resonFile.flush()
                        resonFile.close()
                        if len(globalValue.showMessage) > 0:
                            text_view.insert('insert','\n'.join(globalValue.showMessage))
                        else:
                            text_view.insert('insert','解析完成')

                    postAction(action=parse)
                except:
                    logUtils.logException("Error: unable to start thread")
                bar.start()
            else:
                messagebox.showwarning(title='错误', message='请选择anr的zip包！')
        elif value == 1:
            # tip.config(text='解析解析目录下所有anr文件(例如:项目/Jira号)')
            if isdir(file_path):
                text_view.delete('1.0','end')
                try:
                    def parse():
                        globalValuesList = parserZipLogDir(file_path, packageName=packageName, removeDir=True, callbackMsg=bar.updateMsg)
                        showMessages = ['\n'.join(globalValues.showMessage) for globalValues in globalValuesList if len(globalValues.showMessage)>0 ]
                        if len(showMessages) > 0:
                            text_view.insert('insert','\n'.join(showMessages))
                        else:
                            text_view.insert('insert','解析完成')
                        fileTxt = sep.join([file_path,'reason.txt'])

                    postAction(action=parse)
                except:
                    logUtils.logException("Error: unable to start thread")
                bar.start()
            else:
                messagebox.showwarning(title='错误', message='请选择带anr的zip的目录！')


        if value == 2:
            # tip.config(text='解析解析目录下所有anr文件(例如:/项目)')
            if isdir(file_path):
                text_view.delete('1.0','end')
                for foldPath in [sep.join([file_path, child]) for child in listdir(file_path)]:
                    def getAction(path):
                        def action():
                            if isdir(path):
                                globalValuesList = parserZipLogDir(path, packageName=packageName, removeDir=True, callbackMsg=bar.updateMsg)
                                showMessages = ['\n'.join(globalValues.showMessage) for globalValues in globalValuesList if len(globalValues.showMessage)>0 ]
                                if len(showMessages) > 0:
                                    text_view.insert('insert','\n'.join(showMessages))
                        return action
                    try:
                        postAction(getAction(foldPath))
                    except:
                        logUtils.logException("Error: unable to start thread")
                bar.start()
            else:
                messagebox.showwarning(title='错误', message='请选择带anr的zip的目录！')
    selse_button = tk.Button(window, text='文件/文件夹', font=('Arial', 10), width=10, height=2, command=selectPath)
    selse_button.place(x=WIDTH / 10 - 30, y=h, anchor='nw')
    parser_button = tk.Button(window, text='解析', font=('Arial', 10), width=10, height=2, command=parserAnr)
    parser_button.place(x=WIDTH - 140, y=h, anchor='nw')
    select_radio()
    ##########检查更新#########
    updateExe()
    window.mainloop()

def testImage():
    from tkinter import (Tk,Label,LEFT,PhotoImage, RIGHT, mainloop)
    root = Tk()
    textLabel = Label(root,text = '请重试！\n您的操作不被允许！', # 文字支持换行
    justify = LEFT, # 左对齐
    padx = 10, # 左边距10px
    pady = 10) # 右边距10px
    textLabel.pack(side=LEFT)
    # 显示图片
    photo = PhotoImage(file='tk_image.png')
    imageLabel = Label(root, image=photo)
    imageLabel.pack(side=RIGHT)
    mainloop()

def testLabel():
    # !/usr/bin/env python
    # -*- coding: utf-8 -*-
    #创建主窗口及Label部件（标签）创建使用

    import tkinter as tk  # 使用Tkinter前需要先导入
    from tkinter import (Tk,Label,LEFT,PhotoImage, RIGHT, mainloop, Frame,StringVar)

    # 第1步，实例化object，建立窗口window
    window = tk.Tk()
    #背景
    photo = PhotoImage(file='tk4_bg.png')
    # 第2步，给窗口的可视化起名字
    window.title('My Window')

    # 第3步，设定窗口的大小(长 * 宽)
    window.geometry('500x300')  # 这里的乘是小x
    var = tk.IntStr()
    # 第4步，在图形界面上设定标签
    fr1 = Frame(window)
    fvar = StringVar()
    fvar.set('hahah')
    ll = Label(fr1, textvariable=var,  justify=LEFT)
    ll.pack(side=LEFT)
    fr1.pack(padx=10, pady=10)
    l = tk.Label(window, text='你好！this is Tkinter', image=photo, bg='green', font=('Arial', 12), width=30, height=2)
    # 说明： bg为背景，font为字体，width为长，height为高，这里的长和高是字符的长和高，比如height=2,就是标签有2个字符这么高

    # 第5步，放置标签
    l.pack()  # Label内容content区域放置位置，自动调节尺寸
    # 放置lable的方法有：1）l.pack(); 2)l.place();

    # 第6步，主窗口循环显示
    window.mainloop()
    # 注意，loop因为是循环的意思，window.mainloop就会让window不断的刷新，如果没有mainloop,就是一个静态的window,传入进去的值就不会有循环，mainloop就相当于一个很大的while循环，有个while，每点击一次就会更新一次，所以我们必须要有循环
    # 所有的窗口文件都必须有类似的mainloop函数，mainloop是窗口文件的关键的关键。


def testButton():
    # !/usr/bin/env python
    # -*- coding: utf-8 -*-
    # Button窗口部件
    # !/usr/bin/env python
    # -*- coding: utf-8 -*-
    # author:洪卫

    import tkinter as tk  # 使用Tkinter前需要先导入

    # 第1步，实例化object，建立窗口window
    window = tk.Tk()

    # 第2步，给窗口的可视化起名字
    window.title('My Window')

    # 第3步，设定窗口的大小(长 * 宽)
    window.geometry('500x300')  # 这里的乘是小x

    # 第4步，在图形界面上设定标签
    var = tk.StringVar()  # 将label标签的内容设置为字符类型，用var来接收hit_me函数的传出内容用以显示在标签上
    l = tk.Label(window, textvariable=var, bg='green', fg='white', font=('Arial', 12), width=30, height=2)
    # 说明： bg为背景，fg为字体颜色，font为字体，width为长，height为高，这里的长和高是字符的长和高，比如height=2,就是标签有2个字符这么高
    l.pack()

    # 定义一个函数功能（内容自己自由编写），供点击Button按键时调用，调用命令参数command=函数名
    on_hit = False

    def hit_me():
        global on_hit
        if on_hit == False:
            on_hit = True
            var.set('you hit me')
        else:
            on_hit = False
            var.set('')

    # 第5步，在窗口界面设置放置Button按键
    b = tk.Button(window, text='hit me', font=('Arial', 12), width=10, height=1, command=hit_me)
    b.pack()

    # 第6步，主窗口循环显示
    window.mainloop()


def testEntry():
    # !/usr/bin/env python
    # Entry是tkinter类中提供的的一个单行文本输入域，用来输入显示一行文本，收集键盘输入(类似 HTML 中的 text)。
    # !/usr/bin/env python
    # -*- coding: utf-8 -*-
    # author:洪卫

    import tkinter as tk  # 使用Tkinter前需要先导入

    # 第1步，实例化object，建立窗口window
    window = tk.Tk()

    # 第2步，给窗口的可视化起名字
    window.title('My Window')

    # 第3步，设定窗口的大小(长 * 宽)
    window.geometry('500x300')  # 这里的乘是小x

    # 第4步，在图形界面上设定输入框控件entry并放置控件
    e1 = tk.Entry(window, show='*', font=('Arial', 14))  # 显示成密文形式
    e2 = tk.Entry(window, show=None, font=('Arial', 14))  # 显示成明文形式
    e1.pack()
    e2.pack()

    # 第5步，主窗口循环显示
    window.mainloop()


def testText():
    #Text是tkinter类中提供的的一个多行文本区域，显示多行文本，可用来收集(或显示)用户输入的文字(类似 HTML 中的 textarea)，
    # 格式化文本显示，允许你用不同的样式和属性来显示和编辑文本，同时支持内嵌图象和窗口。
    # !/usr/bin/env python
    # -*- coding: utf-8 -*-
    # author:洪卫

    import tkinter as tk  # 使用Tkinter前需要先导入

    # 第1步，实例化object，建立窗口window
    window = tk.Tk()

    # 第2步，给窗口的可视化起名字
    window.title('My Window')

    # 第3步，设定窗口的大小(长 * 宽)
    window.geometry('500x300')  # 这里的乘是小x

    # 第4步，在图形界面上设定输入框控件entry框并放置
    e = tk.Entry(window, show=None)  # 显示成明文形式
    e.pack()

    # 第5步，定义两个触发事件时的函数insert_point和insert_end（注意：因为Python的执行顺序是从上往下，所以函数一定要放在按钮的上面）
    def insert_point():  # 在鼠标焦点处插入输入内容
        var = e.get()
        t.insert('insert', var)

    def insert_end():  # 在文本框内容最后接着插入输入内容
        var = e.get()
        t.insert('end', var)

    # 第6步，创建并放置两个按钮分别触发两种情况
    b1 = tk.Button(window, text='insert point', width=10,
                   height=2, command=insert_point)
    b1.pack()
    b2 = tk.Button(window, text='insert end', width=10,
                   height=2, command=insert_end)
    b2.pack()

    # 第7步，创建并放置一个多行文本框text用以显示，指定height=3为文本框是三个字符高度
    t = tk.Text(window, height=3)
    t.pack()

    # 第8步，主窗口循环显示
    window.mainloop()


def testListbox():
    #listbox是tkinter类中提供的的列表框部件，显示供选方案的一个列表。listbox能够被配置来得到radiobutton或checklist的行为。
    import tkinter as tk  # 使用Tkinter前需要先导入
    # !/usr/bin/env python
    # -*- coding: utf-8 -*-
    # author:洪卫

    import tkinter as tk  # 使用Tkinter前需要先导入

    # 第1步，实例化object，建立窗口window
    window = tk.Tk()

    # 第2步，给窗口的可视化起名字
    window.title('My Window')

    # 第3步，设定窗口的大小(长 * 宽)
    window.geometry('500x300')  # 这里的乘是小x

    # 第4步，在图形界面上创建一个标签label用以显示并放置
    var1 = tk.StringVar()  # 创建变量，用var1用来接收鼠标点击具体选项的内容
    l = tk.Label(window, bg='green', fg='yellow', font=('Arial', 12), width=10, textvariable=var1)
    l.pack()

    # 第6步，创建一个方法用于按钮的点击事件
    def print_selection():
        value = lb.get(lb.curselection())  # 获取当前选中的文本
        var1.set(value)  # 为label设置值

    # 第5步，创建一个按钮并放置，点击按钮调用print_selection函数
    b1 = tk.Button(window, text='print selection', width=15, height=2, command=print_selection)
    b1.pack()

    # 第7步，创建Listbox并为其添加内容
    var2 = tk.StringVar()
    var2.set((1, 2, 3, 4))  # 为变量var2设置值
    # 创建Listbox
    lb = tk.Listbox(window, listvariable=var2)  # 将var2的值赋给Listbox
    # 创建一个list并将值循环添加到Listbox控件中
    list_items = [11, 22, 33, 44]
    for item in list_items:
        lb.insert('end', item)  # 从最后一个位置开始加入值
    lb.insert(1, 'first')  # 在第一个位置加入'first'字符
    lb.insert(2, 'second')  # 在第二个位置加入'second'字符
    lb.delete(2)  # 删除第二个位置的字符
    lb.pack()

    # 第8步，主窗口循环显示
    window.mainloop()


def testRadiobutton():
    # !/usr/bin/env python
    # -*- coding: utf-8 -*-
    # Radiobutton：代表一个变量，它可以有多个值中的一个。点击它将为这个变量设置值，并且清除与这同一变量相关的其它radiobutton。

    import tkinter as tk  # 使用Tkinter前需要先导入

    # 第1步，实例化object，建立窗口window
    window = tk.Tk()

    # 第2步，给窗口的可视化起名字
    window.title('My Window')

    # 第3步，设定窗口的大小(长 * 宽)
    window.geometry('500x300')  # 这里的乘是小x

    # 第4步，在图形界面上创建一个标签label用以显示并放置
    var = tk.StringVar()  # 定义一个var用来将radiobutton的值和Label的值联系在一起.
    l = tk.Label(window, bg='yellow', width=20, text='empty')
    l.pack()

    # 第6步，定义选项触发函数功能
    def print_selection():
        l.config(text='you have selected ' + var.get())

    # 第5步，创建三个radiobutton选项，其中variable=var, value='A'的意思就是，当我们鼠标选中了其中一个选项，把value的值A放到变量var中，然后赋值给variable
    r1 = tk.Radiobutton(window, text='Option A', variable=var, value='A', command=print_selection)
    r1.pack()
    r2 = tk.Radiobutton(window, text='Option B', variable=var, value='B', command=print_selection)
    r2.pack()
    r3 = tk.Radiobutton(window, text='Option C', variable=var, value='C', command=print_selection)
    r3.pack()

    # 第7步，主窗口循环显示
    window.mainloop()


def test7():
    # !/usr/bin/env python
    # -*- coding: utf-8 -*-
    # Checkbutton：代表一个变量，它有两个不同的值。点击这个按钮将会在这两个值间切换，选择和取消选择。

    import tkinter as tk  # 使用Tkinter前需要先导入

    # 第1步，实例化object，建立窗口window
    window = tk.Tk()

    # 第2步，给窗口的可视化起名字
    window.title('My Window')

    # 第3步，设定窗口的大小(长 * 宽)
    window.geometry('500x300')  # 这里的乘是小x

    # 第4步，在图形界面上创建一个标签label用以显示并放置
    l = tk.Label(window, bg='yellow', width=20, text='empty')
    l.pack()

    # 第6步，定义触发函数功能
    def print_selection():
        if (var1.get() == 1) & (var2.get() == 0):  # 如果选中第一个选项，未选中第二个选项
            l.config(text='I love only Python ')
        elif (var1.get() == 0) & (var2.get() == 1):  # 如果选中第二个选项，未选中第一个选项
            l.config(text='I love only C++')
        elif (var1.get() == 0) & (var2.get() == 0):  # 如果两个选项都未选中
            l.config(text='I do not love either')
        else:
            l.config(text='I love both')  # 如果两个选项都选中

    # 第5步，定义两个Checkbutton选项并放置
    var1 = tk.IntVar()  # 定义var1和var2整型变量用来存放选择行为返回值
    var2 = tk.IntVar()
    c1 = tk.Checkbutton(window, text='Python', variable=var1, onvalue=1, offvalue=0,
                        command=print_selection)  # 传值原理类似于radiobutton部件
    c1.pack()
    c2 = tk.Checkbutton(window, text='C++', variable=var2, onvalue=1, offvalue=0, command=print_selection)
    c2.pack()

    # 第7步，主窗口循环显示
    window.mainloop()


def testScale():
    # !/usr/bin/env python
    # Scale： 尺度（拉动条），允许你通过滑块来设置一数字值。
    # 在需要用户给出评价等级，或者给出一个评价分数，或者拉动滑动条提供一个具体的数值等等。

    import tkinter as tk  # 使用Tkinter前需要先导入

    # 第1步，实例化object，建立窗口window
    window = tk.Tk()

    # 第2步，给窗口的可视化起名字
    window.title('My Window')

    # 第3步，设定窗口的大小(长 * 宽)
    window.geometry('500x300')  # 这里的乘是小x

    # 第4步，在图形界面上创建一个标签label用以显示并放置
    l = tk.Label(window, bg='green', fg='white', width=20, text='empty')
    l.pack()

    # 第6步，定义一个触发函数功能
    def print_selection(v):
        l.config(text='you have selected ' + v)

    # 第5步，创建一个尺度滑条，长度200字符，从0开始10结束，以2为刻度，精度为0.01，触发调用print_selection函数
    s = tk.Scale(window, label='try me', from_=0, to=10, orient=tk.HORIZONTAL, length=200, showvalue=0, tickinterval=2,
                 resolution=0.01, command=print_selection)
    s.pack()

    # 第7步，主窗口循环显示
    window.mainloop()


def testCanvas():
    # !/usr/bin/env python
    # 画布，提供绘图功能(直线、椭圆、多边形、矩形) 可以包含图形或位图，用来绘制图表和图，创建图形编辑器，实现定制窗口部件。
    # 在比如像用户交互界面等，需要提供设计的图标、图形、logo等信息是可以用到画布。

    import tkinter as tk  # 使用Tkinter前需要先导入

    # 第1步，实例化object，建立窗口window
    window = tk.Tk()

    # 第2步，给窗口的可视化起名字
    window.title('My Window')

    # 第3步，设定窗口的大小(长 * 宽)
    window.geometry('500x300')  # 这里的乘是小x

    # 第4步，在图形界面上创建 500 * 200 大小的画布并放置各种元素
    canvas = tk.Canvas(window, bg='green', height=200, width=500)
    # 说明图片位置，并导入图片到画布上
    image_file = tk.PhotoImage(file='pic.gif')  # 图片位置（相对路径，与.py文件同一文件夹下，也可以用绝对路径，需要给定图片具体绝对路径）
    image = canvas.create_image(250, 0, anchor='n', image=image_file)  # 图片锚定点（n图片顶端的中间点位置）放在画布（250,0）坐标处
    # 定义多边形参数，然后在画布上画出指定图形
    x0, y0, x1, y1 = 100, 100, 150, 150
    line = canvas.create_line(x0 - 50, y0 - 50, x1 - 50, y1 - 50)  # 画直线
    oval = canvas.create_oval(x0 + 120, y0 + 50, x1 + 120, y1 + 50, fill='yellow')  # 画圆 用黄色填充
    arc = canvas.create_arc(x0, y0 + 50, x1, y1 + 50, start=0, extent=180)  # 画扇形 从0度打开收到180度结束
    rect = canvas.create_rectangle(330, 30, 330 + 20, 30 + 20)  # 画矩形正方形
    canvas.pack()

    # 第6步，触发函数，用来一定指定图形
    def moveit():
        canvas.move(rect, 2, 2)  # 移动正方形rect（也可以改成其他图形名字用以移动一起图形、元素），按每次（x=2, y=2）步长进行移动

    # 第5步，定义一个按钮用来移动指定图形的在画布上的位置
    b = tk.Button(window, text='move item', command=moveit).pack()

    # 第7步，主窗口循环显示
    window.mainloop()

def testMenu():
    # !/usr/bin/env python
    # -*- coding: utf-8 -*-
    #菜单条，用来实现下拉和弹出式菜单，点下菜单后弹出的一个选项列表,用户可以从中选择

    import tkinter as tk  # 使用Tkinter前需要先导入

    # 第1步，实例化object，建立窗口window
    window = tk.Tk()

    # 第2步，给窗口的可视化起名字
    window.title('My Window')

    # 第3步，设定窗口的大小(长 * 宽)
    window.geometry('500x300')  # 这里的乘是小x

    # 第4步，在图形界面上创建一个标签用以显示内容并放置
    l = tk.Label(window, text='      ', bg='green')
    l.pack()

    # 第10步，定义一个函数功能，用来代表菜单选项的功能，这里为了操作简单，定义的功能比较简单
    counter = 0

    def do_job():
        global counter
        l.config(text='do ' + str(counter))
        counter += 1

    # 第5步，创建一个菜单栏，这里我们可以把他理解成一个容器，在窗口的上方
    menubar = tk.Menu(window)

    # 第6步，创建一个File菜单项（默认不下拉，下拉内容包括New，Open，Save，Exit功能项）
    filemenu = tk.Menu(menubar, tearoff=0)
    # 将上面定义的空菜单命名为File，放在菜单栏中，就是装入那个容器中
    menubar.add_cascade(label='File', menu=filemenu)

    # 在File中加入New、Open、Save等小菜单，即我们平时看到的下拉菜单，每一个小菜单对应命令操作。
    filemenu.add_command(label='New', command=do_job)
    filemenu.add_command(label='Open', command=do_job)
    filemenu.add_command(label='Save', command=do_job)
    filemenu.add_separator()  # 添加一条分隔线
    filemenu.add_command(label='Exit', command=window.quit)  # 用tkinter里面自带的quit()函数

    # 第7步，创建一个Edit菜单项（默认不下拉，下拉内容包括Cut，Copy，Paste功能项）
    editmenu = tk.Menu(menubar, tearoff=0)
    # 将上面定义的空菜单命名为 Edit，放在菜单栏中，就是装入那个容器中
    menubar.add_cascade(label='Edit', menu=editmenu)

    # 同样的在 Edit 中加入Cut、Copy、Paste等小命令功能单元，如果点击这些单元, 就会触发do_job的功能
    editmenu.add_command(label='Cut', command=do_job)
    editmenu.add_command(label='Copy', command=do_job)
    editmenu.add_command(label='Paste', command=do_job)

    # 第8步，创建第二级菜单，即菜单项里面的菜单
    submenu = tk.Menu(filemenu)  # 和上面定义菜单一样，不过此处实在File上创建一个空的菜单
    filemenu.add_cascade(label='Import', menu=submenu, underline=0)  # 给放入的菜单submenu命名为Import

    # 第9步，创建第三级菜单命令，即菜单项里面的菜单项里面的菜单命令（有点拗口，笑~~~）
    submenu.add_command(label='Submenu_1', command=do_job)  # 这里和上面创建原理也一样，在Import菜单项中加入一个小菜单命令Submenu_1

    # 第11步，创建菜单栏完成后，配置让菜单栏menubar显示出来
    window.config(menu=menubar)

    # 第12步，主窗口循环显示
    window.mainloop()


def testFrame ():
    # !/usr/bin/env python
    # 框架，用来承载放置其他GUI元素，就是一个容器，是一个在 Windows 上分离小区域的部件, 它能将 Windows 分成不同的区,然后存放不同的其他部件. 同时一个 Frame 上也能再分成两个 Frame, Frame 可以认为是一种容器.
    # 在比如像软件或网页交互界面等，有不同的界面逻辑层级和功能区域划分时可以用到，让交互界面逻辑更加清晰。

    import tkinter as tk  # 使用Tkinter前需要先导入

    # 第1步，实例化object，建立窗口window
    window = tk.Tk()

    # 第2步，给窗口的可视化起名字
    window.title('My Window')

    # 第3步，设定窗口的大小(长 * 宽)
    window.geometry('500x300')  # 这里的乘是小x

    # 第4步，在图形界面上创建一个标签用以显示内容并放置
    tk.Label(window, text='on the window', bg='red', font=('Arial', 16)).pack()  # 和前面部件分开创建和放置不同，其实可以创建和放置一步完成

    # 第5步，创建一个主frame，长在主window窗口上
    frame = tk.Frame(window)
    frame.pack()

    # 第6步，创建第二层框架frame，长在主框架frame上面
    frame_l = tk.Frame(frame)  # 第二层frame，左frame，长在主frame上
    frame_r = tk.Frame(frame)  # 第二层frame，右frame，长在主frame上
    frame_l.pack(side='left')
    frame_r.pack(side='right')

    # 第7步，创建三组标签，为第二层frame上面的内容，分为左区域和右区域，用不同颜色标识
    tk.Label(frame_l, text='on the frame_l1', bg='green').pack()
    tk.Label(frame_l, text='on the frame_l2', bg='green').pack()
    tk.Label(frame_l, text='on the frame_l3', bg='green').pack()
    tk.Label(frame_r, text='on the frame_r1', bg='yellow').pack()
    tk.Label(frame_r, text='on the frame_r2', bg='yellow').pack()
    tk.Label(frame_r, text='on the frame_r3', bg='yellow').pack()

    # 第8步，主窗口循环显示
    window.mainloop()

def testmessageBox():
    # import tkinter   # 使用Tkinter前需要先导入
    # tkinter.messagebox.showinfo(title='Hi', message='你好！')  # 提示信息对话窗
    # tkinter.messagebox.showwarning(title='Hi', message='有警告！')  # 提出警告对话窗
    # tkinter.messagebox.showerror(title='Hi', message='出错了！')  # 提出错误对话窗
    # print(tkinter.messagebox.askquestion(title='Hi', message='你好！'))  # 询问选择对话窗return 'yes', 'no'
    # print(tkinter.messagebox.askyesno(title='Hi', message='你好！'))  # return 'True', 'False'
    # print(tkinter.messagebox.askokcancel(title='Hi', message='你好！'))  # return 'True', 'False'

    # !/usr/bin/env python
    # messageBox：消息框，用于显示你应用程序的消息框。(Python2中为tkMessagebox)，其实这里的messageBox就是我们平时看到的弹窗。 我们首先需要定义一个触发功能，来触发这个弹窗，这里我们就放上以前学过的button按钮，通过触发功能，调用messagebox吧，点击button按钮就会弹出提示对话框。下面给出messagebox提示信息的几种形式：
    #在比如像软件或网页交互界面等，有不同的界面逻辑层级和功能区域划分时可以用到，让交互界面逻辑更加清晰。

    import tkinter as tk  # 使用Tkinter前需要先导入
    import tkinter.messagebox  # 要使用messagebox先要导入模块

    # 第1步，实例化object，建立窗口window
    window = tk.Tk()

    # 第2步，给窗口的可视化起名字
    window.title('My Window')

    # 第3步，设定窗口的大小(长 * 宽)
    window.geometry('500x300')  # 这里的乘是小x

    # 第5步，定义触发函数功能
    def hit_me():
        tkinter.messagebox.showinfo(title='Hi', message='你好！')  # 提示信息对话窗
        # tkinter.messagebox.showwarning(title='Hi', message='有警告！')       # 提出警告对话窗
        # tkinter.messagebox.showerror(title='Hi', message='出错了！')         # 提出错误对话窗
        # print(tkinter.messagebox.askquestion(title='Hi', message='你好！'))  # 询问选择对话窗return 'yes', 'no'
        # print(tkinter.messagebox.askyesno(title='Hi', message='你好！'))     # return 'True', 'False'
        # print(tkinter.messagebox.askokcancel(title='Hi', message='你好！'))  # return 'True', 'False'

    # 第4步，在图形界面上创建一个标签用以显示内容并放置
    tk.Button(window, text='hit me', bg='green', font=('Arial', 14), command=hit_me).pack()

    # 第6步，主窗口循环显示
    window.mainloop()

def testGrid ():
    # !/usr/bin/env python
    '''The Grid Geometry Manager
    The Pack Geometry Manager
    The Place Geometry Manager'''
    #grid 是方格, 所以所有的内容会被放在这些规律的方格中。例如
    # for i in range(3):
    #     for j in range(3):
    #         tk.Label(window, text=1).grid(row=i, column=j, padx=10, pady=10, ipadx=10, ipady=10)

    # -*- coding: utf-8 -*-
    # author:洪卫

    import tkinter as tk  # 使用Tkinter前需要先导入

    # 第1步，实例化object，建立窗口window
    window = tk.Tk()

    # 第2步，给窗口的可视化起名字
    window.title('My Window')

    # 第3步，设定窗口的大小(长 * 宽)
    window.geometry('500x300')  # 这里的乘是小x

    # 第4步，grid 放置方法
    for i in range(3):
        for j in range(3):
            tk.Label(window, text=1).grid(row=i, column=j, padx=10, pady=10, ipadx=10, ipady=10)

    # 第5步，主窗口循环显示
    window.mainloop()

def testPack ():
    '''tk.Label(window, text='P', fg='red').pack(side='top')    # 上
    tk.Label(window, text='P', fg='red').pack(side='bottom') # 下
    tk.Label(window, text='P', fg='red').pack(side='left')   # 左
    tk.Label(window, text='P', fg='red').pack(side='right')  # 右
    '''
    # !/usr/bin/env python

    import tkinter as tk  # 使用Tkinter前需要先导入

    # 第1步，实例化object，建立窗口window
    window = tk.Tk()

    # 第2步，给窗口的可视化起名字
    window.title('My Window')

    # 第3步，设定窗口的大小(长 * 宽)
    window.geometry('500x300')  # 这里的乘是小x

    # 第4步，pack 放置方法
    tk.Label(window, text='P', fg='red').pack(side='top')  # 上
    tk.Label(window, text='P', fg='red').pack(side='bottom')  # 下
    tk.Label(window, text='P', fg='red').pack(side='left')  # 左
    tk.Label(window, text='P', fg='red').pack(side='right')  # 右

    # 第5步，主窗口循环显示
    window.mainloop()

def testPlace():
    #再接下来我们来看place(), 这个比较容易理解，就是给精确的坐标来定位，如此处给的(50, 100)，就是将这个部件放在坐标为(x=50, y=100)的这个位置, 后面的参数 anchor='nw'，就是前面所讲的锚定点是西北角。例如：
    #tk.Label(window, text='Pl', font=('Arial', 20), ).place(x=50, y=100, anchor='nw')
    # !/usr/bin/env python

    import tkinter as tk  # 使用Tkinter前需要先导入

    # 第1步，实例化object，建立窗口window
    window = tk.Tk()

    # 第2步，给窗口的可视化起名字
    window.title('My Window')

    # 第3步，设定窗口的大小(长 * 宽)
    window.geometry('500x300')  # 这里的乘是小x

    # 第4步，place 放置方法（精准的放置到指定坐标点的位置上）
    tk.Label(window, text='Pl', font=('Arial', 20), ).place(x=50, y=100, anchor='nw')

    # 第5步，主窗口循环显示
    window.mainloop()

def test():
    # !/usr/bin/env python
    # -*- coding: utf-8 -*-
    # 用户登录窗口例子

    import tkinter as tk  # 使用Tkinter前需要先导入
    import tkinter.messagebox
    import pickle

    # 第1步，实例化object，建立窗口window
    window = tk.Tk()

    # 第2步，给窗口的可视化起名字
    window.title('Wellcome to Hongwei Website')

    # 第3步，设定窗口的大小(长 * 宽)
    window.geometry('400x300')  # 这里的乘是小x

    # 第4步，加载 wellcome image
    canvas = tk.Canvas(window, width=400, height=135, bg='green')
    image_file = tk.PhotoImage(file='pic.gif')
    image = canvas.create_image(200, 0, anchor='n', image=image_file)
    canvas.pack(side='top')
    tk.Label(window, text='Wellcome', font=('Arial', 16)).pack()

    # 第5步，用户信息
    tk.Label(window, text='User name:', font=('Arial', 14)).place(x=10, y=170)
    tk.Label(window, text='Password:', font=('Arial', 14)).place(x=10, y=210)

    # 第6步，用户登录输入框entry
    # 用户名
    var_usr_name = tk.StringVar()
    var_usr_name.set('example@python.com')
    entry_usr_name = tk.Entry(window, textvariable=var_usr_name, font=('Arial', 14))
    entry_usr_name.place(x=120, y=175)
    # 用户密码
    var_usr_pwd = tk.StringVar()
    entry_usr_pwd = tk.Entry(window, textvariable=var_usr_pwd, font=('Arial', 14), show='*')
    entry_usr_pwd.place(x=120, y=215)

    # 第8步，定义用户登录功能
    def usr_login():
        # 这两行代码就是获取用户输入的usr_name和usr_pwd
        usr_name = var_usr_name.get()
        usr_pwd = var_usr_pwd.get()

        # 这里设置异常捕获，当我们第一次访问用户信息文件时是不存在的，所以这里设置异常捕获。
        # 中间的两行就是我们的匹配，即程序将输入的信息和文件中的信息匹配。
        try:
            with open('usrs_info.pickle', 'rb') as usr_file:
                usrs_info = pickle.load(usr_file)
        except FileNotFoundError:
            # 这里就是我们在没有读取到`usr_file`的时候，程序会创建一个`usr_file`这个文件，并将管理员
            # 的用户和密码写入，即用户名为`admin`密码为`admin`。
            with open('usrs_info.pickle', 'wb') as usr_file:
                usrs_info = {'admin': 'admin'}
                pickle.dump(usrs_info, usr_file)
                usr_file.close()  # 必须先关闭，否则pickle.load()会出现EOFError: Ran out of input

        # 如果用户名和密码与文件中的匹配成功，则会登录成功，并跳出弹窗how are you? 加上你的用户名。
        if usr_name in usrs_info:
            if usr_pwd == usrs_info[usr_name]:
                tkinter.messagebox.showinfo(title='Welcome', message='How are you? ' + usr_name)
            # 如果用户名匹配成功，而密码输入错误，则会弹出'Error, your password is wrong, try again.'
            else:
                tkinter.messagebox.showerror(message='Error, your password is wrong, try again.')
        else:  # 如果发现用户名不存在
            is_sign_up = tkinter.messagebox.askyesno('Welcome！ ', 'You have not sign up yet. Sign up now?')
            # 提示需不需要注册新用户
            if is_sign_up:
                usr_sign_up()

    # 第9步，定义用户注册功能
    def usr_sign_up():
        def sign_to_Hongwei_Website():
            # 以下三行就是获取我们注册时所输入的信息
            np = new_pwd.get()
            npf = new_pwd_confirm.get()
            nn = new_name.get()

            # 这里是打开我们记录数据的文件，将注册信息读出
            with open('usrs_info.pickle', 'rb') as usr_file:
                exist_usr_info = pickle.load(usr_file)
            # 这里就是判断，如果两次密码输入不一致，则提示Error, Password and confirm password must be the same!
            if np != npf:
                tkinter.messagebox.showerror('Error', 'Password and confirm password must be the same!')

            # 如果用户名已经在我们的数据文件中，则提示Error, The user has already signed up!
            elif nn in exist_usr_info:
                tkinter.messagebox.showerror('Error', 'The user has already signed up!')

            # 最后如果输入无以上错误，则将注册输入的信息记录到文件当中，并提示注册成功Welcome！,You have successfully signed up!，然后销毁窗口。
            else:
                exist_usr_info[nn] = np
                with open('usrs_info.pickle', 'wb') as usr_file:
                    pickle.dump(exist_usr_info, usr_file)
                tkinter.messagebox.showinfo('Welcome', 'You have successfully signed up!')
                # 然后销毁窗口。
                window_sign_up.destroy()

        # 定义长在窗口上的窗口
        window_sign_up = tk.Toplevel(window)
        window_sign_up.geometry('300x200')
        window_sign_up.title('Sign up window')

        new_name = tk.StringVar()  # 将输入的注册名赋值给变量
        new_name.set('example@python.com')  # 将最初显示定为'example@python.com'
        tk.Label(window_sign_up, text='User name: ').place(x=10, y=10)  # 将`User name:`放置在坐标（10,10）。
        entry_new_name = tk.Entry(window_sign_up, textvariable=new_name)  # 创建一个注册名的`entry`，变量为`new_name`
        entry_new_name.place(x=130, y=10)  # `entry`放置在坐标（150,10）.

        new_pwd = tk.StringVar()
        tk.Label(window_sign_up, text='Password: ').place(x=10, y=50)
        entry_usr_pwd = tk.Entry(window_sign_up, textvariable=new_pwd, show='*')
        entry_usr_pwd.place(x=130, y=50)

        new_pwd_confirm = tk.StringVar()
        tk.Label(window_sign_up, text='Confirm password: ').place(x=10, y=90)
        entry_usr_pwd_confirm = tk.Entry(window_sign_up, textvariable=new_pwd_confirm, show='*')
        entry_usr_pwd_confirm.place(x=130, y=90)

        # 下面的 sign_to_Hongwei_Website
        btn_comfirm_sign_up = tk.Button(window_sign_up, text='Sign up', command=sign_to_Hongwei_Website)
        btn_comfirm_sign_up.place(x=180, y=120)

    # 第7步，login and sign up 按钮
    btn_login = tk.Button(window, text='Login', command=usr_login)
    btn_login.place(x=120, y=240)
    btn_sign_up = tk.Button(window, text='Sign up', command=usr_sign_up)
    btn_sign_up.place(x=200, y=240)

    # 第10步，主窗口循环显示
    window.mainloop()
