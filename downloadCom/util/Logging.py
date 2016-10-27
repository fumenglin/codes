# -*- coding: utf-8 -*-
"""
logging模块
"""

import sys

reload(sys)
sys.setdefaultencoding("utf-8")
import os

import logging
from logging.handlers import TimedRotatingFileHandler


def singleton(cls, *args, **kw):
    '''
    单例模式
    :param cls:
    :param args:
    :param kw:
    :return:
    '''
    instances = {}

    def _singleton(*args, **kw):
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]

    return _singleton


FMT = '%(asctime)s (%(process)d) [%(filename)s-%(module)s-%(funcName)s %(lineno)d] %(levelname)s: %(message)s'


# 输出格式  时间 （进程号） [文件名-模块名-函数名-行号] 日志等级:日志

def Log(name=None):
    L = Logging(name)
    return L.getLogger()


@singleton
class Logging(object):
    '''
    日志实例
    '''

    def __init__(self, name=None):
        assert name != None, 'name == None'
        self.name = name.lower()
        self.logger = logging.getLogger(self.name)
        # 初始化logger
        self.logger.setLevel(logging.DEBUG)
        # 设置logger等级
        self.getLogger()
        self.logger.propagate = False

    def getLogger(self):
        if self.logger.handlers:
            return self.logger
        sl = self.streamLogger()
        self.logger.addHandler(sl)
        fl = self.fileLogger()
        self.logger.addHandler(fl)

        return self.logger

    def fileLogger(self):
        """
        日志输出到文件
        :return:
        """
        if not os.path.exists('log'):
            os.makedirs('log')
        filename = os.path.join('log', self.name)
        filehandler = TimedRotatingFileHandler(filename, 'D', 1, 2)
        filehandler.suffix = '%Y-%m-%d.log'
        filehandler.setLevel(logging.DEBUG)
        fmtr = logging.Formatter(fmt=FMT)
        filehandler.setFormatter(fmtr)
        return filehandler

    def streamLogger(self):
        """
        日志输出到屏幕
        :return:
        """

        sl = logging.StreamHandler()
        sl.setLevel(logging.DEBUG)
        fmtr = logging.Formatter(fmt=FMT)
        sl.setFormatter(fmtr)
        return sl


if __name__ == '__main__':
    pass
