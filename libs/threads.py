# -*- coding: utf-8 -*-

__author__ = 'zhouhaichao@2008.sina.com'
import threading

import wx

def errorMessageHandler(e):
    wx.MessageBox(e.message)

class wxAsynchronousThread(threading.Thread):
    def __init__(self, handler, error_handler=errorMessageHandler):
        threading.Thread.__init__(self)
        self.__handler = handler
        self.__error_handler = error_handler

    def run(self):
        try:
            if isinstance(self.__handler,tuple) :
                wx.CallAfter(self.__handler[0],self.__handler[1])
            else :
                wx.CallAfter(self.__handler)
        except Exception, e:
            wx.CallAfter(self.__error_handler, e)

class AsynchronousThread(threading.Thread):
    def __init__(self, handler, error_handler=errorMessageHandler):
        threading.Thread.__init__(self)
        self.__handler = handler
        self.__error_handler = error_handler

    def run(self):
        try:
            if isinstance(self.__handler,tuple) :
                self.__handler[0](self.__handler[1])
            else :
                self.__handler()
        except Exception, e:
            self.__error_handler(e)