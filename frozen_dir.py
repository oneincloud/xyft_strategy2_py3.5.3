import sys
import os

def app_path():
    '''
    Return the base application path.
    :return:
    '''
    if hasattr(sys,'frozen'):
        # Handle PyInstaller
        return os.path.dirname(sys.executable)
    return os.path.dirname(__file__)

#生成资源文件目录访问路径
def resource_path():
    if getattr(sys, 'frozen', False): #是否Bundle Resource
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")

    return base_path
    # return os.path.join(base_path, relative_path)