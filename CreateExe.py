
from subprocess import call
from os.path import (isdir, isfile, sep, dirname, abspath)
from datetime import datetime
from configparser import ConfigParser
from shutil import (rmtree, copyfile)
from Tool.toolUtils import ( zip_single, checkFileCode)
import re
import  AnrWindow, JiraTool

SHARE_PATH = sep.join(['D:','Share'])

def getVersion(pyName='AnrWindow.py'):
    currentVersion = '1.0.001'
    pattrn = 'CURRENT_VERSION = \'([\.|\d]+)\'.*'
    anr_py = sep.join([dirname(abspath(__file__)), pyName])
    for line in open(anr_py,encoding=checkFileCode(anr_py)).readlines():
        match = re.match(pattrn, line)
        if match:
            currentVersion = match.group(1)
    return currentVersion

def getUpdateContent(pyName='AnrWindow.py'):
    CURRENT_UPDATE_CONTENT = '初始化版本'
    pattrn = 'CURRENT_UPDATE_CONTENT = \'(.*)\'.*'
    anr_py = sep.join([dirname(abspath(__file__)), pyName])
    for line in open(anr_py,encoding=checkFileCode(anr_py)).readlines():
        match = re.match(pattrn, line)
        if match:
            CURRENT_UPDATE_CONTENT = match.group(1)
    return CURRENT_UPDATE_CONTENT

def create_decorator(func):
    def decorator(ico_path, *args, **kwargs):
        if ico_path and isfile(ico_path) and ico_path.endswith('.ico'):
            return func(ico_path, *args, **kwargs)
        else:
            return None
    return decorator

@create_decorator
def createAnrWindowExe(ico:str = None):
    call('pyinstaller -w -F -i {}  AnrWindow.py -p AnrTool.py -p Tool --hidden-import Tool'.format(ico))
    dist = sep.join(['dist','AnrWindow.exe'])

    if isfile(dist):
        EXE_PATH = sep.join([SHARE_PATH, 'AnrTool'])
        print('{} isdir {}'.format(EXE_PATH, isdir(EXE_PATH)))
        ANR_TOOL_PATH = sep.join([EXE_PATH, 'AnrTool'])
        EXE_FILE_PATH = sep.join([ANR_TOOL_PATH, 'AnrTool.exe'])
        ZIP_FILE_PATH = sep.join([EXE_PATH, 'AnrTool.zip'])
        print('exe={} zip={}'.format(EXE_FILE_PATH, ZIP_FILE_PATH))
        copyfile(dist, EXE_FILE_PATH)
        zip_single(ANR_TOOL_PATH, ZIP_FILE_PATH)

        customerConf = ConfigParser()
        customerConf.read(AnrWindow.VERSION_INI_FILE)
        defaultConf = customerConf.defaults()
        defaultConf['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        defaultConf['version'] = getVersion('AnrWindow.py')
        defaultConf['v{}'.format(defaultConf['version'])] = getUpdateContent('AnrWindow.py')
        defaultConf['content'] = defaultConf['v{}'.format(defaultConf['version'])]
        customerConf.write(open(AnrWindow.VERSION_INI_FILE, mode='w'))
        if isdir('dist'):
            rmtree('dist')
        if isdir('build'):
            rmtree('build')

@create_decorator
def createJiraExe(ico:str = None):
    call('pyinstaller -w -F -i {}  JiraTool.py -p AnrTool.py -p Tool --hidden-import Tool'.format(ico))
    dist = sep.join(['dist','JiraTool.exe'])
    if isfile(dist):

        EXE_PATH = sep.join([SHARE_PATH,'JiraTool'])
        print('{} isdir {}'.format(EXE_PATH, isdir(EXE_PATH)))
        JIRA_TOOL_PATH = sep.join([EXE_PATH, 'JiraTool'])
        EXE_FILE_PATH = sep.join([JIRA_TOOL_PATH, 'JiraTool.exe'])
        ZIP_FILE_PATH = sep.join([EXE_PATH, 'JiraTool.zip'])
        print('exe={} zip={}'.format(EXE_FILE_PATH, ZIP_FILE_PATH))

        copyfile(dist, EXE_FILE_PATH)
        zip_single(JIRA_TOOL_PATH, ZIP_FILE_PATH)
        customerConf = ConfigParser()
        customerConf.read(JiraTool.VERSION_INI_FILE)
        defaultConf = customerConf.defaults()
        defaultConf['update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        defaultConf['version'] = getVersion('JiraTool.py')
        defaultConf['v{}'.format(defaultConf['version'])] = getUpdateContent('JiraTool.py')
        defaultConf['content'] = defaultConf['v{}'.format(defaultConf['version'])]
        customerConf.write(open(JiraTool.VERSION_INI_FILE, mode='w'))
        if isdir('dist'):
            rmtree('dist')
        if isdir('build'):
            rmtree('build')


if __name__ == '__main__':
    createAnrWindowExe(sep.join(['res','anr.ico']))
    createJiraExe(sep.join(['res','systemui.ico']))
    exit()






'''
def xx():
    import base64
    open_icon = open("icon2.ico", "rb")  # 选择图标文件
    b64str = base64.b64encode(open_icon.read())
    open_icon.close()
    write_data = "img = '{0}'".format(b64str)
    f = open("icon2.py", "w+")
    f.write(write_data)  # 生成ASCII码
    f.close()

    import tkinter as tk
    import base64
    import os

    window = tk.Tk()
    tmp = open("tmp.ico", "wb+")
    tmp.write(base64.b64decode('AAA')
    # tmp.write(base64.b64decode('粘贴icon2.py字符串内容'))
    tmp.close()
    window.title('窗口标题')
    window.geometry('300x300')
    window.iconbitmap("tmp.ico")
    os.remove("tmp.ico")  #删除icon文件

    window.mainloop()
'''
#装饰器例子
def statically_typed(*types, return_type=None):
    def decorator(func):
        import functools
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if len(args) > len(types):
                raise ValueError('too many arguments')
            elif len(args) < len(types):
                raise ValueError('too few arguments')
            for i, (type_, arg) in enumerate(zip(types, args)):
                if not isinstance(type_, arg):
                    raise ValueError('argument {} must be of type {}'.format(i, type_.__name__))
            result = func(*args, **kwargs)
            if return_type is not None and not isinstance(result, return_type):
                raise ValueError('return value must be of type {}'.format(return_type.__name__))
            return wrapper
        return decorator

@statically_typed(str, str, return_type=str)
def make_tagged(text, tag):
    import html
    return '<{0}>{1}</{0}>'.format(tag, html.escape(text))

@statically_typed(str, int, str)
def repeat(what, count, separator):
    return ((what + separator)*count)[:-len(separator)]
